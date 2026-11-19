"""Persistência do alerta descrito no Model Card.

O banco guarda a série município x safra e a inferência do pipeline campeão
(regressão logística L2 em tmax_enchimento, limiar de probabilidade 0,45).
Recriar as tabelas a cada execução evita misturar o esquema antigo.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.etl_processamento import DATA_PATH, FEATURE, TARGET, carregar_base

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "monitoramento_safra.db"
MODEL_PATH = BASE_DIR / "models" / "pipeline_final.joblib"
LIMIAR_PATH = BASE_DIR / "models" / "limiar_congelado.json"
MODELO_NOME = "LogisticRegression L2 (C=1.0, class_weight=balanced)"


def limiar_congelado() -> tuple[float, float]:
    cfg = json.loads(LIMIAR_PATH.read_text(encoding="utf-8"))
    return float(cfg["limiar_otimo"]), float(cfg["limiar_celsius"])


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def inicializar_e_popular_banco() -> dict[str, int]:
    """Recria as três tabelas e grava a inferência do modelo campeão."""
    if not DATA_PATH.exists() or not MODEL_PATH.exists():
        raise FileNotFoundError("Base processada ou pipeline_final.joblib ausente.")

    df = carregar_base()
    pipe = joblib.load(MODEL_PATH)
    limiar, limiar_c = limiar_congelado()

    with get_connection() as conn:
        conn.executescript(
            """
            DROP TABLE IF EXISTS logs_monitoramento;
            DROP TABLE IF EXISTS previsoes_sistemicas;
            DROP TABLE IF EXISTS dados_historicos;
            CREATE TABLE dados_historicos (
                id_historico INTEGER PRIMARY KEY AUTOINCREMENT,
                municipio TEXT NOT NULL,
                codigo_ibge TEXT NOT NULL,
                ano_safra INTEGER NOT NULL,
                quebra_safra INTEGER NOT NULL,
                tmax_enchimento REAL NOT NULL,
                split TEXT NOT NULL,
                UNIQUE (codigo_ibge, ano_safra)
            );
            CREATE TABLE previsoes_sistemicas (
                id_previsao INTEGER PRIMARY KEY AUTOINCREMENT,
                id_historico INTEGER,
                ano_safra INTEGER NOT NULL,
                municipio TEXT NOT NULL,
                modelo_utilizado TEXT NOT NULL,
                alerta_quebra INTEGER NOT NULL,
                probabilidade_quebra REAL NOT NULL,
                limiar_decisao REAL NOT NULL,
                limiar_celsius REAL NOT NULL,
                tempo_inferencia_ms REAL NOT NULL,
                origem_execucao TEXT NOT NULL,
                data_previsao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_historico) REFERENCES dados_historicos (id_historico)
            );
            CREATE TABLE logs_monitoramento (
                id_log INTEGER PRIMARY KEY AUTOINCREMENT,
                id_previsao INTEGER,
                nivel_log TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                payload_entrada TEXT,
                data_log TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_previsao) REFERENCES previsoes_sistemicas (id_previsao)
            );
            """
        )

        X = df[[FEATURE]]
        t0 = time.perf_counter()
        probas = pipe.predict_proba(X)[:, 1]
        tempo_lote_ms = (time.perf_counter() - t0) * 1000
        tempo_linha = round(tempo_lote_ms / max(len(df), 1), 3)

        for (_, row), prob in zip(df.iterrows(), probas, strict=True):
            alerta = int(float(prob) >= limiar)
            cur_hist = conn.execute(
                """INSERT INTO dados_historicos
                (municipio, codigo_ibge, ano_safra, quebra_safra, tmax_enchimento, split)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    row["municipio"],
                    str(int(row["cod_municipio"])),
                    int(row["safra"]),
                    int(row[TARGET]),
                    float(row[FEATURE]),
                    row["split"],
                ),
            )
            cur_prev = conn.execute(
                """INSERT INTO previsoes_sistemicas
                (id_historico, ano_safra, municipio, modelo_utilizado, alerta_quebra,
                 probabilidade_quebra, limiar_decisao, limiar_celsius, tempo_inferencia_ms, origem_execucao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cur_hist.lastrowid,
                    int(row["safra"]),
                    row["municipio"],
                    MODELO_NOME,
                    alerta,
                    float(prob),
                    limiar,
                    limiar_c,
                    tempo_linha,
                    "teste" if row["split"] == "teste" else "treino",
                ),
            )
            conn.execute(
                """INSERT INTO logs_monitoramento
                (id_previsao, nivel_log, mensagem, payload_entrada)
                VALUES (?, ?, ?, ?)""",
                (
                    cur_prev.lastrowid,
                    "INFO",
                    f"Inferência {row['municipio']} {int(row['safra'])}: alerta={alerta}",
                    json.dumps({FEATURE: float(row[FEATURE])}, ensure_ascii=False),
                ),
            )

        contagens = {}
        for tabela in ("dados_historicos", "previsoes_sistemicas", "logs_monitoramento"):
            contagens[tabela] = conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        return contagens


if __name__ == "__main__":
    totais = inicializar_e_popular_banco()
    limiar, limiar_c = limiar_congelado()
    with get_connection() as conn:
        sorriso = pd.read_sql_query(
            """
            SELECT h.ano_safra, h.quebra_safra, h.tmax_enchimento, h.split,
                   p.probabilidade_quebra, p.alerta_quebra
            FROM dados_historicos h
            JOIN previsoes_sistemicas p ON p.id_historico = h.id_historico
            WHERE h.municipio = 'Sorriso'
            ORDER BY h.ano_safra
            """,
            conn,
        )
    print("Banco atualizado:", totais)
    print(f"Limiar: probabilidade {limiar:.2f} = {limiar_c:.2f} °C")
    print(sorriso.to_string(index=False))
