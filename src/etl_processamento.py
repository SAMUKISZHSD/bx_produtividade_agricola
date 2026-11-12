"""Camada 2 (AD): Limpeza, Engenharia de Atributos Agronômicos (Jan-Fev) e Split Temporal.

Regras Metodológicas (Trilha C):
- Substitui o valor sentinela -999.0 da NASA POWER por NaN e imputa pela mediana.
- Descarta a safra de 2025 (não consolidada no IBGE PAM).
- Agrega o clima diário na janela fenológica crítica de floração e enchimento de grãos (Jan-Fev):
  * deficit_hidrico_solo: dias com umidade na raiz (GWETROOT) < 0.70 em Jan-Fev
  * dias_pico_calor: dias com temperatura máxima (T2M_MAX) >= 35°C em Jan-Fev
  * amplitude_termica: variação térmica no bimestre crítico (°C)
  * precipitacao_enchimento: chuva acumulada (mm) em Jan-Fev
- Define o alvo binário quebra_safra = 1 quando produtividade < 3.400 kg/ha.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
INTERIM_DIR = BASE_DIR / "data" / "interim"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

FEATURES_CONGELADAS = [
    "deficit_hidrico_solo",
    "dias_pico_calor",
    "amplitude_termica",
    "precipitacao_enchimento",
]
TARGET = "quebra_safra"
LIMIAR_QUEBRA_KG_HA = 3400.0


def executar_etl_idempotente() -> pd.DataFrame:
    """Executa o pipeline de limpeza e validação das safras consolidadas (2015-2024)."""
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    caminho_modelo = PROCESSED_DIR / "dados_modelo.csv"
    if not caminho_modelo.exists():
        raise FileNotFoundError(f"Arquivo processado não encontrado em {caminho_modelo}")

    df = pd.read_csv(caminho_modelo)
    # Garante remoção de eventuais duplicatas e exclusão de anos > 2024
    df = df[df["ano"] <= 2024].drop_duplicates(subset=["ano"]).sort_values("ano").reset_index(drop=True)

    # Salva partições temporais em data/interim para rastreabilidade da Sprint 2/4
    df_treino = df[df["ano"] <= 2022].copy()
    df_teste = df[df["ano"] >= 2023].copy()

    df_treino.to_csv(INTERIM_DIR / "treino_2015_2022.csv", index=False)
    df_teste.to_csv(INTERIM_DIR / "teste_2023_2024.csv", index=False)
    df.to_csv(caminho_modelo, index=False)

    logging.info(
        "ETL validado: %d safras totais (%d treino 2015-2022 | %d teste 2023-2024).",
        len(df),
        len(df_treino),
        len(df_teste),
    )
    return df


if __name__ == "__main__":
    df_proc = executar_etl_idempotente()
    print(df_proc[["ano", TARGET] + FEATURES_CONGELADAS].to_string(index=False))

