"""Compara classificadores com cinco sinais agroclimaticos por validacao temporal.

A selecao e feita apenas em previsoes walk-forward do split de treino, usando
limiar fixo de 0.5 e custo 5*FN + FP. O teste congelado e apenas diagnostico:
ja foi consultado em experimentos anteriores e nao deve eleger um vencedor.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression

import experimento_multivariavel as features


ROOT = Path(__file__).resolve().parent.parent
BASE_PATH = ROOT / "data" / "processed" / "dados_modelo_s4.csv"
ACTIVE_MODEL_PATH = ROOT / "models" / "pipeline_final.joblib"
THRESHOLD_PATH = ROOT / "models" / "limiar_congelado.json"
SUMMARY_PATH = ROOT / "models" / "s7_comparacao_modelos.csv"
YEAR_PATH = ROOT / "models" / "s7_metricas_por_safra.csv"
OOF_PATH = ROOT / "models" / "s7_previsoes_expansivas.csv"
TEST_PREDICTIONS_PATH = ROOT / "models" / "s7_previsoes_teste_diagnostico.csv"

TARGET = features.TARGET
FEATURES = features.FEATURES_MULTI_WITH_TMAX
MIN_TRAIN_SEASONS = features.MIN_TRAIN_SEASONS
THRESHOLD = 0.5
COST_FN = features.COST_FN
COST_FP = features.COST_FP


def make_candidates() -> dict[str, object]:
    """Keep preprocessing inside each pipeline so every fold fits it on past data."""
    scaled = lambda estimator: make_pipeline(StandardScaler(), estimator)
    return {
        "LogReg L2 balanceada": scaled(
            LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000)
        ),
        "GaussianNB": scaled(GaussianNB()),
        "SVC RBF balanceado": scaled(
            SVC(C=1.0, kernel="rbf", class_weight="balanced", probability=True, random_state=42)
        ),
        "LDA": scaled(LinearDiscriminantAnalysis()),
        "KNN (k=7)": scaled(KNeighborsClassifier(n_neighbors=7, weights="distance")),
        "Árvore (profundidade 1)": DecisionTreeClassifier(
            max_depth=1, min_samples_leaf=9, class_weight="balanced", random_state=42
        ),
        "Árvore (profundidade 2)": DecisionTreeClassifier(
            max_depth=2, min_samples_leaf=9, class_weight="balanced", random_state=42
        ),
        "Random Forest (rasa)": RandomForestClassifier(
            n_estimators=200,
            max_depth=2,
            min_samples_leaf=9,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=1,
        ),
        "Extra Trees (rasa)": ExtraTreesClassifier(
            n_estimators=200,
            max_depth=2,
            min_samples_leaf=9,
            class_weight="balanced",
            random_state=42,
            n_jobs=1,
        ),
    }


def positive_probability(model: object, X: pd.DataFrame) -> np.ndarray:
    classes = list(model.classes_)
    if 1 not in classes:
        raise ValueError(f"Modelo não contém classe positiva 1: {classes}")
    return model.predict_proba(X)[:, classes.index(1)]


def metricas(y: np.ndarray, probability: np.ndarray, threshold: float = THRESHOLD) -> dict[str, float | int]:
    y = np.asarray(y, dtype=int)
    pred = (np.asarray(probability) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    auc = roc_auc_score(y, probability) if np.unique(y).size == 2 else float("nan")
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
        "custo_5FN_1FP": int(COST_FN * fn + COST_FP * fp),
        "limiar": float(threshold),
    }


def expanding_predictions(train: pd.DataFrame, model: object, model_name: str) -> pd.DataFrame:
    records = []
    seasons = sorted(train["safra"].unique())
    for season in seasons:
        past_seasons = [year for year in seasons if year < season]
        if len(past_seasons) < MIN_TRAIN_SEASONS:
            continue
        fit = train.loc[train["safra"].isin(past_seasons)]
        valid = train.loc[train["safra"].eq(season)]
        if fit[TARGET].nunique() < 2:
            continue
        fitted = clone(model).fit(fit[FEATURES], fit[TARGET])
        probability = positive_probability(fitted, valid[FEATURES])
        records.append(
            valid[["cod_municipio", "municipio", "safra", TARGET]].assign(
                modelo=model_name, probabilidade=probability, threshold=THRESHOLD
            )
        )
    if not records:
        raise ValueError(f"Nenhuma previsão walk-forward gerada para {model_name}.")
    return pd.concat(records, ignore_index=True)


def run() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not BASE_PATH.is_file():
        raise FileNotFoundError(f"Base ausente: {BASE_PATH}")
    for path in (ACTIVE_MODEL_PATH, THRESHOLD_PATH):
        if not path.is_file():
            raise FileNotFoundError(f"Artefato ausente: {path}")

    base = pd.read_csv(BASE_PATH)
    required = {"cod_municipio", "municipio", "safra", "split", TARGET, "tmax_enchimento"}
    missing = required - set(base.columns)
    if missing:
        raise ValueError(f"Colunas ausentes na base: {sorted(missing)}")

    climate = features.load_daily_features()
    data = base.merge(climate, on=["cod_municipio", "safra"], how="left", validate="one_to_one")
    if data[FEATURES].isna().any(axis=None):
        keys = data.loc[data[FEATURES].isna().any(axis=1), ["cod_municipio", "safra"]]
        raise ValueError(f"Há features ausentes nas chaves: {keys.head(10).to_dict('records')}")
    delta = (data["tmax_enchimento"] - data["tmax_recalculada"]).abs()
    if delta.max() > 0.05:
        raise ValueError(f"tmax_enchimento não confere com a série diária (delta máximo {delta.max():.4f} °C).")

    train = data.loc[data["split"].eq("treino")].copy()
    test = data.loc[data["split"].eq("teste")].copy()
    if train.empty or test.empty or train["safra"].max() >= test["safra"].min():
        raise ValueError("A base não respeita o split temporal treino antes do teste.")

    candidate_models = make_candidates()
    oof_frames = []
    summary_rows = []
    annual_rows = []
    for name, model in candidate_models.items():
        oof = expanding_predictions(train, model, name)
        oof_frames.append(oof)
        validation_metrics = metricas(oof[TARGET].to_numpy(), oof["probabilidade"].to_numpy())
        fitted = clone(model).fit(train[FEATURES], train[TARGET])
        test_probability = positive_probability(fitted, test[FEATURES])
        test_metrics = metricas(test[TARGET].to_numpy(), test_probability)
        without_2024 = test["safra"].ne(2024).to_numpy()
        test_no_2024_metrics = metricas(
            test.loc[without_2024, TARGET].to_numpy(), test_probability[without_2024]
        )
        summary_rows.append(
            {
                "modelo": name,
                "features": " | ".join(FEATURES),
                "selecao_validacao": "ordenacao por custo OOF com threshold fixo 0.5; empate por AUC e recall",
                **{f"validacao_{key}": value for key, value in validation_metrics.items()},
                **{f"teste_diagnostico_{key}": value for key, value in test_metrics.items()},
                **{f"teste_sem_2024_diagnostico_{key}": value for key, value in test_no_2024_metrics.items()},
            }
        )
        test_output = test[["cod_municipio", "municipio", "safra", TARGET]].copy()
        test_output["modelo"] = name
        test_output["probabilidade"] = test_probability
        test_output["alerta"] = (test_probability >= THRESHOLD).astype(int)
        for season, group in test_output.groupby("safra", sort=True):
            year_metrics = metricas(group[TARGET].to_numpy(), group["probabilidade"].to_numpy())
            annual_rows.append({"modelo": name, "safra": int(season), **year_metrics})
        if name == next(iter(candidate_models)):
            test_predictions = test_output
        else:
            test_predictions = pd.concat([test_predictions, test_output], ignore_index=True)

    oof_predictions = pd.concat(oof_frames, ignore_index=True)
    current_threshold_config = json.loads(THRESHOLD_PATH.read_text(encoding="utf-8"))
    active_threshold = float(current_threshold_config["limiar_otimo"])
    active_model = joblib.load(ACTIVE_MODEL_PATH)
    active_oof = expanding_predictions(
        train,
        active_model,
        "Modelo ativo (Tmax; threshold oficial 0.45)",
    )
    active_oof["threshold"] = active_threshold
    active_metrics = metricas(
        active_oof[TARGET].to_numpy(), active_oof["probabilidade"].to_numpy(), active_threshold
    )
    active_probability = positive_probability(active_model, test[["tmax_enchimento"]])
    active_test_metrics = metricas(
        test[TARGET].to_numpy(), active_probability, active_threshold
    )
    no_2024 = test["safra"].ne(2024).to_numpy()
    active_test_no_2024_metrics = metricas(
        test.loc[no_2024, TARGET].to_numpy(), active_probability[no_2024], active_threshold
    )
    summary_rows.append(
        {
            "modelo": "Modelo ativo (Tmax; threshold oficial 0.45)",
            "features": "tmax_enchimento",
            "selecao_validacao": "referência ativa; threshold congelado oficial",
            **{f"validacao_{key}": value for key, value in active_metrics.items()},
            **{f"teste_diagnostico_{key}": value for key, value in active_test_metrics.items()},
            **{f"teste_sem_2024_diagnostico_{key}": value for key, value in active_test_no_2024_metrics.items()},
        }
    )
    active_test = test[["cod_municipio", "municipio", "safra", TARGET]].copy()
    active_test["modelo"] = "Modelo ativo (Tmax; threshold oficial 0.45)"
    active_test["probabilidade"] = active_probability
    active_test["alerta"] = (active_probability >= active_threshold).astype(int)
    for season, group in active_test.groupby("safra", sort=True):
        annual_rows.append(
            {
                "modelo": "Modelo ativo (Tmax; threshold oficial 0.45)",
                "safra": int(season),
                **metricas(group[TARGET].to_numpy(), group["probabilidade"].to_numpy(), active_threshold),
            }
        )
    test_predictions = pd.concat([test_predictions, active_test], ignore_index=True)

    summary = pd.DataFrame(summary_rows)
    candidate_validation = summary.loc[summary["modelo"].isin(candidate_models)].copy()
    candidate_validation = candidate_validation.sort_values(
        ["validacao_custo_5FN_1FP", "validacao_AUC", "validacao_recall"],
        ascending=[True, False, False],
        na_position="last",
    )
    winner = candidate_validation.iloc[0]["modelo"]
    summary["ranking_validacao"] = np.nan
    for rank, name in enumerate(candidate_validation["modelo"], start=1):
        summary.loc[summary["modelo"].eq(name), "ranking_validacao"] = rank
    summary["melhor_por_criterio_validacao"] = summary["modelo"].eq(winner)
    annual = pd.DataFrame(annual_rows)

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUMMARY_PATH, index=False)
    annual.to_csv(YEAR_PATH, index=False)
    oof_predictions.to_csv(OOF_PATH, index=False)
    test_predictions.to_csv(TEST_PREDICTIONS_PATH, index=False)
    return summary, annual, oof_predictions, test_predictions


if __name__ == "__main__":
    results, by_year, _, _ = run()
    columns = [
        "ranking_validacao",
        "modelo",
        "validacao_custo_5FN_1FP",
        "validacao_AUC",
        "validacao_recall",
        "validacao_precisao",
        "teste_diagnostico_custo_5FN_1FP",
        "teste_diagnostico_AUC",
        "teste_sem_2024_diagnostico_custo_5FN_1FP",
    ]
    ranked = results.loc[results["ranking_validacao"].notna(), columns].sort_values("ranking_validacao")
    print(ranked.to_string(index=False))
    best = ranked.iloc[0]
    print(
        f"\nMelhor candidato no critério pré-definido: {best['modelo']} "
        f"(custo OOF {best['validacao_custo_5FN_1FP']:.0f}, AUC {best['validacao_AUC']:.3f})."
    )
    print("O teste e o teste sem 2024 são apenas diagnósticos; seleção baseada somente no OOF do treino.")
    print(f"Resultados: {SUMMARY_PATH}")
