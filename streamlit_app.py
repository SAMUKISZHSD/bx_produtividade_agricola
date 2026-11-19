"""SojaRisco - dashboard de apoio à decisão agroclimática.

O app carrega models/pipeline_final.joblib: regressão logística em tmax_enchimento.
O alerta dispara se a probabilidade for >= 0,45, o que equivale a tmax média de dez-fev >= 28,34 °C.
O Model Card classifica este pipeline como protótipo experimental, não aprovado para decisão operacional.
Acessibilidade: WCAG 2.1 AA (contraste de texto >= 4.5:1, semântica e suporte a tema claro/escuro).
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
import streamlit as st
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, roc_auc_score

# -----------------------------------------------------------------------------
# Configuração e caminhos
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODEL_DIR = BASE_DIR / "models"
ASSETS_DIR = BASE_DIR / "icons"
DATA_PROCESSED_PATH = PROCESSED_DIR / "dados_modelo_s4.csv"
MODEL_PATH = MODEL_DIR / "pipeline_final.joblib"
LIMIAR_PATH = MODEL_DIR / "limiar_congelado.json"
DB_PATH = DATA_DIR / "monitoramento_safra.db"
LOG_DIR = BASE_DIR / "logs"
LOG_PATH = LOG_DIR / "sojarisco.log"

APP_NAME = "SojaRisco"
MUNICIPIO = os.getenv("SOJARISCO_MUNICIPIO", "Sorriso")
UF = os.getenv("SOJARISCO_UF", "MT")
LATITUDE = float(os.getenv("SOJARISCO_LATITUDE", "-12.5414"))
LONGITUDE = float(os.getenv("SOJARISCO_LONGITUDE", "-55.7269"))
FEATURE = "tmax_enchimento"
MODELO_NOME = "LogisticRegression L2 (C=1.0, class_weight=balanced)"
MODEL_FEATURES = {FEATURE: FEATURE}

def _ler_limiar() -> tuple[float, float]:
    cfg = json.loads(LIMIAR_PATH.read_text(encoding="utf-8"))
    return float(cfg["limiar_otimo"]), float(cfg["limiar_celsius"])

LIMIAR_ALERTA, LIMIAR_CELSIUS = _ler_limiar()

st.set_page_config(
    page_title="SojaRisco | Inteligência Agroclimática",
    page_icon=str(ASSETS_DIR / "soybean.svg") if (ASSETS_DIR / "soybean.svg").exists() else "🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Helper para carregar e colorir SVGs com atributos a11y
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_svg(icon_name: str, color: str | None = None, width: int = 24, height: int = 24) -> str:
    """Lê um SVG da pasta assets/icons, ajusta dimensões e atributos WCAG/a11y."""
    svg_path = ASSETS_DIR / f"{icon_name}.svg"
    if not svg_path.exists():
        return ""
    try:
        content = svg_path.read_text(encoding="utf-8")
        if "aria-hidden=" not in content:
            content = content.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1)
        if f'width="{width}"' not in content:
            content = content.replace("<svg ", f'<svg width="{width}" height="{height}" style="vertical-align: middle; flex-shrink: 0;" ', 1)
        if color:
            content = content.replace('stroke="#153D2B"', f'stroke="{color}"')
        return content
    except Exception:
        return ""


# -----------------------------------------------------------------------------
# Gerenciamento de Tema (Dark / Light) com WCAG 2.1 AA e st.session_state
# -----------------------------------------------------------------------------
def obter_tipo_tema() -> str:
    """Detecta o tema ativo do Streamlit (dark ou light) com fallback seguro."""
    try:
        tema = getattr(st.context, "theme", None)
        tipo = getattr(tema, "type", None)
        if tipo in ("dark", "light"):
            return tipo
    except Exception:
        pass
    return "light"


if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = obter_tipo_tema() == "dark"

is_dark = bool(st.session_state["dark_mode"])

# Tokens de cores com contraste auditado (WCAG 2.1 AA >= 4.5:1 para texto normal)
if is_dark:
    theme_vars = """
        --bg-app: #0e1612;
        --bg-card: #15241c;
        --bg-card-alt: #1a2e24;
        --bg-hero: linear-gradient(135deg, #0d2217 0%, #153d2b 60%, #1b4f37 100%);
        --text-title: #f1f7f3;
        --text-body: #d8e5dc;
        --text-muted: #a3b8ac;
        --border-color: #274233;
        --sidebar-bg: #091510;
        --sidebar-bg-alt: #11241b;
        --sidebar-text: #e8f3ec;
        --sidebar-muted: #9eb5a7;
        --brand-green: #22c55e;
        --brand-green-dark: #16a34a;
        --brand-accent: #fbbf24;
        --alert-danger: #f87171;
        --alert-danger-bg: #351616;
        --alert-warn: #fbbf24;
        --alert-warn-bg: #33260c;
        --alert-success: #4ade80;
        --alert-success-bg: #11301c;
        --icon-color: #4ade80;
        --kpi-shadow: 0 4px 20px rgba(0,0,0,0.35);
        --btn-pri-bg: #22c55e;
        --btn-pri-text: #091510;
        --btn-sec-bg: #1a2e24;
        --btn-sec-text: #f1f7f3;
        --btn-sec-border: #274233;
    """
    svg_color_main = "#4ade80"
    svg_color_body = "#d8e5dc"
else:
    theme_vars = """
        --bg-app: #f4f7f4;
        --bg-card: #ffffff;
        --bg-card-alt: #eaf1ec;
        --bg-hero: linear-gradient(135deg, #153d2b 0%, #1f6b45 58%, #2e8b57 100%);
        --text-title: #0f1c15;
        --text-body: #1c2e24;
        --text-muted: #3d5045;
        --border-color: #c6d4cb;
        --sidebar-bg: #102d20;
        --sidebar-bg-alt: #163a29;
        --sidebar-text: #edf5ef;
        --sidebar-muted: #b0c7b8;
        --brand-green: #1b5e39;
        --brand-green-dark: #153d2b;
        --brand-accent: #b45309;
        --alert-danger: #b91c1c;
        --alert-danger-bg: #fef2f2;
        --alert-warn: #b45309;
        --alert-warn-bg: #fffbeb;
        --alert-success: #15803d;
        --alert-success-bg: #f0fdf4;
        --icon-color: #1b5e39;
        --kpi-shadow: 0 4px 16px rgba(21,61,43,0.06);
        --btn-pri-bg: #1b5e39;
        --btn-pri-text: #ffffff;
        --btn-sec-bg: #ffffff;
        --btn-sec-text: #153d2b;
        --btn-sec-border: #1b5e39;
    """
    svg_color_main = "#153d2b"
    svg_color_body = "#1c2e24"

st.markdown(
    f"""
    <style>
    :root {{
        {theme_vars}
    }}

    /* Base da Aplicação - Fontes nativas de alta performance (sem @import) */
    .stApp {{
        background: var(--bg-app) !important;
        color: var(--text-body) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}

    /* Tipografia de Alta Acessibilidade (WCAG AA) */
    h1, h2, h3, h4, h5, h6 {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        color: var(--text-title) !important;
        font-weight: 800 !important;
        letter-spacing: -0.025em;
    }}
    p, span, label, div {{
        color: var(--text-body);
    }}

    /* Sidebar Acessível - Estilização Específica sem Seletor Universal Destrutivo */
    [data-testid="stSidebar"] {{
        background: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border-color);
    }}
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] strong {{
        color: var(--sidebar-text) !important;
    }}
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stCaption {{
        color: var(--sidebar-muted) !important;
        font-size: 13px !important;
    }}
    [data-testid="stSidebar"] .stSelectbox label, 
    [data-testid="stSidebar"] .stToggle label,
    [data-testid="stSidebar"] .stCheckbox label {{
        color: var(--sidebar-text) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }}
    [data-testid="stSidebar"] hr {{
        border-color: rgba(255,255,255,0.15) !important;
    }}

    /* Botões nativos na área principal e sidebar com alto contraste WCAG AA */
    .stButton > button,
    .stDownloadButton > button {{
        border-radius: 8px;
        font-weight: 700;
        font-size: 14px;
        padding: 8px 18px;
        transition: all 0.15s ease-in-out;
        cursor: pointer;
    }}

    /* Botões primários */
    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"] {{
        background-color: var(--btn-pri-bg) !important;
        color: var(--btn-pri-text) !important;
        border: 1px solid var(--brand-green-dark) !important;
    }}
    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover {{
        background-color: var(--brand-green-dark) !important;
        border-color: var(--brand-green-dark) !important;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }}

    /* Botões secundários (área principal) */
    .stButton > button[kind="secondary"],
    .stDownloadButton > button[kind="secondary"] {{
        background-color: var(--btn-sec-bg) !important;
        color: var(--btn-sec-text) !important;
        border: 1px solid var(--btn-sec-border) !important;
    }}
    .stButton > button[kind="secondary"]:hover,
    .stDownloadButton > button[kind="secondary"]:hover {{
        background-color: var(--bg-card-alt) !important;
        color: var(--btn-sec-text) !important;
    }}

    /* Botões na sidebar */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stDownloadButton > button {{
        background-color: #1f6b45 !important;
        color: #ffffff !important;
        border: 1px solid #4ade80 !important;
    }}
    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] .stDownloadButton > button:hover {{
        background-color: #288355 !important;
        border-color: #86efac !important;
        color: #ffffff !important;
    }}

    /* Focus-visible para navegação por teclado e a11y */
    .stButton > button:focus-visible,
    .stDownloadButton > button:focus-visible {{
        outline: 2px solid var(--brand-green) !important;
        outline-offset: 2px !important;
    }}

    /* Container Principal */
    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 3.5rem;
        max-width: 1450px;
    }}

    /* Header Hero com Alto Contraste */
    .hero {{
        background: var(--bg-hero);
        border-radius: 20px;
        padding: 28px 32px;
        color: #ffffff !important;
        position: relative;
        overflow: hidden;
        box-shadow: 0 12px 30px rgba(0,0,0,0.15);
        margin: 4px 0 24px;
        border: 1px solid rgba(255,255,255,0.1);
    }}
    .hero * {{
        color: #ffffff !important;
    }}
    .hero-kicker {{
        color: #d1fae5 !important;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .hero-title {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-size: clamp(26px, 3.2vw, 38px);
        font-weight: 800;
        letter-spacing: -1px;
        line-height: 1.15;
        margin: 0 0 10px;
    }}
    .hero-copy {{
        color: #e2f1e8 !important;
        font-size: 15px;
        max-width: 740px;
        line-height: 1.6;
        margin: 0;
    }}
    .hero-meta {{
        margin-top: 18px;
        color: #d1fae5 !important;
        font-size: 13.5px;
        font-weight: 600;
        display: flex;
        gap: 20px;
        flex-wrap: wrap;
    }}
    .hero-meta span {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }}

    /* Cards e Métricas com Contraste WCAG 2.1 AA */
    .metric-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 20px 22px;
        min-height: 135px;
        box-shadow: var(--kpi-shadow);
        transition: transform .15s ease, box-shadow .15s ease;
    }}
    .metric-card:hover {{
        transform: translateY(-2px);
    }}
    .metric-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }}
    .metric-label {{
        color: var(--text-muted);
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }}
    .metric-value {{
        color: var(--text-title);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -1px;
        line-height: 1.1;
    }}
    .metric-foot {{
        color: var(--text-muted);
        font-size: 13px;
        font-weight: 500;
        margin-top: 6px;
    }}

    /* Painéis e Diagnóstico */
    .panel {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 22px 24px;
        box-shadow: var(--kpi-shadow);
    }}
    .risk-card {{
        border-radius: 16px;
        padding: 24px 26px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        box-shadow: var(--kpi-shadow);
        height: 100%;
    }}
    .risk-high {{
        border-left: 6px solid var(--alert-danger);
    }}
    .risk-low {{
        border-left: 6px solid var(--alert-success);
    }}
    .risk-demo {{
        border-left: 6px solid var(--alert-warn);
    }}
    .risk-label {{
        color: var(--text-muted);
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .risk-title {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-size: 24px;
        font-weight: 800;
        margin: 10px 0 6px;
        color: var(--text-title);
        line-height: 1.25;
    }}
    .risk-description {{
        color: var(--text-body);
        font-size: 14.5px;
        line-height: 1.55;
    }}

    /* Barra de Progresso Acessível */
    .progress-track {{
        height: 10px;
        border-radius: 99px;
        background: var(--bg-card-alt);
        overflow: hidden;
        margin: 14px 0 6px;
        border: 1px solid var(--border-color);
    }}
    .progress-fill {{
        height: 100%;
        border-radius: 99px;
        background: linear-gradient(90deg, #4ade80, #15803d);
        transition: width .6s ease;
    }}

    /* Seções */
    .section-head {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 26px 0 14px;
    }}
    .section-title {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-size: 20px;
        font-weight: 800;
        letter-spacing: -0.4px;
        color: var(--text-title);
        margin: 0;
    }}
    .section-sub {{
        color: var(--text-muted);
        font-size: 13.5px;
        margin: 2px 0 0;
    }}

    /* Badges / Pills com contraste verificado */
    .pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 99px;
        font-size: 12.5px;
        font-weight: 700;
        background: var(--alert-success-bg);
        color: var(--alert-success);
        border: 1px solid var(--border-color);
    }}
    .pill-warn {{
        background: var(--alert-warn-bg);
        color: var(--alert-warn);
    }}
    .pill-danger {{
        background: var(--alert-danger-bg);
        color: var(--alert-danger);
    }}

    /* Avisos e Rodapé */
    .notice {{
        background: var(--alert-warn-bg);
        border: 1px solid var(--alert-warn);
        border-radius: 12px;
        padding: 14px 18px;
        color: var(--text-title);
        font-size: 14px;
        line-height: 1.55;
    }}
    .notice strong {{
        color: var(--alert-warn);
    }}
    .footer {{
        border-top: 1px solid var(--border-color);
        padding-top: 18px;
        margin-top: 32px;
        color: var(--text-muted);
        font-size: 13px;
        display: flex;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
    }}

    /* Abas nativas */
    div[data-testid="stTabs"] button {{
        font-weight: 700;
        font-size: 15px;
        color: var(--text-muted) !important;
    }}
    div[data-testid="stTabs"] button[aria-selected="true"] {{
        color: var(--brand-green) !important;
        border-bottom-color: var(--brand-green) !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Logs e banco de dados SQLite
# -----------------------------------------------------------------------------
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_PATH), level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@st.cache_resource(show_spinner=False)
def inicializar_banco() -> dict[str, int]:
    from src.database import inicializar_e_popular_banco
    return inicializar_e_popular_banco()


def salvar_previsao(ano: int, alerta: int, prob: float, tempo_ms: float,
                    modelo: str, payload: dict[str, Any], origem: str) -> None:
    with get_db_connection() as conn:
        cur = conn.execute(
            """INSERT INTO previsoes_sistemicas
            (ano_safra, municipio, modelo_utilizado, alerta_quebra, probabilidade_quebra,
             limiar_decisao, limiar_celsius, tempo_inferencia_ms, origem_execucao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ano, MUNICIPIO, modelo, alerta, prob, LIMIAR_ALERTA, LIMIAR_CELSIUS, tempo_ms, origem),
        )
        conn.execute(
            "INSERT INTO logs_monitoramento (id_previsao,nivel_log,mensagem,payload_entrada) VALUES (?,?,?,?)",
            (cur.lastrowid, "INFO", f"Inferência registrada para safra {ano}", json.dumps(payload, ensure_ascii=False)),
        )


_contagens_banco = inicializar_banco()

# -----------------------------------------------------------------------------
# Carregamento de Dados e Modelo
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def carregar_historico() -> pd.DataFrame:
    if DATA_PROCESSED_PATH.exists():
        df = pd.read_csv(DATA_PROCESSED_PATH)
        if "ano" in df.columns and "ano_safra" not in df.columns:
            df = df.rename(columns={"ano": "ano_safra"})
        if "safra" in df.columns and "ano_safra" not in df.columns:
            df = df.rename(columns={"safra": "ano_safra"})
        return df
    return pd.DataFrame()


@st.cache_resource(show_spinner=False)
def carregar_modelo():
    if not MODEL_PATH.exists():
        return None, "DEMONSTRAÇÃO", "Artefato do modelo ainda não disponível."
    try:
        import joblib
        model = joblib.load(MODEL_PATH)
        if not hasattr(model, "predict_proba"):
            raise TypeError("O pipeline carregado não implementa predict_proba().")
        return model, "REAL", "Pipeline serializado carregado com sucesso."
    except Exception as exc:
        logging.exception("Falha ao carregar modelo")
        return None, "ERRO", f"Não foi possível carregar o modelo: {exc}"


@st.cache_data(ttl=1800, show_spinner=False)
def consultar_nasa_power(ano: int) -> dict[str, Any]:
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "PRECTOTCORR,T2M_MAX,T2M_MIN",
        "community": "AG",
        "longitude": LONGITUDE,
        "latitude": LATITUDE,
        "start": f"{ano}0101",
        "end": f"{ano}1231",
        "format": "JSON",
    }
    response = requests.get(url, params=params, timeout=25)
    response.raise_for_status()
    payload = response.json()
    properties = payload.get("properties", {}).get("parameter", {})
    precip = pd.to_numeric(pd.Series(properties.get("PRECTOTCORR", {})), errors="coerce")
    tmax = pd.to_numeric(pd.Series(properties.get("T2M_MAX", {})), errors="coerce")
    tmin = pd.to_numeric(pd.Series(properties.get("T2M_MIN", {})), errors="coerce")
    return {
        "precipitacao_anual_mm": float(precip.replace(-999, np.nan).sum()),
        "temperatura_max_media_c": float(tmax.replace(-999, np.nan).mean()),
        "temperatura_min_media_c": float(tmin.replace(-999, np.nan).mean()),
        "dias_calor_35c": int((tmax.replace(-999, np.nan) >= 35).sum()),
        "periodo": str(ano),
        "fonte": "NASA POWER Daily API",
    }


@st.cache_data(ttl=3600, show_spinner=False)
def dados_demo() -> pd.DataFrame:
    rng = np.random.default_rng(21)
    anos = np.arange(2015, 2025)
    tmax = np.array([28.1, 28.6, 27.8, 29.2, 28.0, 29.8, 28.7, 30.1, 29.4, 30.3])
    deficit = np.array([12, 18, 9, 27, 14, 31, 22, 38, 17, 25], dtype=float)
    calor = np.array([1, 2, 0, 4, 1, 5, 3, 7, 2, 4], dtype=float)
    chuva = np.array([430, 390, 510, 280, 450, 230, 320, 190, 470, 300], dtype=float)
    amplitude = np.array([25.1, 26.4, 24.8, 29.1, 25.7, 30.2, 28.1, 31.0, 26.0, 28.8])
    return pd.DataFrame({
        "ano_safra": anos,
        "tmax_enchimento": tmax,
        "deficit_hidrico_solo": deficit + rng.normal(0, 1, len(anos)),
        "dias_pico_calor": calor,
        "amplitude_termica": amplitude,
        "precipitacao_enchimento": chuva,
        "quebra_safra": [0, 0, 0, 1, 0, 1, 0, 1, 0, 1],
    })


df_historico = carregar_historico()
modelo, status_modelo, mensagem_modelo = carregar_modelo()
if df_historico.empty:
    df_visual = dados_demo()
    origem_dados = "DEMONSTRAÇÃO - dados ilustrativos"
else:
    df_visual = df_historico.copy()
    origem_dados = "Dados processados do projeto"


def executar_predicao(features: dict[str, float], modo_simulacao: bool = False):
    inicio = time.perf_counter()
    if modelo is not None and status_modelo == "REAL" and not modo_simulacao:
        tmax = float(features.get(FEATURE, features.get("amplitude_termica", LIMIAR_CELSIUS)))
        X = pd.DataFrame({FEATURE: [tmax]})
        probas = modelo.predict_proba(X)[0]
        classes = list(getattr(modelo, "classes_", [0, 1]))
        if 1 not in classes:
            raise ValueError("A classe positiva 1 não foi encontrada em model.classes_.")
        prob = float(np.clip(float(probas[classes.index(1)]), 0.0, 1.0))
        nome = modelo.__class__.__name__
        tipo = "REAL"
    else:
        tmax = float(features.get(FEATURE, LIMIAR_CELSIUS))
        score = (tmax - 24.0) / 10.0
        prob = float(np.clip(score, 0.03, 0.97))
        nome = "Simulação ilustrativa (sem modelo serializado)"
        tipo = "SIMULAÇÃO"
    tempo_ms = round((time.perf_counter() - inicio) * 1000, 3)
    return int(prob >= LIMIAR_ALERTA), prob, tempo_ms, nome, tipo


# -----------------------------------------------------------------------------
# Sidebar com Logo Oficial, Indicador de Tema WCAG e Navegação
# -----------------------------------------------------------------------------
with st.sidebar:
    # Logo vetorial oficial
    logo_svg_path = ASSETS_DIR / "sojarisco_logo.svg"
    if logo_svg_path.exists():
        st.image(str(logo_svg_path), use_container_width=True)
    else:
        st.markdown("### 🌱 SojaRisco")

    st.markdown(f"**{MUNICIPIO} - {UF}**")
    st.caption("Assistente Inteligente de Apoio à Decisão Agrícola")

    st.divider()

    # Alternância de Modo Claro / Modo Escuro (WCAG AA)
    btn_theme_label = "☀️ Modo Claro" if is_dark else "🌙 Modo Escuro"
    if st.button(btn_theme_label, key="theme_toggle", use_container_width=True):
        st.session_state["dark_mode"] = not is_dark
        st.rerun()

    st.divider()
    anos_disponiveis = sorted(pd.to_numeric(df_visual.get("ano_safra", pd.Series([2024])), errors="coerce").dropna().astype(int).unique().tolist())
    ano_atual = st.selectbox("Safra de referência", anos_disponiveis, index=len(anos_disponiveis)-1)
    mostrar_tecnico = st.toggle("Exibir detalhes técnicos de ML", value=False)

    st.divider()
    status_cor = "🟢" if status_modelo == "REAL" else ("🟡" if status_modelo == "DEMONSTRAÇÃO" else "🔴")
    st.markdown(f"**{status_cor} Motor: {status_modelo}**")
    if status_modelo == "REAL":
        st.caption("Pipeline oficial serializado (LogisticRegression L2) ativo e integrado ao SQLite.")
    else:
        st.caption("O assistente opera em modo de simulação até a integração do artefato pipeline_final.joblib.")
    if mostrar_tecnico:
        st.markdown("---")
        st.markdown(f"**{load_svg('settings', '#b0c7b8', 16, 16)} Parâmetros do sistema**", unsafe_allow_html=True)
        st.code(f"Artefato: {MODEL_PATH.name}\nLimiar: {LIMIAR_ALERTA:.0%}\nBase: {origem_dados}", language="text")
        st.caption(mensagem_modelo)

    st.markdown("---")
    st.caption("Estimativas de apoio à decisão para a lavoura. Não substituem assistência técnica agronômica presencial.")

# -----------------------------------------------------------------------------
# Cabeçalho Principal (Hero) com Hierarquia H1 Única
# -----------------------------------------------------------------------------
icon_loc = load_svg("location", "#d1fae5", 16, 16)
icon_soy = load_svg("soybean", "#d1fae5", 16, 16)
icon_cal = load_svg("calendar", "#d1fae5", 16, 16)
icon_shield = load_svg("shield", "#d1fae5", 18, 18)

st.markdown(
    f"""
    <div class="hero">
      <div class="hero-kicker">{icon_shield} PAINEL DE INTELIGÊNCIA DA SAFRA · {MUNICIPIO.upper()} / {UF}</div>
      <h1 class="hero-title">Antecipe riscos climáticos.<br>Proteja a sua produtividade.</h1>
      <p class="hero-copy">Acompanhe indicadores agroclimáticos em tempo real e antecipe riscos severos de quebra de safra para a soja em Sorriso-MT através de inteligência analítica prática.</p>
      <div class="hero-meta">
        <span>{icon_loc} {MUNICIPIO}, {UF}</span>
        <span>{icon_soy} Soja em grão</span>
        <span>{icon_cal} Safra {ano_atual}</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if status_modelo == "DEMONSTRAÇÃO":
    st.warning("⚠️ **Ambiente de demonstração:** o pipeline de inferência real está em fase final de validação. Os dados e alertas apresentados são ilustrativos para navegação.", icon="⚠️")
elif status_modelo == "ERRO":
    st.error(f"Não foi possível carregar o modelo de predição: {mensagem_modelo}")

# Abas com ícones vetoriais
tab_title_1 = "Visão da safra"
tab_title_2 = "Histórico e desempenho"
tab_title_3 = "Sobre o assistente"

aba_previsao, aba_historico, aba_sistema = st.tabs([f"🌱 {tab_title_1}", f"📊 {tab_title_2}", f"ℹ️ {tab_title_3}"])

# -----------------------------------------------------------------------------
# Aba 1 - Visão da Safra (Experiência do Produtor com Assets Vetoriais)
# -----------------------------------------------------------------------------
with aba_previsao:
    linha = df_visual[pd.to_numeric(df_visual["ano_safra"], errors="coerce") == ano_atual]
    if not linha.empty:
        r = linha.iloc[0]
        defaults = {
            "tmax_enchimento": float(r.get("tmax_enchimento", LIMIAR_CELSIUS)),
            "deficit_hidrico_solo": float(r.get("deficit_hidrico_solo", 18)),
            "dias_pico_calor": float(r.get("dias_pico_calor", 2)),
            "precipitacao_enchimento": float(r.get("precipitacao_enchimento", 400)),
            "amplitude_termica": float(r.get("amplitude_termica", 26)),
        }
        quebra_observada = r.get("quebra_safra", None)
    else:
        defaults = {"tmax_enchimento": LIMIAR_CELSIUS, "deficit_hidrico_solo": 18.0, "dias_pico_calor": 2.0,
                    "precipitacao_enchimento": 400.0, "amplitude_termica": 26.0}
        quebra_observada = None

    alerta, prob, tempo_ms, nome_modelo, tipo_predicao = executar_predicao(defaults)
    risco_texto = "Atenção: risco elevado de quebra" if alerta else "Condições climáticas favoráveis"
    risco_classe = "risk-high" if alerta else "risk-low"
    risco_descricao = (
        "Os indicadores desta safra apresentam estresse hídrico e térmico acima do tolerável, recomendando ação preventiva no planejamento e comercialização."
        if alerta else
        "Os fatores agroclimáticos monitorados encontram-se dentro da média histórica saudável para a produtividade esperada da soja em Sorriso."
    )

    # Cards de Métricas com Ícones SVG
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        icon_brain = load_svg("brain", svg_color_main, 24, 24)
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-header'>
                    <span class='metric-label'>Risco Estimado</span>
                    {icon_brain}
                </div>
                <div class='metric-value'>{prob:.0%}</div>
                <div class='metric-foot'>Limiar de alerta calibrado: {LIMIAR_ALERTA:.0%}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        icon_rain = load_svg("rain", svg_color_main, 24, 24)
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-header'>
                    <span class='metric-label'>Chuva no Enchimento</span>
                    {icon_rain}
                </div>
                <div class='metric-value'>{defaults['precipitacao_enchimento']:.0f} <span style='font-size:18px;font-weight:600'>mm</span></div>
                <div class='metric-foot'>Precipitação na fase crítica (R5-R6)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        icon_sun = load_svg("sun", svg_color_main, 24, 24)
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-header'>
                    <span class='metric-label'>Picos de Calor</span>
                    {icon_sun}
                </div>
                <div class='metric-value'>{defaults['dias_pico_calor']:.0f} <span style='font-size:18px;font-weight:600'>dias</span></div>
                <div class='metric-foot'>Temperaturas máximas ≥ 35 °C</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Diagnóstico da Safra com Hierarquia H2 -> H3
    st.markdown(
        f"""
        <div class='section-head'>
            {load_svg('dashboard', svg_color_main, 22, 22)}
            <div>
                <h2 class='section-title'>Diagnóstico da Safra</h2>
                <p class='section-sub'>Leitura consolidada dos fatores determinantes para a produtividade</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.2, 1], gap="medium")
    with left:
        icon_alert = load_svg("alert" if alerta else "shield", "#dc2626" if alerta else "#16a34a", 20, 20)
        st.markdown(
            f"""
            <div class='risk-card {risco_classe}'>
                <div class='risk-label'>{icon_alert} Diagnóstico do Assistente · {tipo_predicao}</div>
                <h3 class='risk-title'>{risco_texto}</h3>
                <div class='risk-description'>{risco_descricao}</div>
                <div class='progress-track'>
                    <div class='progress-fill' style='width:{prob*100:.1f}%;'></div>
                </div>
                <div style='display:flex;justify-content:space-between;font-size:13px;font-weight:700;margin-top:6px;'>
                    <span>Probabilidade calculada</span>
                    <span>{prob:.1%}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Motor: {nome_modelo} · Inferência medida: {tempo_ms:.3f} ms")

    with right:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown(f"**{load_svg('thermometer', svg_color_main, 18, 18)} Condições Observadas**", unsafe_allow_html=True)
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.metric("Déficit hídrico no solo", f"{defaults['deficit_hidrico_solo']:.1f} dias")
        with col_r2:
            st.metric("Amplitude térmica", f"{defaults['amplitude_termica']:.1f} °C")
        if quebra_observada is not None and pd.notna(quebra_observada):
            resultado_hist = "Quebra severa de produtividade" if int(quebra_observada) == 1 else "Safra sem quebra registrada"
            st.caption(f"Registro histórico oficial (IBGE PAM): **{resultado_hist}**")
        st.markdown("</div>", unsafe_allow_html=True)

    # Evolução Agroclimática
    st.markdown(
        f"""
        <div class='section-head'>
            {load_svg('chart_line', svg_color_main, 22, 22)}
            <div>
                <h2 class='section-title'>Evolução Histórica dos Indicadores</h2>
                <p class='section-sub'>Acompanhe chuva acumulada no enchimento e déficit hídrico ao longo das safras</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    chart_cols = [c for c in ["precipitacao_enchimento", "deficit_hidrico_solo"] if c in df_visual.columns]
    if chart_cols:
        chart_df = df_visual.set_index("ano_safra")[chart_cols].copy()
        chart_df.columns = ["Chuva Enchimento (mm)", "Déficit Hídrico (dias)"]
        st.line_chart(chart_df, height=260, use_container_width=True)

    # Simulador de Cenários isolado com @st.fragment para performance
    @st.fragment
    def render_simulador_cenarios(defaults_sim: dict[str, float]) -> None:
        with st.expander("🧪 Explorar cenários na fazenda - Simulador Agroclimático", expanded=False):
            st.info("Altere a temperatura máxima média de dezembro a fevereiro para calcular o índice atual do modelo.")
            sc1, sc2 = st.columns(2)
            with sc1:
                sim_tmax = st.slider("Temperatura máxima média no enchimento (°C)", 20.0, 35.0, float(defaults_sim.get("tmax_enchimento", LIMIAR_CELSIUS)), 0.1)
            with sc2:
                st.metric("Limiar oficial", f"{LIMIAR_CELSIUS:.2f} °C")

            if st.button("Calcular Risco do Cenário", type="primary", use_container_width=True):
                sim_features = {
                    "tmax_enchimento": sim_tmax,
                }
                sim_alerta, sim_prob, sim_ms, sim_nome, sim_tipo = executar_predicao(sim_features, modo_simulacao=False)
                st.session_state["ultimo_cenario"] = {"alerta": sim_alerta, "prob": sim_prob, "features": sim_features}

            if "ultimo_cenario" in st.session_state:
                cenario = st.session_state["ultimo_cenario"]
                nivel = "Risco ELEVADO de quebra" if cenario["alerta"] else "Risco MODERADO / BAIXO"
                st.success(f"Resultado do Cenário: **{cenario['prob']:.1%} de probabilidade de quebra** ({nivel}).")

    render_simulador_cenarios(defaults)

    # Consulta de Clima na NASA POWER isolada com @st.fragment
    @st.fragment
    def render_consulta_nasa(ano_padrao: int) -> None:
        st.markdown(
            f"""
            <div class='section-head'>
                {load_svg('weather', svg_color_main, 22, 22)}
                <div>
                    <h2 class='section-title'>Consulta de Dados Agrometeorológicos Reais</h2>
                    <p class='section-sub'>Conexão direta com a API pública da NASA POWER para Sorriso-MT</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        api_col, api_info = st.columns([1, 2])
        with api_col:
            ano_api = st.number_input("Ano da consulta", min_value=1985, max_value=date.today().year, value=ano_padrao, step=1)
            consultar = st.button("Consultar NASA POWER", use_container_width=True)
        with api_info:
            st.markdown("<div class='notice'><strong>Fonte Oficial:</strong> A consulta recupera a série histórica de radiação e precipitação medida por satélite e reanálise meteorológica para as coordenadas do município.</div>", unsafe_allow_html=True)

        if consultar:
            try:
                with st.spinner("Buscando dados agrometeorológicos na NASA POWER..."):
                    dados_api = consultar_nasa_power(int(ano_api))
                st.success("Dados agroclimáticos recebidos com sucesso da NASA POWER.")
                api1, api2, api3 = st.columns(3)
                with api1:
                    st.metric("Chuva anual acumulada", f"{dados_api['precipitacao_anual_mm']:.0f} mm")
                with api2:
                    st.metric("Temperatura máxima média", f"{dados_api['temperatura_max_media_c']:.1f} °C")
                with api3:
                    st.metric("Dias com calor ≥ 35 °C", f"{dados_api['dias_calor_35c']} dias")
                st.caption(f"Fonte: {dados_api['fonte']} · Período consultado: {dados_api['periodo']}")
            except Exception as exc:
                logging.exception("Erro ao consultar NASA POWER")
                st.error(f"Não foi possível conectar com a API da NASA POWER no momento: {exc}")

    render_consulta_nasa(ano_atual)

    # Registro de Histórico isolado com @st.fragment
    @st.fragment
    def render_salvar_registro(ano_salvar: int, alerta_salvar: int, prob_salvar: float, tempo_salvar: float, modelo_salvar: str, defaults_salvar: dict[str, float]) -> None:
        st.markdown("---")
        if st.button("Salvar Registro Desta Análise"):
            try:
                salvar_previsao(ano_salvar, alerta_salvar, prob_salvar, tempo_salvar, modelo_salvar, defaults_salvar, "dashboard")
                st.success("Análise persistida com sucesso no banco de monitoramento local.")
            except Exception as exc:
                st.error(f"Erro ao salvar previsão no banco: {exc}")

    render_salvar_registro(ano_atual, alerta, prob, tempo_ms, nome_modelo, defaults)

# -----------------------------------------------------------------------------
# Aba 2 - Histórico e Desempenho
# -----------------------------------------------------------------------------
with aba_historico:
    st.markdown(
        f"""
        <div class='section-head'>
            {load_svg('database', svg_color_main, 22, 22)}
            <div>
                <h2 class='section-title'>Base de Dados Agroclimática Consolidada</h2>
                <p class='section-sub'>Série histórica combinada (NASA POWER + PAM/IBGE) utilizada no projeto</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not df_historico.empty:
        cols = [c for c in ["ano_safra", "precipitacao_enchimento", "deficit_hidrico_solo", "dias_pico_calor", "amplitude_termica", "quebra_safra"] if c in df_historico.columns]
        df_display = df_historico[cols].sort_values("ano_safra", ascending=False).copy()
        nomes_colunas = {
            "ano_safra": "Safra",
            "precipitacao_enchimento": "Chuva Enchimento (mm)",
            "deficit_hidrico_solo": "Déficit Hídrico (dias)",
            "dias_pico_calor": "Picos de Calor (dias)",
            "amplitude_termica": "Amplitude Térmica (°C)",
            "quebra_safra": "Quebra Observada",
        }
        df_display = df_display.rename(columns=nomes_colunas)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado processado encontrado em data/processed/dados_modelo.csv. A visualização demonstrativa utiliza valores de referência.")

    st.markdown(
        f"""
        <div class='section-head'>
            {load_svg('chart_bar', svg_color_main, 22, 22)}
            <div>
                <h2 class='section-title'>Como o modelo se saiu no teste temporal</h2>
                <p class='section-sub'>Safras 2019–2024: quebras observadas e alertas do pipeline ativo, por município</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    colunas_avaliacao = {"ano_safra", "split", "quebra_safra", FEATURE}
    faltantes_avaliacao = colunas_avaliacao - set(df_historico.columns)
    if modelo is None or status_modelo != "REAL":
        st.warning("O gráfico de desempenho requer o pipeline serializado carregado; nenhum resultado demonstrativo será apresentado como métrica real.")
    elif faltantes_avaliacao:
        st.error(f"Não é possível avaliar o modelo: faltam colunas na base histórica: {sorted(faltantes_avaliacao)}")
    else:
        dados_teste = df_historico.loc[df_historico["split"].eq("teste")].copy()
        if dados_teste.empty:
            st.warning("A base não contém linhas do teste temporal congelado.")
        else:
            X_teste = dados_teste[[FEATURE]]
            prob_teste = modelo.predict_proba(X_teste)[:, list(modelo.classes_).index(1)]
            y_teste = pd.to_numeric(dados_teste["quebra_safra"], errors="raise").astype(int).to_numpy()
            alerta_teste = (prob_teste >= LIMIAR_ALERTA).astype(int)
            tn, fp, fn, tp = confusion_matrix(y_teste, alerta_teste, labels=[0, 1]).ravel()
            auc_teste = roc_auc_score(y_teste, prob_teste) if np.unique(y_teste).size == 2 else float("nan")

            teste_sem_2024 = dados_teste["ano_safra"].astype(int).to_numpy() != 2024
            tn_sem24, fp_sem24, fn_sem24, tp_sem24 = confusion_matrix(
                y_teste[teste_sem_2024], alerta_teste[teste_sem_2024], labels=[0, 1]
            ).ravel()

            met_cols = st.columns(4)
            met_cols[0].metric("Acurácia", f"{accuracy_score(y_teste, alerta_teste):.1%}")
            met_cols[1].metric("Recall das quebras", f"{recall_score(y_teste, alerta_teste, zero_division=0):.1%}")
            met_cols[2].metric("Precisão dos alertas", f"{precision_score(y_teste, alerta_teste, zero_division=0):.1%}")
            met_cols[3].metric("AUC", f"{auc_teste:.3f}" if np.isfinite(auc_teste) else "N/A")

            dados_teste["alerta_modelo"] = alerta_teste
            dados_teste["verdadeiro_positivo"] = (
                dados_teste["quebra_safra"].astype(int).eq(1) & dados_teste["alerta_modelo"].eq(1)
            ).astype(int)
            dados_teste["falso_positivo"] = (
                dados_teste["quebra_safra"].astype(int).eq(0) & dados_teste["alerta_modelo"].eq(1)
            ).astype(int)
            dados_teste["falso_negativo"] = (
                dados_teste["quebra_safra"].astype(int).eq(1) & dados_teste["alerta_modelo"].eq(0)
            ).astype(int)
            grafico_safras = (
                dados_teste.groupby("ano_safra", as_index=False)
                .agg(
                    **{
                        "Quebras observadas": ("quebra_safra", "sum"),
                        "Quebras alertadas corretamente": ("verdadeiro_positivo", "sum"),
                        "Falsos alarmes": ("falso_positivo", "sum"),
                        "Quebras não alertadas": ("falso_negativo", "sum"),
                    }
                )
                .rename(columns={"ano_safra": "Safra"})
                .sort_values("Safra")
            )
            st.bar_chart(
                grafico_safras,
                x="Safra",
                y=["Quebras observadas", "Quebras alertadas corretamente", "Falsos alarmes", "Quebras não alertadas"],
                stack=False,
                height=340,
                use_container_width=True,
            )
            st.caption(
                "Cada barra conta municípios (n=9 por safra). O teste contém seis safras compartilhadas; "
                "as 54 linhas município-safra não são 54 anos independentes. "
                f"Custo dos erros: {5 * fn + fp} (5×FN+FP); sem 2024: {5 * fn_sem24 + fp_sem24} "
                f"(TN={tn_sem24}, FP={fp_sem24}, FN={fn_sem24}, TP={tp_sem24}). "
                "É uma avaliação retrospectiva, não garantia de desempenho em safras futuras."
            )

    st.markdown(
        f"""
        <div class='section-head'>
            {load_svg('history', svg_color_main, 22, 22)}
            <div>
                <h2 class='section-title'>Histórico de Análises Realizadas</h2>
                <p class='section-sub'>Registro das últimas inferências executadas no painel</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        with get_db_connection() as conn:
            df_prev = pd.read_sql_query(
                "SELECT ano_safra, modelo_utilizado, alerta_quebra, probabilidade_quebra, tempo_inferencia_ms, origem_execucao, data_previsao FROM previsoes_sistemicas ORDER BY id_previsao DESC LIMIT 30",
                conn,
            )
        if df_prev.empty:
            st.caption("Nenhuma previsão persistida até o momento. Utilize o botão 'Salvar Registro Desta Análise' na primeira aba.")
        else:
            df_prev.columns = ["Safra", "Modelo", "Alerta", "Probabilidade", "Tempo (ms)", "Origem", "Data/Hora"]
            st.dataframe(df_prev, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.error(f"Falha ao consultar banco local: {exc}")

# -----------------------------------------------------------------------------
# Aba 3 - Sobre o Assistente e Transparência
# -----------------------------------------------------------------------------
with aba_sistema:
    st.markdown(
        f"""
        <div class='section-head'>
            {load_svg('info', svg_color_main, 22, 22)}
            <div>
                <h2 class='section-title'>Como o SojaRisco Opera</h2>
                <p class='section-sub'>Metodologia simplificada para suporte diário ao produtor</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    passos = [
        ("01", "Captura de Dados Agroclimáticos", "O assistente monitora automaticamente dados diários de chuva, temperatura e déficit hídrico coletados por satélites da NASA e órgãos públicos.", "weather"),
        ("02", "Engenharia de Indicadores", "Transforma milhões de registros climáticos em variáveis agronômicas determinantes: dias de pico de calor e chuva no enchimento do grão.", "water"),
        ("03", "Inferência Probabilística", "A regressão logística padronizada avalia a temperatura máxima média de dez-fev; a probabilidade é um índice de risco, não uma probabilidade clínica calibrada.", "brain"),
        ("04", "Apoio à Tomada de Decisão", "Entrega uma probabilidade calibrada para orientar compras de insumos, manejo e proteção comercial de contratos futuros de grãos.", "shield"),
    ]
    for num, titulo, desc, icon in passos:
        svg_badge = load_svg(icon, svg_color_main, 24, 24)
        st.markdown(
            f"""
            <div class='panel' style='display:flex;gap:18px;align-items:flex-start;margin-bottom:12px;'>
                <div style='background:var(--bg-card-alt);border:1px solid var(--border-color);border-radius:12px;padding:12px;display:flex;align-items:center;justify-content:center;'>
                    {svg_badge}
                </div>
                <div>
                    <div style='font-weight:800;color:var(--text-title);font-size:16px;'>{num}. {titulo}</div>
                    <div style='font-size:14px;color:var(--text-body);margin-top:4px;line-height:1.55;'>{desc}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class='section-head'>
            {load_svg('shield', svg_color_main, 22, 22)}
            <div>
                <h2 class='section-title'>Acessibilidade & Diretrizes WCAG 2.1 AA</h2>
                <p class='section-sub'>Compromisso com usabilidade e ergonomia visual</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="notice">
            <strong>Conformidade WCAG 2.1 AA:</strong> Este aplicativo utiliza contraste mínimo de 4.5:1 para textos em ambos os modos (claro e escuro), 
            ícones vetoriais com suporte a leitores de tela e paletas com distinção clara para produtores com daltonismo (Deuteranopia/Protanopia).
        </div>
        """,
        unsafe_allow_html=True,
    )

    if mostrar_tecnico:
        st.markdown("#### Configurações do Sistema")
        st.json({
            "modo": status_modelo,
            "caminho_modelo": str(MODEL_PATH),
            "features_selecionadas": MODEL_FEATURES,
            "limiar_alerta": LIMIAR_ALERTA,
            "municipio": MUNICIPIO,
            "uf": UF,
            "tema_atual": "Dark" if is_dark else "Light",
        })

# -----------------------------------------------------------------------------
# Rodapé da Aplicação
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class='footer'>
        <span><strong>SojaRisco</strong> · Assistente inteligente de apoio à decisão agroclimática (Sorriso - MT)</span>
        <span>Acessibilidade WCAG 2.1 AA · Atualizado em {datetime.now().strftime('%d/%m/%Y')}</span>
    </div>
    """,
    unsafe_allow_html=True,
)
