"""Inventário da coleta já feita pelo notebook 01.

A série usada no modelo não é um único ponto de Sorriso em 2015-2024.
O notebook 01 grava, em data/raw/, o clima NASA POWER e a PAM/IBGE dos
municípios do Alto Teles Pires. Este script só confere esse cache.
Não baixa de novo e não substitui a base processada.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED = BASE_DIR / "data" / "processed" / "dados_modelo_s4.csv"


def inventariar_cache() -> dict[str, int]:
    nasa = list((RAW_DIR / "nasa").glob("nasa_*.json")) if (RAW_DIR / "nasa").exists() else []
    ibge = list((RAW_DIR / "ibge").glob("*.json")) if (RAW_DIR / "ibge").exists() else []
    municipios = set()
    for caminho in nasa:
        partes = caminho.stem.split("_")
        if len(partes) >= 2 and partes[1].isdigit():
            municipios.add(partes[1])
    resumo = {
        "arquivos_nasa": len(nasa),
        "municipios_nasa": len(municipios),
        "arquivos_ibge": len(ibge),
        "base_processada": int(PROCESSED.exists()),
    }
    logging.info("Cache regional: %s", resumo)
    return resumo


if __name__ == "__main__":
    resumo = inventariar_cache()
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    if not PROCESSED.exists():
        raise SystemExit("Falta data/processed/dados_modelo_s4.csv. Rode os notebooks 01 a 08.")
    print(f"Base do modelo presente: {PROCESSED.name}")
