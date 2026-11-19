"""Valida a base usada pelo modelo do Model Card.

A matriz oficial é data/processed/dados_modelo_s4.csv, produzida pelo notebook 08.
Unidade: município x safra, na microrregião do Alto Teles Pires.
Alvo: quebra_safra = 1 quando o rendimento fica mais de 8% abaixo da tendência
linear das safras anteriores do próprio município.
Feature do modelo campeão: tmax_enchimento (média da temperatura máxima diária, dez-fev).
Split: treino 2001-2018 e teste 2019-2024.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "dados_modelo_s4.csv"
FEATURE = "tmax_enchimento"
TARGET = "quebra_safra"
MUNICIPIOS_ESPERADOS = 9
N_TREINO = 138
N_TESTE = 54


def carregar_base() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Base do modelo não encontrada em {DATA_PATH}. Execute o notebook 08.")
    df = pd.read_csv(DATA_PATH)
    obrigatorias = {"cod_municipio", "safra", "municipio", FEATURE, TARGET, "split"}
    faltando = obrigatorias - set(df.columns)
    if faltando:
        raise ValueError(f"Colunas ausentes em {DATA_PATH.name}: {sorted(faltando)}")
    return df


def executar_etl_idempotente() -> pd.DataFrame:
    """Confere a base já gerada pelos notebooks, sem recriar o alvo nem o split."""
    df = carregar_base()
    treino = df[df["split"] == "treino"]
    teste = df[df["split"] == "teste"]
    if df["municipio"].nunique() != MUNICIPIOS_ESPERADOS:
        raise ValueError(f"Esperados {MUNICIPIOS_ESPERADOS} municípios, encontrados {df['municipio'].nunique()}.")
    if len(treino) != N_TREINO or len(teste) != N_TESTE:
        raise ValueError(f"Split inesperado: treino={len(treino)} teste={len(teste)}.")
    if int(treino["safra"].min()) != 2001 or int(teste["safra"].max()) != 2024:
        raise ValueError("Janela de safras diferente de 2001-2024.")
    if df[FEATURE].isna().any():
        raise ValueError(f"{FEATURE} tem valores ausentes.")
    logging.info(
        "Base validada: %d linhas, %d municípios, treino %d (%d quebras), teste %d (%d quebras).",
        len(df),
        df["municipio"].nunique(),
        len(treino),
        int(treino[TARGET].sum()),
        len(teste),
        int(teste[TARGET].sum()),
    )
    return df


if __name__ == "__main__":
    base = executar_etl_idempotente()
    sorriso = base[base["municipio"] == "Sorriso"]
    print(
        f"Linhas: {len(base)} | municípios: {base['municipio'].nunique()} | "
        f"quebras treino/teste: {int(base.loc[base['split']=='treino', TARGET].sum())}/"
        f"{int(base.loc[base['split']=='teste', TARGET].sum())}"
    )
    print("Sorriso (safra, split, tmax_enchimento, quebra):")
    print(
        sorriso[["safra", "split", FEATURE, TARGET]]
        .sort_values("safra")
        .to_string(index=False)
    )
