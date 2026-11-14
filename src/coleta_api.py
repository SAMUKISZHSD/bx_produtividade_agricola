"""Camada 1 (CD): Coleta e Ingestão Idempotente de Dados Abertos.

Fontes Oficiais:
1. NASA POWER Daily API (variáveis meteorológicas e de solo diárias).
2. IBGE SIDRA API - Pesquisa Agrícola Municipal (PAM, Agregado 1612 - Soja em grão).

Garante tratamento de erros de rede, timeout, logging estruturado e idempotência
(executar múltiplas vezes mantém os arquivos brutos sem duplicação de linhas).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

MUNICIPIO = os.getenv("SOJARISCO_MUNICIPIO", "Sorriso")
UF = os.getenv("SOJARISCO_UF", "MT")
CODIGO_IBGE = os.getenv("SOJARISCO_CODIGO_IBGE", "5107925")
LATITUDE = float(os.getenv("SOJARISCO_LATITUDE", "-12.5414"))
LONGITUDE = float(os.getenv("SOJARISCO_LONGITUDE", "-55.7269"))


def coletar_nasa_power_diario(ano_inicio: int = 2015, ano_fim: int = 2024, forcar_download: bool = False) -> pd.DataFrame:
    """Coleta dados diários da NASA POWER para Sorriso-MT com garantia de idempotência."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    caminho_csv = RAW_DIR / "nasa_power_sorriso_daily.csv"

    if caminho_csv.exists() and not forcar_download:
        df_existente = pd.read_csv(caminho_csv)
        df_existente = df_existente.drop_duplicates(subset=["data"]).sort_values("data").reset_index(drop=True)
        df_existente.to_csv(caminho_csv, index=False)
        logging.info("Cache local NASA POWER validado de forma idempotente (%d dias).", len(df_existente))
        return df_existente

    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params: dict[str, Any] = {
        "parameters": "PRECTOTCORR,T2M,T2M_MAX,T2M_MIN,RH2M,ALLSKY_SFC_SW_DWN,GWETROOT",
        "community": "AG",
        "longitude": LONGITUDE,
        "latitude": LATITUDE,
        "start": f"{ano_inicio}0101",
        "end": f"{ano_fim}1231",
        "format": "JSON",
    }

    try:
        logging.info("Consultando API pública NASA POWER (%d-%d)...", ano_inicio, ano_fim)
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        param_dict = payload.get("properties", {}).get("parameter", {})
        df = pd.DataFrame(param_dict)
        df.index.name = "data"
        df = df.reset_index()
        df = df.drop_duplicates(subset=["data"]).sort_values("data").reset_index(drop=True)
        df.to_csv(caminho_csv, index=False)
        logging.info("Dados NASA POWER salvos em %s (%d registros).", caminho_csv, len(df))
        return df
    except requests.RequestException as exc:
        logging.error("Falha de rede/timeout na API NASA POWER: %s", exc)
        if caminho_csv.exists():
            logging.info("Utilizando fallback local existente em %s.", caminho_csv)
            return pd.read_csv(caminho_csv)
        raise


def coletar_ibge_pam_soja(codigo_ibge: str = CODIGO_IBGE, forcar_download: bool = False) -> pd.DataFrame:
    """Coleta a série histórica de produtividade anual da soja (kg/ha) no IBGE SIDRA PAM."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    caminho_csv = RAW_DIR / "ibge_pam_soja_sorriso.csv"

    if caminho_csv.exists() and not forcar_download:
        df_existente = pd.read_csv(caminho_csv)
        col_ano = "ano" if "ano" in df_existente.columns else df_existente.columns[0]
        df_existente = df_existente.drop_duplicates(subset=[col_ano]).sort_values(col_ano).reset_index(drop=True)
        df_existente.to_csv(caminho_csv, index=False)
        logging.info("Cache local IBGE PAM validado de forma idempotente (%d safras).", len(df_existente))
        return df_existente

    url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/1612/periodos/"
        f"2015|2016|2017|2018|2019|2020|2021|2022|2023|2024/variaveis/112"
        f"?localidades=N6[{codigo_ibge}]&classificacao=81[2713]"
    )
    try:
        logging.info("Consultando API pública IBGE SIDRA PAM (Município %s)...", codigo_ibge)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        dados = resp.json()
        serie = dados[0]["resultados"][0]["series"][0]["serie"]
        registros = [
            {"ano": int(ano), "codigo_ibge": codigo_ibge, "municipio": f"{MUNICIPIO} - {UF}", "produtividade_kg_ha": float(val)}
            for ano, val in serie.items()
            if str(val).replace(".", "", 1).isdigit()
        ]
        df = pd.DataFrame(registros).drop_duplicates(subset=["ano"]).sort_values("ano").reset_index(drop=True)
        df.to_csv(caminho_csv, index=False)
        logging.info("Dados IBGE PAM salvos em %s (%d safras).", caminho_csv, len(df))
        return df
    except requests.RequestException as exc:
        logging.error("Falha de rede/timeout na API IBGE SIDRA: %s", exc)
        if caminho_csv.exists():
            return pd.read_csv(caminho_csv)
        raise


if __name__ == "__main__":
    df_nasa = coletar_nasa_power_diario()
    df_ibge = coletar_ibge_pam_soja()
    print(f"Coleta concluída! NASA POWER: {len(df_nasa)} linhas | IBGE PAM: {len(df_ibge)} safras.")

