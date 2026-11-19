"""Compara o modelo atual com candidatos de sinais agroclimaticos do periodo critico.

A validacao e expansiva por safra: cada previsao de validacao usa apenas anos
anteriores. O teste 2019-2024 e usado somente depois de congelar os limiares.
Inclui LogReg com os quatro sinais diarios e com os quatro mais tmax_enchimento.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parent.parent
RAW_NASA = ROOT / "data" / "raw" / "nasa"
BASE_PATH = ROOT / "data" / "processed" / "dados_modelo_s4.csv"
MODEL_PATH = ROOT / "models" / "pipeline_final.joblib"
THRESHOLD_PATH = ROOT / "models" / "limiar_congelado.json"
OUTPUT_PATH = ROOT / "models" / "s6_comparacao_multivariavel.csv"
YEAR_OUTPUT_PATH = ROOT / "models" / "s6_metricas_por_safra.csv"

TARGET = "quebra_safra"
FEATURES_MULTI = [
    "deficit_hidrico_solo",
    "dias_pico_calor",
    "precipitacao_enchimento",
    "veranico_max_dias",
]
FEATURES_CURRENT = ["tmax_enchimento"]
FEATURES_MULTI_WITH_TMAX = [*FEATURES_CURRENT, *FEATURES_MULTI]
MODEL_NAMES = [
    "LogReg atual (tmax)",
    "LogReg multivariavel (4 sinais)",
    "GaussianNB multivariavel (4 sinais)",
    "Arvore profundidade 1 (4 sinais)",
    "Arvore profundidade 2 (4 sinais)",
    "LogReg multivariavel (5 sinais incluindo tmax)",
]
MIN_TRAIN_SEASONS = 8
COST_FN = 5
COST_FP = 1


def load_daily_features() -> pd.DataFrame:
    """Deriva sinais diarios de dez-fev a partir dos JSONs NASA locais."""
    files = sorted(RAW_NASA.glob("nasa_*.json"))
    if not files:
        raise FileNotFoundError(f"Nenhum JSON NASA encontrado em {RAW_NASA}")

    daily_frames = []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        parameters = payload.get("properties", {}).get("parameter", {})
        required = {"PRECTOTCORR", "T2M_MAX", "GWETROOT"}
        missing = required - set(parameters)
        if missing:
            raise ValueError(f"{path.name} sem parametros requeridos: {sorted(missing)}")
        daily = pd.DataFrame(parameters)
        daily.index = pd.to_datetime(daily.index, format="%Y%m%d")
        daily.index.name = "data"
        daily = daily.reset_index()
        parts = path.stem.split("_")
        daily["cod_municipio"] = int(parts[1])
        daily_frames.append(daily)

    daily = pd.concat(daily_frames, ignore_index=True)
    daily = daily.drop_duplicates(["cod_municipio", "data"]).sort_values(["cod_municipio", "data"])
    daily = daily[daily["data"].dt.month.isin([12, 1, 2])].copy()
    daily["safra"] = daily["data"].dt.year + daily["data"].dt.month.eq(12).astype(int)

    rows = []
    for (code, season), group in daily.groupby(["cod_municipio", "safra"], sort=True):
        valid = group[list(["PRECTOTCORR", "T2M_MAX", "GWETROOT"])].notna().all(axis=1)
        valid &= group[list(["PRECTOTCORR", "T2M_MAX", "GWETROOT"])].ne(-999.0).all(axis=1)
        expected = (
            pd.Period(year=int(season) - 1, month=12, freq="M").days_in_month
            + pd.Period(year=int(season), month=1, freq="M").days_in_month
            + pd.Period(year=int(season), month=2, freq="M").days_in_month
        )
        if valid.sum() / expected < 0.95:
            continue

        measured = group.loc[valid].copy()
        dry = measured["PRECTOTCORR"].lt(1.0).to_numpy()
        longest_dry_spell = current = 0
        for is_dry in dry:
            current = current + 1 if is_dry else 0
            longest_dry_spell = max(longest_dry_spell, current)

        rows.append(
            {
                "cod_municipio": int(code),
                "safra": int(season),
                "deficit_hidrico_solo": int(measured["GWETROOT"].lt(0.70).sum()),
                "dias_pico_calor": int(measured["T2M_MAX"].ge(35.0).sum()),
                "precipitacao_enchimento": float(measured["PRECTOTCORR"].sum()),
                "veranico_max_dias": int(longest_dry_spell),
                "tmax_recalculada": float(measured["T2M_MAX"].mean()),
            }
        )

    features = pd.DataFrame(rows)
    if features.empty:
        raise ValueError("Nenhum conjunto municipal-safra passou o limite de cobertura climatica.")
    if features.duplicated(["cod_municipio", "safra"]).any():
        raise ValueError("Features climaticas duplicadas para a mesma chave municipio-safra.")
    return features


def make_models() -> dict[str, tuple[list[str], Callable[[], object]]]:
    return {
        MODEL_NAMES[0]: (
            FEATURES_CURRENT,
            lambda: make_pipeline(
                StandardScaler(),
                LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000),
            ),
        ),
        MODEL_NAMES[1]: (
            FEATURES_MULTI,
            lambda: make_pipeline(
                StandardScaler(),
                LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000),
            ),
        ),
        MODEL_NAMES[2]: (
            FEATURES_MULTI,
            lambda: make_pipeline(StandardScaler(), GaussianNB()),
        ),
        MODEL_NAMES[3]: (
            FEATURES_MULTI,
            lambda: DecisionTreeClassifier(
                max_depth=1, min_samples_leaf=9, class_weight="balanced", random_state=42
            ),
        ),
        MODEL_NAMES[4]: (
            FEATURES_MULTI,
            lambda: DecisionTreeClassifier(
                max_depth=2, min_samples_leaf=9, class_weight="balanced", random_state=42
            ),
        ),
        MODEL_NAMES[5]: (
            FEATURES_MULTI_WITH_TMAX,
            lambda: make_pipeline(
                StandardScaler(),
                LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000),
            ),
        ),
    }


def expanding_validation(
    train: pd.DataFrame, features: list[str], model_factory: Callable[[], object]
) -> pd.DataFrame:
    predictions = []
    seasons = sorted(train["safra"].unique())
    for season in seasons:
        prior = [year for year in seasons if year < season]
        if len(prior) < MIN_TRAIN_SEASONS:
            continue
        fit = train[train["safra"].isin(prior)]
        valid = train[train["safra"] == season]
        if fit[TARGET].nunique() < 2:
            continue
        model = model_factory()
        model.fit(fit[features], fit[TARGET])
        positive_index = list(model.classes_).index(1)
        probabilities = model.predict_proba(valid[features])[:, positive_index]
        predictions.append(
            pd.DataFrame(
                {
                    "cod_municipio": valid["cod_municipio"].to_numpy(),
                    "safra": valid["safra"].to_numpy(),
                    "y": valid[TARGET].astype(int).to_numpy(),
                    "probabilidade": probabilities,
                }
            )
        )
    if not predictions:
        raise ValueError("Validacao expansiva nao produziu previsoes.")
    return pd.concat(predictions, ignore_index=True)


def choose_threshold(validation: pd.DataFrame) -> tuple[float, float]:
    y = validation["y"].to_numpy()
    probabilities = validation["probabilidade"].to_numpy()
    candidates = np.unique(np.r_[0.0, probabilities, 1.0])
    scored = []
    for threshold in candidates:
        pred = probabilities >= threshold
        tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
        cost = COST_FN * int(fn) + COST_FP * int(fp)
        scored.append((cost, -float(threshold), float(threshold)))
    cost, _, threshold = min(scored)
    return threshold, float(cost)


def summarize(y: np.ndarray, pred: np.ndarray, prob: np.ndarray, threshold: float) -> dict[str, float | int]:
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    auc = roc_auc_score(y, prob) if np.unique(y).size == 2 else float("nan")
    return {
        "N": int(len(y)),
        "TN": int(tn),
        "FP": int(fp),
        "FN": int(fn),
        "TP": int(tp),
        "acuracia": float(accuracy_score(y, pred)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "precisao": float(precision_score(y, pred, zero_division=0)),
        "F1": float(f1_score(y, pred, zero_division=0)),
        "AUC": float(auc),
        "alertas_pct": float(np.mean(pred)),
        "quebras_pct": float(np.mean(y)),
        "custo_5FN_1FP": int(COST_FN * fn + fp),
        "limiar_probabilidade": float(threshold),
    }


def run() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not BASE_PATH.exists():
        raise FileNotFoundError(f"Base final nao encontrada: {BASE_PATH}")
    base = pd.read_csv(BASE_PATH)
    required = {"cod_municipio", "safra", "municipio", "split", TARGET, *FEATURES_CURRENT}
    missing = required - set(base.columns)
    if missing:
        raise ValueError(f"Colunas ausentes em {BASE_PATH.name}: {sorted(missing)}")

    climate = load_daily_features()
    data = base.merge(climate, on=["cod_municipio", "safra"], how="left", validate="one_to_one")
    missing_weather = data[FEATURES_MULTI].isna().any(axis=1)
    if missing_weather.any():
        keys = data.loc[missing_weather, ["cod_municipio", "safra"]].to_dict("records")
        raise ValueError(f"Features climaticas ausentes para chaves: {keys[:10]}")

    # Confirma que a feature que define o modelo implantado bate com a fonte diaria.
    delta = (data["tmax_enchimento"] - data["tmax_recalculada"]).abs()
    if delta.max() > 0.05:
        raise ValueError(f"tmax_enchimento diverge dos JSONs diarios (max delta={delta.max():.4f} C).")
    if data[FEATURES_MULTI_WITH_TMAX].isna().any(axis=None):
        raise ValueError("Features do candidato multivariavel contem valores ausentes.")

    train = data[data["split"] == "treino"].copy()
    test = data[data["split"] == "teste"].copy()
    if train["safra"].max() >= test["safra"].min():
        raise ValueError("Split temporal invalido: treino nao precede integralmente o teste.")

    results = []
    annual_results = []
    model_specs = make_models()
    with THRESHOLD_PATH.open(encoding="utf-8") as file:
        official_config = json.load(file)
    official_threshold = float(official_config["limiar_otimo"])
    deployed = joblib.load(MODEL_PATH)

    for name, (features, factory) in model_specs.items():
        oof = expanding_validation(train, features, factory)
        learned_threshold, validation_cost = choose_threshold(oof)
        model = factory()
        model.fit(train[features], train[TARGET])
        positive_index = list(model.classes_).index(1)
        test_probability = model.predict_proba(test[features])[:, positive_index]
        threshold = official_threshold if name == MODEL_NAMES[0] else learned_threshold
        test_prediction = (test_probability >= threshold).astype(int)
        validation_prediction = (oof["probabilidade"].to_numpy() >= learned_threshold).astype(int)
        validation_metrics = summarize(
            oof["y"].to_numpy(), validation_prediction, oof["probabilidade"].to_numpy(), learned_threshold
        )
        test_metrics = summarize(test[TARGET].to_numpy(), test_prediction, test_probability, threshold)
        without_2024 = test["safra"].to_numpy() != 2024
        test_without_2024_metrics = summarize(
            test.loc[without_2024, TARGET].to_numpy(),
            test_prediction[without_2024],
            test_probability[without_2024],
            threshold,
        )
        results.append(
            {
                "modelo": name,
                "features": " | ".join(features),
                "limiar_frozen": threshold,
                "custo_validacao_expansiva": validation_cost,
                **{f"validacao_{key}": value for key, value in validation_metrics.items()},
                **{f"teste_{key}": value for key, value in test_metrics.items()},
                **{f"teste_sem_2024_{key}": value for key, value in test_without_2024_metrics.items()},
            }
        )

        if name == MODEL_NAMES[0]:
            deployed_probability = deployed.predict_proba(test[FEATURES_CURRENT])[:, list(deployed.classes_).index(1)]
            deployed_prediction = (deployed_probability >= official_threshold).astype(int)
            deployed_metrics = summarize(
                test[TARGET].to_numpy(), deployed_prediction, deployed_probability, official_threshold
            )
            results.append(
                {
                    "modelo": "Modelo implantado (artefato joblib)",
                    "features": " | ".join(FEATURES_CURRENT),
                    "limiar_frozen": official_threshold,
                    "custo_validacao_expansiva": validation_cost,
                    **{f"validacao_{key}": value for key, value in validation_metrics.items()},
                    **{f"teste_{key}": value for key, value in deployed_metrics.items()},
                    **{f"teste_sem_2024_{key}": value for key, value in summarize(
                        test.loc[without_2024, TARGET].to_numpy(),
                        deployed_prediction[without_2024],
                        deployed_probability[without_2024],
                        official_threshold,
                    ).items()},
                }
            )

        for season, group in test.assign(pred=test_prediction, prob=test_probability).groupby("safra"):
            metrics = summarize(
                group[TARGET].to_numpy(),
                group["pred"].to_numpy(),
                group["prob"].to_numpy(),
                threshold,
            )
            annual_results.append({"modelo": name, "safra": int(season), **metrics})

    for name, prediction in (
        ("Baseline: nunca alertar", np.zeros(len(test), dtype=int)),
        ("Baseline: alertar sempre", np.ones(len(test), dtype=int)),
    ):
        probability = prediction.astype(float)
        metrics = summarize(test[TARGET].to_numpy(), prediction, probability, float("nan"))
        mask = test["safra"].to_numpy() != 2024
        no_2024_metrics = summarize(
            test.loc[mask, TARGET].to_numpy(),
            prediction[mask],
            probability[mask],
            float("nan"),
        )
        results.append(
            {
                "modelo": name,
                "features": "nenhuma",
                "limiar_frozen": float("nan"),
                "custo_validacao_expansiva": float("nan"),
                **{f"teste_{key}": value for key, value in metrics.items()},
                **{f"teste_sem_2024_{key}": value for key, value in no_2024_metrics.items()},
            }
        )

    results_df = pd.DataFrame(results)
    annual_df = pd.DataFrame(annual_results)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUTPUT_PATH, index=False)
    annual_df.to_csv(YEAR_OUTPUT_PATH, index=False)
    return results_df, annual_df


if __name__ == "__main__":
    comparison, by_year = run()
    print(comparison[["modelo", "limiar_frozen", "validacao_custo_5FN_1FP", "teste_acuracia",
                      "teste_recall", "teste_precisao", "teste_AUC", "teste_custo_5FN_1FP",
                      "teste_sem_2024_custo_5FN_1FP"]].to_string(index=False))
    print(f"\nResultados por safra: {YEAR_OUTPUT_PATH}")
    print(f"Comparacao salva em: {OUTPUT_PATH}")
