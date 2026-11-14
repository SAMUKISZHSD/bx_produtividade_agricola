"""Camada 4 (PROD): Persistência Relacional em SQLite (3 Tabelas Encadeadas).

Estrutura do Banco (`data/monitoramento_safra.db`):
1. `dados_historicos`: série consolidada por safra (chave única em `ano_safra`).
2. `previsoes_sistemicas`: inferências geradas pelos modelos (FK para `id_historico`).
3. `logs_monitoramento`: trilha de auditoria e latência (FK para `id_previsao`).
(Mantém também as tabelas `safras_historico` e `previsoes_modelos` dos notebooks da Sprint 5).
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "monitoramento_safra.db"
DATA_PATH = BASE_DIR / "data" / "processed" / "dados_modelo.csv"
MODEL_PATH = BASE_DIR / "models" / "pipeline_final.joblib"

FEATURES = [
    "deficit_hidrico_solo",
    "dias_pico_calor",
    "amplitude_termica",
    "precipitacao_enchimento",
]


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def inicializar_e_popular_banco() -> dict[str, int]:
    """Cria as tabelas relacionais e popula de maneira idempotente com o modelo campeão."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS dados_historicos (
                id_historico INTEGER PRIMARY KEY AUTOINCREMENT,
                municipio TEXT NOT NULL,
                codigo_ibge TEXT NOT NULL,
                ano_safra INTEGER NOT NULL UNIQUE,
                area_plantada_ha REAL,
                area_colhida_ha REAL,
                rendimento_kg_ha REAL,
                quebra_safra INTEGER NOT NULL,
                deficit_hidrico_solo INTEGER NOT NULL,
                dias_pico_calor INTEGER NOT NULL,
                precipitacao_enchimento REAL NOT NULL,
                amplitude_termica REAL NOT NULL,
                data_consolidacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS previsoes_sistemicas (
                id_previsao INTEGER PRIMARY KEY AUTOINCREMENT,
                id_historico INTEGER,
                ano_safra INTEGER NOT NULL,
                modelo_utilizado TEXT NOT NULL,
                alerta_quebra INTEGER NOT NULL,
                probabilidade_quebra REAL NOT NULL,
                limiar_decisao REAL NOT NULL,
                tempo_inferencia_ms REAL NOT NULL,
                origem_execucao TEXT NOT NULL,
                data_previsao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_historico) REFERENCES dados_historicos (id_historico)
            );
            CREATE TABLE IF NOT EXISTS logs_monitoramento (
                id_log INTEGER PRIMARY KEY AUTOINCREMENT,
                id_previsao INTEGER,
                nivel_log TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                payload_entrada TEXT,
                ip_origem TEXT,
                data_log TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_previsao) REFERENCES previsoes_sistemicas (id_previsao)
            );
            """
        )

        if DATA_PATH.exists() and MODEL_PATH.exists():
            df = pd.read_csv(DATA_PATH)
            pipe = joblib.load(MODEL_PATH)
            rendimentos = {
                2015: 3148.0, 2016: 2880.0, 2017: 3520.0, 2018: 3870.0, 2019: 3480.0,
                2020: 3490.0, 2021: 3360.0, 2022: 3610.0, 2023: 3580.0, 2024: 3560.0,
            }

            # Limpa registros anteriores nas 3 tabelas encadeadas para garantir idempotência exata
            conn.execute("DELETE FROM logs_monitoramento;")
            conn.execute("DELETE FROM previsoes_sistemicas;")
            conn.execute("DELETE FROM dados_historicos;")

            for _, row in df.iterrows():
                ano = int(row["ano"])
                cur_hist = conn.execute(
                    """INSERT INTO dados_historicos
                    (municipio, codigo_ibge, ano_safra, area_plantada_ha, area_colhida_ha,
                     rendimento_kg_ha, quebra_safra, deficit_hidrico_solo, dias_pico_calor,
                     precipitacao_enchimento, amplitude_termica)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        "Sorriso - MT",
                        "5107925",
                        ano,
                        600000.0,
                        600000.0,
                        rendimentos.get(ano, 3500.0),
                        int(row["quebra_safra"]),
                        int(row["deficit_hidrico_solo"]),
                        int(row["dias_pico_calor"]),
                        float(row["precipitacao_enchimento"]),
                        float(row["amplitude_termica"]),
                    ),
                )
                id_hist = cur_hist.lastrowid

                X_row = pd.DataFrame([row[FEATURES]])
                t0 = time.perf_counter()
                prob = float(pipe.predict_proba(X_row)[0, 1])
                alerta = int(prob >= 0.50)
                t_ms = round((time.perf_counter() - t0) * 1000, 3)

                cur_prev = conn.execute(
                    """INSERT INTO previsoes_sistemicas
                    (id_historico, ano_safra, modelo_utilizado, alerta_quebra, probabilidade_quebra,
                     limiar_decisao, tempo_inferencia_ms, origem_execucao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        id_hist,
                        ano,
                        "DecisionTreeClassifier (max_depth=2, balanced)",
                        alerta,
                        prob,
                        0.50,
                        t_ms,
                        "teste_temporal" if ano >= 2023 else "treino_historico",
                    ),
                )
                payload = {k: float(row[k]) for k in FEATURES}
                conn.execute(
                    """INSERT INTO logs_monitoramento
                    (id_previsao, nivel_log, mensagem, payload_entrada, ip_origem)
                    VALUES (?, ?, ?, ?, ?)""",
                    (
                        cur_prev.lastrowid,
                        "INFO",
                        f"Inferência oficial registrada para safra {ano} (Alerta={alerta})",
                        json.dumps(payload, ensure_ascii=False),
                        "127.0.0.1",
                    ),
                )

        contagens = {}
        for tabela in ("dados_historicos", "previsoes_sistemicas", "logs_monitoramento"):
            c = conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
            contagens[tabela] = c
        return contagens


if __name__ == "__main__":
    res = inicializar_e_popular_banco()
    print("Banco SQLite atualizado de forma idempotente:", res)
