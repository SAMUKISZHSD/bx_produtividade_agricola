"""SojaRisco - dashboard de apoio à decisão agroclimática.

O app carrega models/pipeline_final.joblib: regressão logística em tmax_enchimento.
O alerta dispara se o índice de risco for >= 0,45, o que equivale a tmax média de dez-fev >= 28,34 °C.
O Model Card classifica este pipeline como protótipo experimental, não aprovado para decisão operacional.
Acessibilidade: WCAG 2.1 AA (contraste de texto >= 4.5:1, semântica e suporte a tema claro/escuro).
"""

from __future__ import annotations

import base64
import html
import json
import logging
import os
import re
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
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
MODEL_DIR = BASE_DIR / "models"
ASSETS_DIR = BASE_DIR / "icons"
DATA_PROCESSED_PATH = PROCESSED_DIR / "dados_modelo_s4.csv"
MUNICIPIOS_PATH = INTERIM_DIR / "municipios_selecionados.csv"
MODEL_PATH = MODEL_DIR / "pipeline_final.joblib"
LIMIAR_PATH = MODEL_DIR / "limiar_congelado.json"
DB_PATH = DATA_DIR / "monitoramento_safra.db"
LOG_DIR = BASE_DIR / "logs"
LOG_PATH = LOG_DIR / "sojarisco.log"

APP_NAME = "SojaRisco"
DEFAULT_MUNICIPIO = os.getenv("SOJARISCO_MUNICIPIO", "Sorriso")
UF = os.getenv("SOJARISCO_UF", "MT")
LATITUDE_PADRAO = float(os.getenv("SOJARISCO_LATITUDE", "-12.668"))
LONGITUDE_PADRAO = float(os.getenv("SOJARISCO_LONGITUDE", "-55.723"))
FEATURE = "tmax_enchimento"
MODELO_NOME = "LogisticRegression L2 (C=1.0, class_weight=balanced)"
MODEL_FEATURES = {FEATURE: FEATURE}

COORDENADAS_MUNICIPIOS_FALLBACK: dict[str, dict[str, Any]] = {
    "Ipiranga do Norte": {"cod_municipio": "5104526", "lat": -12.017, "lon": -56.0587},
    "Itanhangá": {"cod_municipio": "5104542", "lat": -12.1404, "lon": -56.7549},
    "Lucas do Rio Verde": {"cod_municipio": "5105259", "lat": -13.0373, "lon": -56.1675},
    "Nobres": {"cod_municipio": "5105903", "lat": -14.377, "lon": -55.8125},
    "Nova Mutum": {"cod_municipio": "5106224", "lat": -13.6296, "lon": -56.1061},
    "Nova Ubiratã": {"cod_municipio": "5106240", "lat": -12.7925, "lon": -54.7164},
    "Santa Rita do Trivelato": {"cod_municipio": "5107768", "lat": -13.8337, "lon": -55.2936},
    "Sorriso": {"cod_municipio": "5107925", "lat": -12.668, "lon": -55.723},
    "Tapurah": {"cod_municipio": "5108006", "lat": -12.568, "lon": -56.5318},
}

def _ler_limiar() -> tuple[float, float]:
    cfg = json.loads(LIMIAR_PATH.read_text(encoding="utf-8"))
    return float(cfg["limiar_otimo"]), float(cfg["limiar_celsius"])

LIMIAR_ALERTA, LIMIAR_CELSIUS = _ler_limiar()

st.set_page_config(
    page_title="SojaRisco | Inteligência Agroclimática",
    page_icon=str(ASSETS_DIR / "soybean.svg") if (ASSETS_DIR / "soybean.svg").exists() else None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Helper para carregar e colorir SVGs com atributos a11y
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_svg(icon_name: str, color: str | None = None, width: int = 24, height: int = 24) -> str:
    """Lê um SVG da pasta icons, ajusta dimensões e atributos WCAG/a11y."""
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


@st.cache_data(show_spinner=False)
def load_logo_sidebar_svg() -> str:
    """Carrega o logo vetorial ajustado para alto contraste na sidebar escura."""
    svg_path = ASSETS_DIR / "sojarisco_logo.svg"
    if not svg_path.exists():
        return ""
    try:
        content = svg_path.read_text(encoding="utf-8").strip()
        # Preserva folhas (#2E7D32 / #81C784) e sol (#F9A825); ajusta texto e haste para fundo escuro
        content = content.replace('fill="#153D2B"', 'fill="#edf5ef"')
        content = content.replace('stroke="#153D2B"', 'stroke="#86efac"')
        content = re.sub(r'(<text\b[^>]*?)fill="#2E7D32"', r'\1fill="#86efac"', content)
        if "<svg " in content:
            content = content.replace(
                "<svg ",
                '<svg role="img" aria-label="Logo Oficial SojaRisco - Assistente Agroclimático" '
                'style="width:100%;height:auto;max-width:240px;display:block;" ',
                1,
            )
        return content
    except Exception:
        return ""


@st.cache_data(show_spinner=False)
def load_svg_data_uri(icon_name: str, color: str) -> str:
    """Retorna data URI base64 de um ícone SVG de icons/ colorido para uso em CSS."""
    svg_path = ASSETS_DIR / f"{icon_name}.svg"
    if not svg_path.exists():
        return ""
    try:
        content = svg_path.read_text(encoding="utf-8").replace('stroke="#153D2B"', f'stroke="{color}"')
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"
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
    svg_color_success = "#4ade80"
    svg_color_warn = "#fbbf24"
    svg_color_danger = "#f87171"
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
    svg_color_success = "#15803d"
    svg_color_warn = "#b45309"
    svg_color_danger = "#b91c1c"

svg_color_muted = "#a3b8ac" if is_dark else "#3d5045"
svg_color_brand = "#22c55e" if is_dark else "#1b5e39"
uri_tab1_idle = load_svg_data_uri("soybean", svg_color_muted)
uri_tab1_active = load_svg_data_uri("soybean", svg_color_brand)
uri_tab2_idle = load_svg_data_uri("chart_bar", svg_color_muted)
uri_tab2_active = load_svg_data_uri("chart_bar", svg_color_brand)
uri_tab3_idle = load_svg_data_uri("info", svg_color_muted)
uri_tab3_active = load_svg_data_uri("info", svg_color_brand)
uri_expander = load_svg_data_uri("field", svg_color_main)
uri_theme_btn = load_svg_data_uri("sun", "#ffffff")

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

    /* Cabeçalho nativo do Streamlit integrado ao tema */
    header[data-testid="stHeader"] {{
        background: var(--bg-app) !important;
        border-bottom: none !important;
    }}
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] svg {{
        color: var(--text-muted) !important;
        fill: currentColor;
    }}
    [data-testid="stDecoration"] {{
        background-image: none !important;
        background: var(--brand-green) !important;
        height: 2px !important;
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
    [data-testid="stWidgetLabel"] p {{
        color: var(--text-title) !important;
        font-weight: 600 !important;
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
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
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
    .sidebar-logo {{
        margin: 0 0 10px;
    }}
    .sidebar-tech-head {{
        display: flex;
        align-items: center;
        gap: 6px;
        color: var(--sidebar-text);
        font-weight: 700;
        font-size: 14px;
        margin-bottom: 6px;
    }}

    /* Selectboxes na sidebar e popovers de opções */
    [data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background-color: var(--sidebar-bg-alt) !important;
        border: 1px solid rgba(255,255,255,0.22) !important;
        border-radius: 8px !important;
        color: var(--sidebar-text) !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="select"] > div:hover,
    [data-testid="stSidebar"] [data-baseweb="select"] > div:focus-within {{
        border-color: rgba(255,255,255,0.45) !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="select"] span,
    [data-testid="stSidebar"] [data-baseweb="select"] div,
    [data-testid="stSidebar"] [data-baseweb="select"] input {{
        color: var(--sidebar-text) !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="select"] svg {{
        fill: var(--sidebar-text) !important;
        color: var(--sidebar-text) !important;
    }}
    [data-baseweb="popover"] > div,
    [data-testid="stSelectboxVirtualDropdown"],
    ul[role="listbox"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-body) !important;
    }}
    [data-testid="stSelectboxVirtualDropdown"] li[role="option"],
    ul[role="listbox"] li[role="option"] {{
        background-color: transparent !important;
        color: var(--text-body) !important;
    }}
    [data-testid="stSelectboxVirtualDropdown"] li[role="option"]:hover,
    [data-testid="stSelectboxVirtualDropdown"] li[aria-selected="true"],
    ul[role="listbox"] li[role="option"]:hover,
    ul[role="listbox"] li[aria-selected="true"] {{
        background-color: var(--bg-card-alt) !important;
        color: var(--text-title) !important;
        font-weight: 600 !important;
    }}

    /* Código na sidebar e área principal */
    [data-testid="stSidebar"] [data-testid="stCode"] pre {{
        background-color: var(--sidebar-bg-alt) !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        color: var(--sidebar-text) !important;
        border-radius: 8px !important;
    }}
    [data-testid="stCode"] pre {{
        background-color: var(--bg-card-alt) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-title) !important;
        border-radius: 10px !important;
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
    .stButton > button[kind="primary"] p,
    .stDownloadButton > button[kind="primary"] p {{
        color: var(--btn-pri-text) !important;
    }}
    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover {{
        background-color: var(--brand-green-dark) !important;
        border-color: var(--brand-green-dark) !important;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }}
    .stButton > button[kind="primary"]:hover p,
    .stDownloadButton > button[kind="primary"]:hover p {{
        color: #ffffff !important;
    }}

    /* Botões secundários (área principal) */
    .stButton > button[kind="secondary"],
    .stDownloadButton > button[kind="secondary"] {{
        background-color: var(--btn-sec-bg) !important;
        color: var(--btn-sec-text) !important;
        border: 1px solid var(--btn-sec-border) !important;
    }}
    .stButton > button[kind="secondary"] p,
    .stDownloadButton > button[kind="secondary"] p {{
        color: var(--btn-sec-text) !important;
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
    [data-testid="stSidebar"] .stButton > button p,
    [data-testid="stSidebar"] .stDownloadButton > button p {{
        color: #ffffff !important;
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

    /* Controles nativos sem acento vermelho padrão do Streamlit (#ff4b4b) */
    [data-testid="stSlider"] [data-baseweb="slider"] > div > div {{
        background: var(--border-color) !important;
    }}
    [data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {{
        background-color: var(--brand-green) !important;
        border: 2px solid #ffffff !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.28) !important;
    }}
    [data-testid="stSlider"] [data-baseweb="slider"] [role="slider"]:focus-visible {{
        box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.35) !important;
    }}
    [data-testid="stSliderThumbValue"] {{
        color: var(--brand-green) !important;
        font-weight: 700 !important;
    }}
    [data-testid="stSliderTickBarMin"],
    [data-testid="stSliderTickBarMax"] {{
        color: var(--text-muted) !important;
    }}

    [data-baseweb="checkbox"] > span:first-of-type {{
        background-color: var(--bg-card) !important;
        border-color: var(--border-color) !important;
    }}
    [data-baseweb="checkbox"]:has(input:checked) > span:first-of-type {{
        background-color: var(--brand-green) !important;
        border-color: var(--brand-green) !important;
    }}
    [data-baseweb="checkbox"] > div:first-of-type {{
        background-color: var(--border-color) !important;
    }}
    [data-baseweb="checkbox"]:has(input:checked) > div:first-of-type {{
        background-color: var(--brand-green) !important;
    }}
    [data-baseweb="checkbox"] > div:first-of-type > div {{
        background-color: #ffffff !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="checkbox"] > div:first-of-type {{
        background-color: rgba(255,255,255,0.24) !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="checkbox"]:has(input:checked) > div:first-of-type {{
        background-color: #22c55e !important;
    }}

    /* Widgets nativos da área principal harmonizados com Light / Dark */
    [data-testid="stExpander"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 14px !important;
        box-shadow: var(--kpi-shadow);
        margin-top: 12px;
    }}
    [data-testid="stExpander"] summary {{
        background: var(--bg-card) !important;
        color: var(--text-title) !important;
        font-weight: 700 !important;
        border-radius: 14px !important;
    }}
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary svg {{
        color: var(--text-title) !important;
        fill: currentColor;
    }}
    [data-testid="stExpander"] summary:hover p,
    [data-testid="stExpander"] summary:hover svg {{
        color: var(--brand-green) !important;
    }}
    [data-testid="stExpanderDetails"] {{
        background: var(--bg-card) !important;
        color: var(--text-body) !important;
    }}

    [data-testid="stNumberInput"] [data-testid="stNumberInputContainer"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }}
    [data-testid="stNumberInput"] [data-testid="stNumberInputContainer"]:focus-within {{
        border-color: var(--brand-green) !important;
        box-shadow: 0 0 0 1px var(--brand-green) !important;
    }}
    [data-testid="stNumberInput"] input {{
        background: var(--bg-card) !important;
        color: var(--text-title) !important;
        -webkit-text-fill-color: var(--text-title) !important;
    }}
    [data-testid="stNumberInputStepDown"],
    [data-testid="stNumberInputStepUp"] {{
        background: var(--bg-card-alt) !important;
        color: var(--text-title) !important;
        border-color: var(--border-color) !important;
    }}
    [data-testid="stNumberInputStepDown"]:hover,
    [data-testid="stNumberInputStepUp"]:hover {{
        background: var(--brand-green) !important;
        color: #ffffff !important;
    }}

    [data-testid="stMetric"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 14px !important;
        padding: 16px 18px !important;
        box-shadow: var(--kpi-shadow);
    }}
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricLabel"] {{
        color: var(--text-muted) !important;
        font-weight: 700 !important;
        font-size: 13px !important;
    }}
    [data-testid="stMetricValue"] {{
        color: var(--text-title) !important;
        font-weight: 800 !important;
    }}

    [data-testid="stDataFrame"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        overflow: hidden;
    }}
    [data-testid="stJson"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 12px 14px !important;
    }}
    [data-testid="stCaptionContainer"] p {{
        color: var(--text-muted) !important;
    }}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
        color: var(--sidebar-muted) !important;
    }}
    [data-testid="stAlert"] {{
        background: var(--bg-card-alt) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-title) !important;
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
        margin: 4px 0 18px;
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
        color: #d1fae5 !important;
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
    .metric-unit {{
        font-size: 18px;
        font-weight: 600;
        color: var(--text-muted);
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
    .panel-header {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 15px;
        font-weight: 800;
        color: var(--text-title);
        margin-bottom: 4px;
    }}
    .panel-sub {{
        color: var(--text-muted);
        font-size: 13px;
        line-height: 1.45;
        margin: 0 0 14px;
    }}
    .obs-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 16px;
    }}
    .obs-item {{
        background: var(--bg-card-alt);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 12px 14px;
    }}
    .obs-label {{
        color: var(--text-muted);
        font-size: 11.5px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 4px;
    }}
    .obs-value {{
        color: var(--text-title);
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.5px;
        line-height: 1.15;
    }}
    .obs-unit {{
        font-size: 13px;
        font-weight: 600;
        color: var(--text-muted);
    }}
    .obs-badges {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding-top: 12px;
        border-top: 1px solid var(--border-color);
    }}

    .risk-card {{
        border-radius: 16px;
        padding: 24px 26px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        box-shadow: var(--kpi-shadow);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
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
    .risk-scale {{
        display: flex;
        justify-content: space-between;
        font-size: 13px;
        font-weight: 700;
        margin-top: 6px;
        color: var(--text-title);
    }}
    .risk-scale span {{
        color: var(--text-title);
    }}
    .risk-meta {{
        margin-top: 14px;
        padding-top: 10px;
        border-top: 1px solid var(--border-color);
        color: var(--text-muted);
        font-size: 12.5px;
        line-height: 1.4;
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
    .risk-high .progress-fill {{
        background: linear-gradient(90deg, var(--alert-warn), var(--alert-danger));
    }}
    .risk-low .progress-fill {{
        background: linear-gradient(90deg, #4ade80, #15803d);
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
        padding: 0 !important;
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
        padding: 5px 12px;
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
    .pill-neutral {{
        background: var(--bg-card-alt);
        color: var(--text-body);
    }}

    /* Avisos customizados alinhados à paleta (substitui banners padrão do Streamlit) */
    .notice,
    .notice-danger,
    .notice-info,
    .notice-success {{
        border-radius: 12px;
        padding: 13px 16px;
        color: var(--text-title);
        font-size: 14px;
        line-height: 1.55;
        display: flex;
        align-items: flex-start;
        gap: 11px;
        margin: 8px 0 14px;
    }}
    .notice {{
        background: var(--alert-warn-bg);
        border: 1px solid var(--alert-warn);
        border-left: 4px solid var(--alert-warn);
    }}
    .notice strong {{
        color: var(--alert-warn);
    }}
    .notice-danger {{
        background: var(--alert-danger-bg);
        border: 1px solid var(--alert-danger);
        border-left: 4px solid var(--alert-danger);
    }}
    .notice-danger strong {{
        color: var(--alert-danger);
    }}
    .notice-success {{
        background: var(--alert-success-bg);
        border: 1px solid var(--alert-success);
        border-left: 4px solid var(--alert-success);
    }}
    .notice-success strong {{
        color: var(--alert-success);
    }}
    .notice-info {{
        background: var(--bg-card-alt);
        border: 1px solid var(--border-color);
        border-left: 4px solid var(--brand-green);
    }}
    .notice-info strong {{
        color: var(--brand-green);
    }}
    .notice-body,
    .notice-body span {{
        color: var(--text-title);
    }}
    .notice code,
    .notice-danger code,
    .notice-info code,
    .notice-success code,
    .panel code {{
        background: rgba(128, 128, 128, 0.14);
        color: var(--text-title);
        padding: 1px 6px;
        border-radius: 5px;
        font-size: 0.9em;
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
    .footer span {{
        color: var(--text-muted);
    }}

    /* Abas nativas */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
        background-color: var(--brand-green) !important;
    }}
    [data-testid="stTabs"] [data-baseweb="tab-border"] {{
        background-color: var(--border-color) !important;
    }}
    div[data-testid="stTabs"] button {{
        font-weight: 700;
        font-size: 15px;
        color: var(--text-muted) !important;
    }}
    div[data-testid="stTabs"] button p {{
        color: inherit !important;
    }}
    div[data-testid="stTabs"] button[role="tab"] p {{
        display: inline-flex !important;
        align-items: center;
        gap: 7px;
    }}
    div[data-testid="stTabs"] button[role="tab"] p::before {{
        content: "";
        width: 17px;
        height: 17px;
        display: inline-block;
        flex-shrink: 0;
        background-repeat: no-repeat;
        background-position: center;
        background-size: contain;
    }}
    div[data-testid="stTabs"] button[role="tab"]:nth-of-type(1) p::before {{
        background-image: url("{uri_tab1_idle}");
    }}
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"]:nth-of-type(1) p::before {{
        background-image: url("{uri_tab1_active}");
    }}
    div[data-testid="stTabs"] button[role="tab"]:nth-of-type(2) p::before {{
        background-image: url("{uri_tab2_idle}");
    }}
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"]:nth-of-type(2) p::before {{
        background-image: url("{uri_tab2_active}");
    }}
    div[data-testid="stTabs"] button[role="tab"]:nth-of-type(3) p::before {{
        background-image: url("{uri_tab3_idle}");
    }}
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"]:nth-of-type(3) p::before {{
        background-image: url("{uri_tab3_active}");
    }}
    [data-testid="stExpander"] summary p {{
        display: inline-flex !important;
        align-items: center;
        gap: 8px;
    }}
    [data-testid="stExpander"] summary p::before {{
        content: "";
        width: 18px;
        height: 18px;
        display: inline-block;
        flex-shrink: 0;
        background: url("{uri_expander}") no-repeat center / contain;
    }}
    [data-testid="stSidebar"] .stButton > button p {{
        display: inline-flex !important;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }}
    [data-testid="stSidebar"] .stButton > button p::before {{
        content: "";
        width: 16px;
        height: 16px;
        display: inline-block;
        flex-shrink: 0;
        background: url("{uri_theme_btn}") no-repeat center / contain;
    }}
    div[data-testid="stTabs"] button:hover {{
        color: var(--text-title) !important;
    }}
    div[data-testid="stTabs"] button[aria-selected="true"] {{
        color: var(--brand-green) !important;
        border-bottom-color: var(--brand-green) !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def render_notice(
    body_html: str,
    variant: str = "warn",
    icon_name: str | None = None,
    extra_style: str = "",
) -> None:
    """Renderiza aviso temático acessível com a paleta oficial do projeto."""
    variant_cfg = {
        "warn": ("notice", "alert", svg_color_warn),
        "danger": ("notice-danger", "alert", svg_color_danger),
        "success": ("notice-success", "shield", svg_color_success),
        "info": ("notice-info", "info", svg_color_main),
    }
    css_class, default_icon, icon_color = variant_cfg.get(variant, variant_cfg["warn"])
    svg_html = load_svg(icon_name or default_icon, icon_color, 18, 18)
    icon_block = f"<span style='margin-top:2px;display:inline-flex;flex-shrink:0;'>{svg_html}</span>" if svg_html else ""
    style_attr = f" style='{extra_style}'" if extra_style else ""
    st.markdown(
        f"<div class='{css_class}'{style_attr}>{icon_block}<div class='notice-body'>{body_html}</div></div>",
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


def salvar_previsao(
    ano: int,
    municipio: str,
    alerta: int,
    prob: float,
    tempo_ms: float,
    modelo: str,
    payload: dict[str, Any],
    origem: str,
) -> None:
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.execute(
                """INSERT INTO previsoes_sistemicas
                (ano_safra, municipio, modelo_utilizado, alerta_quebra, probabilidade_quebra,
                 limiar_decisao, limiar_celsius, tempo_inferencia_ms, origem_execucao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ano, municipio, modelo, alerta, prob, LIMIAR_ALERTA, LIMIAR_CELSIUS, tempo_ms, origem),
            )
            conn.execute(
                "INSERT INTO logs_monitoramento (id_previsao,nivel_log,mensagem,payload_entrada) VALUES (?,?,?,?)",
                (
                    cur.lastrowid,
                    "INFO",
                    f"Inferência registrada para {municipio} - safra {ano}",
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
    finally:
        conn.close()


_contagens_banco = inicializar_banco()

# -----------------------------------------------------------------------------
# Carregamento de Dados e Modelo
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def carregar_coordenadas_municipios() -> dict[str, dict[str, Any]]:
    coords = {k: dict(v) for k, v in COORDENADAS_MUNICIPIOS_FALLBACK.items()}
    if MUNICIPIOS_PATH.exists():
        try:
            df_coords = pd.read_csv(MUNICIPIOS_PATH)
            if {"municipio", "lat", "lon"}.issubset(df_coords.columns):
                for _, row in df_coords.iterrows():
                    nome = str(row["municipio"]).strip()
                    if not nome:
                        continue
                    cod = row.get("cod_municipio", "")
                    cod_str = str(int(cod)) if pd.notna(cod) and str(cod).strip() else ""
                    coords[nome] = {
                        "cod_municipio": cod_str,
                        "lat": float(row["lat"]),
                        "lon": float(row["lon"]),
                    }
        except Exception:
            logging.exception("Falha ao ler municipios_selecionados.csv; usando coordenadas de fallback.")
    return coords


def obter_info_municipio(municipio: str, coords: dict[str, dict[str, Any]]) -> tuple[str, float, float]:
    info = coords.get(municipio) or coords.get(DEFAULT_MUNICIPIO)
    if info:
        return str(info.get("cod_municipio", "")), float(info["lat"]), float(info["lon"])
    return "5107925", LATITUDE_PADRAO, LONGITUDE_PADRAO


def _valor_numerico(row: pd.Series, col: str, fallback: float) -> float:
    val = row.get(col, fallback)
    if val is None or pd.isna(val):
        return float(fallback)
    return float(val)


def extrair_dados_safra(
    df: pd.DataFrame,
    municipio: str,
    ano: int,
    limiar_celsius: float = LIMIAR_CELSIUS,
) -> tuple[dict[str, float], Any, str]:
    defaults_base = {
        "tmax_enchimento": float(limiar_celsius),
        "chuva_enchimento": 0.0,
        "dias_calor_enchimento": 0.0,
        "veranico_enchimento": 0.0,
        "gwet_enchimento": 0.0,
        "amplitude_termica": 0.0,
    }
    if df.empty or "ano_safra" not in df.columns:
        return defaults_base, None, "N/A"

    mask = pd.to_numeric(df["ano_safra"], errors="coerce") == int(ano)
    if "municipio" in df.columns:
        mask = mask & (df["municipio"].astype(str) == str(municipio))
    linha = df.loc[mask]
    if linha.empty:
        return defaults_base, None, "N/A"

    r = linha.iloc[0]
    defaults = {
        "tmax_enchimento": _valor_numerico(r, "tmax_enchimento", limiar_celsius),
        "chuva_enchimento": _valor_numerico(r, "chuva_enchimento", 0.0),
        "dias_calor_enchimento": _valor_numerico(r, "dias_calor_enchimento", 0.0),
        "veranico_enchimento": _valor_numerico(r, "veranico_enchimento", 0.0),
        "gwet_enchimento": _valor_numerico(r, "gwet_enchimento", 0.0),
        "amplitude_termica": _valor_numerico(r, "amplitude_termica", 0.0),
    }
    quebra_observada = r.get("quebra_safra", None)
    split_val = r.get("split", "N/A")
    split_safra = str(split_val) if split_val is not None and pd.notna(split_val) else "N/A"
    return defaults, quebra_observada, split_safra


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
def consultar_nasa_power(ano: int, lat: float, lon: float) -> dict[str, Any]:
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "PRECTOTCORR,T2M_MAX,T2M_MIN",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
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
        "latitude": lat,
        "longitude": lon,
        "fonte": "NASA POWER Daily API",
    }


@st.cache_data(ttl=3600, show_spinner=False)
def dados_demo() -> pd.DataFrame:
    anos = np.arange(2015, 2025)
    splits = ["treino"] * 4 + ["teste"] * 6
    return pd.DataFrame({
        "municipio": [DEFAULT_MUNICIPIO] * len(anos),
        "ano_safra": anos,
        "split": splits,
        "tmax_enchimento": np.array([29.52, 31.69, 27.85, 27.68, 29.04, 29.62, 31.42, 27.53, 27.54, 31.19]),
        "chuva_enchimento": np.array([429.7, 408.2, 654.2, 973.3, 547.6, 501.2, 546.8, 823.6, 757.8, 692.7]),
        "dias_calor_enchimento": np.array([0.0, 14.0, 0.0, 0.0, 0.0, 0.0, 9.0, 0.0, 0.0, 18.0]),
        "veranico_enchimento": np.array([7.0, 7.0, 3.0, 5.0, 7.0, 2.0, 5.0, 5.0, 1.0, 5.0]),
        "gwet_enchimento": np.array([0.699, 0.682, 0.759, 0.835, 0.719, 0.703, 0.676, 0.836, 0.794, 0.717]),
        "amplitude_termica": np.array([21.45, 26.01, 20.52, 22.51, 22.28, 21.17, 22.81, 22.13, 23.33, 20.64]),
        "quebra_safra": [0, 1, 0, 0, 0, 0, 1, 0, 0, 1],
    })


df_historico = carregar_historico()
coords_municipios = carregar_coordenadas_municipios()
modelo, status_modelo, mensagem_modelo = carregar_modelo()
if df_historico.empty:
    df_visual = dados_demo()
    origem_dados = "DEMONSTRAÇÃO - dados ilustrativos"
else:
    df_visual = df_historico.copy()
    origem_dados = "Dados processados do projeto"


def executar_predicao(features: dict[str, float], modo_simulacao: bool = False):
    inicio = time.perf_counter()
    tmax = float(features.get(FEATURE, LIMIAR_CELSIUS))
    if modelo is not None and status_modelo == "REAL" and not modo_simulacao:
        X = pd.DataFrame({FEATURE: [tmax]})
        probas = modelo.predict_proba(X)[0]
        classes = list(getattr(modelo, "classes_", [0, 1]))
        if 1 not in classes:
            raise ValueError("A classe positiva 1 não foi encontrada em model.classes_.")
        prob = float(np.clip(float(probas[classes.index(1)]), 0.0, 1.0))
        nome = modelo.__class__.__name__
        tipo = "REAL"
    else:
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
    # Logo vetorial oficial ajustado para contraste em fundo escuro
    logo_sidebar_svg = load_logo_sidebar_svg()
    if logo_sidebar_svg:
        st.markdown(f"<div class='sidebar-logo'>{logo_sidebar_svg}</div>", unsafe_allow_html=True)
    else:
        st.markdown("### SojaRisco")

    sidebar_loc_placeholder = st.empty()
    st.caption("Assistente experimental de apoio à decisão agroclimática")

    st.divider()

    # Alternância de Modo Claro / Modo Escuro (WCAG AA)
    btn_theme_label = "Modo Claro" if is_dark else "Modo Escuro"
    if st.button(btn_theme_label, key="theme_toggle", use_container_width=True):
        st.session_state["dark_mode"] = not is_dark
        st.rerun()

    st.divider()
    if "municipio" in df_visual.columns:
        municipios_disponiveis = sorted(
            df_visual["municipio"].dropna().astype(str).unique().tolist()
        )
    else:
        municipios_disponiveis = [DEFAULT_MUNICIPIO]
    if not municipios_disponiveis:
        municipios_disponiveis = [DEFAULT_MUNICIPIO]
    idx_mun_padrao = (
        municipios_disponiveis.index(DEFAULT_MUNICIPIO)
        if DEFAULT_MUNICIPIO in municipios_disponiveis
        else 0
    )
    municipio_selecionado = st.selectbox(
        "Município",
        municipios_disponiveis,
        index=idx_mun_padrao,
    )
    cod_mun, lat_mun, lon_mun = obter_info_municipio(municipio_selecionado, coords_municipios)

    if "municipio" in df_visual.columns:
        df_mun = df_visual[df_visual["municipio"].astype(str) == municipio_selecionado].copy()
    else:
        df_mun = df_visual.copy()
    if df_mun.empty:
        df_mun = df_visual.copy()
    if "ano_safra" in df_mun.columns:
        df_mun = df_mun.sort_values("ano_safra").reset_index(drop=True)

    anos_disponiveis = sorted(
        pd.to_numeric(df_mun.get("ano_safra", pd.Series([2024])), errors="coerce")
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )
    if not anos_disponiveis:
        anos_disponiveis = [2024]
    ano_atual = st.selectbox("Safra de referência", anos_disponiveis, index=len(anos_disponiveis) - 1)
    sidebar_loc_placeholder.markdown(f"**{municipio_selecionado} - {UF}** ({lat_mun:.3f}, {lon_mun:.3f})")

    mostrar_tecnico = st.toggle("Exibir detalhes técnicos de ML", value=False)

    st.divider()
    if status_modelo == "REAL":
        pill_status_cls = "pill"
        pill_status_icon = load_svg("shield", svg_color_success, 14, 14)
    elif status_modelo == "DEMONSTRAÇÃO":
        pill_status_cls = "pill pill-warn"
        pill_status_icon = load_svg("alert", svg_color_warn, 14, 14)
    else:
        pill_status_cls = "pill pill-danger"
        pill_status_icon = load_svg("alert", svg_color_danger, 14, 14)
    st.markdown(
        f"<div class='{pill_status_cls}' style='margin-bottom:8px;'>{pill_status_icon} Motor: {status_modelo}</div>",
        unsafe_allow_html=True,
    )
    if status_modelo == "REAL":
        st.caption("Pipeline experimental (LogisticRegression L2) ativo e integrado ao SQLite.")
    else:
        st.caption("Operando em modo de simulação até a integração do artefato pipeline_final.joblib.")
    if mostrar_tecnico:
        st.markdown("---")
        st.markdown(
            f"<div class='sidebar-tech-head'>{load_svg('settings', '#b0c7b8', 16, 16)} Parâmetros do sistema</div>",
            unsafe_allow_html=True,
        )
        st.code(
            f"Artefato: {MODEL_PATH.name}\n"
            f"Município: {municipio_selecionado} ({cod_mun})\n"
            f"Coords: {lat_mun:.4f}, {lon_mun:.4f}\n"
            f"Limiar: {LIMIAR_ALERTA:.0%} (≥ {LIMIAR_CELSIUS:.2f} °C)\n"
            f"Base: {origem_dados}",
            language="text",
        )
        st.caption(mensagem_modelo)

    st.markdown("---")
    st.caption("Protótipo experimental. Não aprovado para decisão operacional isolada (crédito, seguro ou manejo).")

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
<div class="hero-kicker">{icon_shield} PAINEL EXPERIMENTAL DE RISCO TÉRMICO · {html.escape(municipio_selecionado.upper())} / {UF}</div>
<h1 class="hero-title">Monitoramento de risco por calor<br>no enchimento da soja.</h1>
<p class="hero-copy">Acompanhe o índice de risco térmico (dez–fev) e indicadores agroclimáticos contextuais para a soja em {html.escape(municipio_selecionado)}-{UF}, na microrregião do Alto Teles Pires.</p>
<div class="hero-meta">
<span>{icon_loc} {html.escape(municipio_selecionado)}, {UF} ({lat_mun:.3f}, {lon_mun:.3f})</span>
<span>{icon_soy} Soja em grão</span>
<span>{icon_cal} Safra {ano_atual}</span>
</div>
</div>
""",
    unsafe_allow_html=True,
)

render_notice(
    "<strong>Protótipo experimental (não aprovado para decisão operacional):</strong> "
    "o score exibido é um índice de risco térmico referente a dez–fev (<code>tmax_enchimento</code>), "
    "não uma probabilidade calibrada de quebra; perdas por excesso de chuva, pragas ou doenças não são detectadas.",
    variant="warn",
    icon_name="alert",
)

if status_modelo == "DEMONSTRAÇÃO":
    render_notice(
        "<strong>Ambiente de demonstração:</strong> o pipeline de inferência real está indisponível. Os dados e alertas apresentados são ilustrativos para navegação.",
        variant="warn",
        icon_name="alert",
    )
elif status_modelo == "ERRO":
    render_notice(
        f"<strong>Falha ao carregar o modelo de predição:</strong> {html.escape(str(mensagem_modelo))}",
        variant="danger",
        icon_name="alert",
    )

# Abas
tab_title_1 = "Visão da safra"
tab_title_2 = "Histórico e desempenho"
tab_title_3 = "Sobre o assistente"

aba_previsao, aba_historico, aba_sistema = st.tabs([tab_title_1, tab_title_2, tab_title_3])

# -----------------------------------------------------------------------------
# Aba 1 - Visão da Safra (Experiência do Produtor com Assets Vetoriais)
# -----------------------------------------------------------------------------
with aba_previsao:
    defaults, quebra_observada, split_safra = extrair_dados_safra(
        df_visual, municipio_selecionado, ano_atual, LIMIAR_CELSIUS
    )

    alerta, prob, tempo_ms, nome_modelo, tipo_predicao = executar_predicao(defaults)
    risco_texto = "Alerta: risco elevado por calor" if alerta else "Sem alerta térmico pelo limiar"
    risco_classe = "risk-high" if alerta else "risk-low"
    risco_descricao = (
        f"A temperatura máxima média no enchimento de grãos (dez–fev) em {municipio_selecionado} atingiu "
        f"{defaults['tmax_enchimento']:.2f} °C, igual ou superior ao corte de referência ({LIMIAR_CELSIUS:.2f} °C). "
        "Trata-se de um índice experimental de risco por calor; quebras por excesso de chuva, pragas ou doenças não entram no cálculo."
        if alerta else
        f"A temperatura máxima média no enchimento de grãos (dez–fev) em {municipio_selecionado} foi de "
        f"{defaults['tmax_enchimento']:.2f} °C, abaixo do corte térmico de {LIMIAR_CELSIUS:.2f} °C. "
        "Um alerta negativo não garante ausência de quebra por excesso de chuva, pragas ou doenças."
    )

    # Cards de Métricas com Ícones SVG
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        icon_brain = load_svg("brain", svg_color_main, 24, 24)
        st.markdown(
            f"""
<div class='metric-card'>
<div class='metric-header'>
<span class='metric-label'>Índice de Risco</span>
{icon_brain}
</div>
<div class='metric-value'>{prob:.0%}</div>
<div class='metric-foot'>Limiar de alerta: {LIMIAR_ALERTA:.0%} (≥ {LIMIAR_CELSIUS:.2f} °C)</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with c2:
        icon_therm = load_svg("thermometer", svg_color_main, 24, 24)
        st.markdown(
            f"""
<div class='metric-card'>
<div class='metric-header'>
<span class='metric-label'>Tmax no Enchimento</span>
{icon_therm}
</div>
<div class='metric-value'>{defaults['tmax_enchimento']:.2f} <span class='metric-unit'>°C</span></div>
<div class='metric-foot'>Variável única do modelo (dez–fev)</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with c3:
        icon_rain = load_svg("rain", svg_color_main, 24, 24)
        st.markdown(
            f"""
<div class='metric-card'>
<div class='metric-header'>
<span class='metric-label'>Chuva no Enchimento</span>
{icon_rain}
</div>
<div class='metric-value'>{defaults['chuva_enchimento']:.0f} <span class='metric-unit'>mm</span></div>
<div class='metric-foot'>Precipitação acumulada dez–fev (contextual)</div>
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
<p class='section-sub'>Leitura do índice de risco térmico (dez–fev) e indicadores contextuais observados</p>
</div>
</div>
""",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.2, 1], gap="medium")
    with left:
        icon_alert = load_svg(
            "alert" if alerta else "shield",
            svg_color_danger if alerta else svg_color_success,
            20,
            20,
        )
        st.markdown(
            f"""
<div class='risk-card {risco_classe}'>
<div>
<div class='risk-label'>{icon_alert} Diagnóstico do Assistente · {html.escape(tipo_predicao)}</div>
<h3 class='risk-title'>{html.escape(risco_texto)}</h3>
<div class='risk-description'>{html.escape(risco_descricao)}</div>
<div class='progress-track'>
<div class='progress-fill' style='width:{prob*100:.1f}%;'></div>
</div>
<div class='risk-scale'>
<span>Índice de risco (não calibrado)</span>
<span>{prob:.1%}</span>
</div>
</div>
<div class='risk-meta'>Motor: {html.escape(nome_modelo)} · Inferência: {tempo_ms:.3f} ms · Município: {html.escape(municipio_selecionado)}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with right:
        rotulo_split = (
            "Treino (2001–2018)" if split_safra == "treino"
            else ("Teste temporal (2019–2024)" if split_safra == "teste" else split_safra)
        )
        if quebra_observada is not None and pd.notna(quebra_observada):
            if int(quebra_observada) == 1:
                badge_quebra = (
                    f"<span class='pill pill-danger'>"
                    f"{load_svg('alert', svg_color_danger, 14, 14)} "
                    "IBGE PAM: Quebra severa (1)</span>"
                )
            else:
                badge_quebra = (
                    f"<span class='pill'>"
                    f"{load_svg('shield', svg_color_success, 14, 14)} "
                    "IBGE PAM: Sem quebra (0)</span>"
                )
        else:
            badge_quebra = "<span class='pill pill-neutral'>IBGE PAM: Sem registro</span>"

        obs_html = (
            "<div class='panel' style='height:100%;'>"
            f"<div class='panel-header'>{load_svg('thermometer', svg_color_main, 18, 18)} "
            "<span>Condições Observadas</span></div>"
            "<p class='panel-sub'>Indicadores contextuais (NASA POWER). "
            "Somente <code>tmax_enchimento</code> entra no modelo ativo.</p>"
            "<div class='obs-grid'>"
            "<div class='obs-item'>"
            "<div class='obs-label'>Dias de calor (≥ 35 °C)</div>"
            f"<div class='obs-value'>{defaults['dias_calor_enchimento']:.0f} <span class='obs-unit'>dias</span></div>"
            "</div>"
            "<div class='obs-item'>"
            "<div class='obs-label'>Maior veranico (&lt; 1 mm)</div>"
            f"<div class='obs-value'>{defaults['veranico_enchimento']:.0f} <span class='obs-unit'>dias</span></div>"
            "</div>"
            "<div class='obs-item'>"
            "<div class='obs-label'>Umidade do solo (GWET)</div>"
            f"<div class='obs-value'>{defaults['gwet_enchimento']:.2f}</div>"
            "</div>"
            "<div class='obs-item'>"
            "<div class='obs-label'>Amplitude térmica</div>"
            f"<div class='obs-value'>{defaults['amplitude_termica']:.1f} <span class='obs-unit'>°C</span></div>"
            "</div>"
            "</div>"
            "<div class='obs-badges'>"
            f"<span class='pill pill-neutral'>Divisão: {html.escape(rotulo_split)}</span>"
            f"{badge_quebra}"
            "</div>"
            "</div>"
        )
        st.markdown(obs_html, unsafe_allow_html=True)

    # Evolução Agroclimática
    st.markdown(
        f"""
<div class='section-head'>
{load_svg('chart_line', svg_color_main, 22, 22)}
<div>
<h2 class='section-title'>Evolução Histórica dos Indicadores · {html.escape(municipio_selecionado)} - {UF}</h2>
<p class='section-sub'>Temperatura máxima média no enchimento (variável do modelo) frente ao limiar de {LIMIAR_CELSIUS:.2f} °C e chuva acumulada contextual</p>
</div>
</div>
""",
        unsafe_allow_html=True,
    )
    if not df_mun.empty and "ano_safra" in df_mun.columns and "tmax_enchimento" in df_mun.columns:
        df_plot = df_mun.sort_values("ano_safra").copy()
        df_plot["Safra"] = pd.to_numeric(df_plot["ano_safra"], errors="coerce").astype(int).astype(str)
        df_plot = df_plot.set_index("Safra")

        g1, g2 = st.columns(2, gap="medium")
        with g1:
            limiar_label = f"Limiar ({LIMIAR_CELSIUS:.2f} °C)".replace(".", ",")
            st.caption(f"Tmax média no enchimento (dez–fev) vs. {limiar_label}")
            chart_tmax = pd.DataFrame(
                {
                    "Tmax Enchimento (°C)": pd.to_numeric(df_plot["tmax_enchimento"], errors="coerce"),
                    limiar_label: LIMIAR_CELSIUS,
                },
                index=df_plot.index,
            )
            tmax_colors = ["#4ade80", "#fbbf24"] if is_dark else ["#1b5e39", "#b45309"]
            st.line_chart(chart_tmax, color=tmax_colors, height=260, use_container_width=True)
        with g2:
            if "chuva_enchimento" in df_plot.columns:
                st.caption("Chuva acumulada no enchimento (dez–fev · contextual)")
                chart_chuva = pd.DataFrame(
                    {"Chuva Enchimento (mm)": pd.to_numeric(df_plot["chuva_enchimento"], errors="coerce")},
                    index=df_plot.index,
                )
                chuva_colors = ["#22c55e"] if is_dark else ["#2e8b57"]
                st.bar_chart(chart_chuva, color=chuva_colors, height=260, use_container_width=True)

    # Simulador de Cenários isolado com @st.fragment para performance
    @st.fragment
    def render_simulador_cenarios(defaults_sim: dict[str, float]) -> None:
        with st.expander("Explorar cenários na fazenda — Simulador Agroclimático", expanded=False):
            render_notice(
                "Altere a temperatura máxima média de dezembro a fevereiro (<code>tmax_enchimento</code>) "
                "para calcular o índice de risco experimental (não calibrado) do modelo.",
                variant="info",
                icon_name="info",
            )
            sc1, sc2 = st.columns(2)
            with sc1:
                sim_tmax = st.slider("Temperatura máxima média no enchimento (°C)", 20.0, 35.0, float(defaults_sim.get("tmax_enchimento", LIMIAR_CELSIUS)), 0.1)
            with sc2:
                st.metric("Limiar de alerta (corte térmico)", f"{LIMIAR_CELSIUS:.2f} °C", help=f"Corresponde ao índice de risco {LIMIAR_ALERTA:.0%}")

            if st.button("Calcular Risco do Cenário", type="primary", use_container_width=True):
                sim_features = {
                    "tmax_enchimento": sim_tmax,
                }
                sim_alerta, sim_prob, sim_ms, sim_nome, sim_tipo = executar_predicao(sim_features, modo_simulacao=False)
                st.session_state["ultimo_cenario"] = {"alerta": sim_alerta, "prob": sim_prob, "features": sim_features}

            if "ultimo_cenario" in st.session_state:
                cenario = st.session_state["ultimo_cenario"]
                nivel = "ALERTA de risco por calor" if cenario["alerta"] else "Sem alerta térmico pelo limiar"
                render_notice(
                    f"<strong>Resultado do cenário:</strong> índice de risco de <strong>{cenario['prob']:.1%}</strong> "
                    f"(não calibrado) — {nivel}.",
                    variant="danger" if cenario["alerta"] else "success",
                    icon_name="alert" if cenario["alerta"] else "shield",
                )

    render_simulador_cenarios(defaults)

    # Consulta de Clima na NASA POWER isolada com @st.fragment
    @st.fragment
    def render_consulta_nasa(ano_padrao: int, municipio_api: str, lat_api: float, lon_api: float) -> None:
        st.markdown(
            f"""
<div class='section-head'>
{load_svg('weather', svg_color_main, 22, 22)}
<div>
<h2 class='section-title'>Consulta de Dados Agrometeorológicos Reais</h2>
<p class='section-sub'>Conexão direta com a API pública da NASA POWER para {html.escape(municipio_api)}-{UF} ({lat_api:.3f}, {lon_api:.3f})</p>
</div>
</div>
""",
            unsafe_allow_html=True,
        )
        api_col, api_info = st.columns([1, 2], gap="medium", vertical_alignment="bottom")
        with api_col:
            ano_api = st.number_input("Ano da consulta", min_value=1985, max_value=date.today().year, value=ano_padrao, step=1)
            consultar = st.button("Consultar NASA POWER", use_container_width=True)
        with api_info:
            render_notice(
                f"<strong>Fonte Oficial:</strong> A consulta recupera a série histórica diária medida por satélite e reanálise meteorológica "
                f"para as coordenadas de <strong>{html.escape(municipio_api)}-{UF}</strong> ({lat_api:.4f}, {lon_api:.4f}).",
                variant="info",
                icon_name="info",
                extra_style="min-height: 98px; align-items: center; margin: 0;",
            )

        if consultar:
            try:
                with st.spinner("Buscando dados agrometeorológicos na NASA POWER..."):
                    dados_api = consultar_nasa_power(int(ano_api), lat_api, lon_api)
                render_notice(
                    f"<strong>Dados recebidos:</strong> série agroclimática de {html.escape(municipio_api)}-{UF} carregada da NASA POWER.",
                    variant="success",
                    icon_name="shield",
                )
                api1, api2, api3 = st.columns(3)
                with api1:
                    st.metric("Chuva anual acumulada", f"{dados_api['precipitacao_anual_mm']:.0f} mm")
                with api2:
                    st.metric("Temperatura máxima média", f"{dados_api['temperatura_max_media_c']:.1f} °C")
                with api3:
                    st.metric("Dias com calor ≥ 35 °C", f"{dados_api['dias_calor_35c']} dias")
                st.caption(f"Fonte: {dados_api['fonte']} · Município: {municipio_api}-{UF} ({lat_api:.4f}, {lon_api:.4f}) · Período: {dados_api['periodo']}")
            except Exception as exc:
                logging.exception("Erro ao consultar NASA POWER")
                render_notice(
                    f"<strong>Erro na consulta:</strong> não foi possível conectar com a API da NASA POWER ({html.escape(str(exc))}).",
                    variant="danger",
                    icon_name="alert",
                )

    render_consulta_nasa(ano_atual, municipio_selecionado, lat_mun, lon_mun)

    # Registro de Histórico isolado com @st.fragment
    @st.fragment
    def render_salvar_registro(
        ano_salvar: int,
        municipio_salvar: str,
        alerta_salvar: int,
        prob_salvar: float,
        tempo_salvar: float,
        modelo_salvar: str,
        defaults_salvar: dict[str, float],
    ) -> None:
        st.markdown("---")
        if st.button("Salvar Registro Desta Análise"):
            try:
                payload_salvar = {"municipio": municipio_salvar, **defaults_salvar}
                salvar_previsao(
                    ano_salvar,
                    municipio_salvar,
                    alerta_salvar,
                    prob_salvar,
                    tempo_salvar,
                    modelo_salvar,
                    payload_salvar,
                    "dashboard",
                )
                render_notice(
                    f"<strong>Registro salvo:</strong> análise de {html.escape(municipio_salvar)} ({ano_salvar}) persistida no banco local.",
                    variant="success",
                    icon_name="shield",
                )
            except Exception as exc:
                render_notice(
                    f"<strong>Erro ao salvar:</strong> não foi possível registrar a previsão ({html.escape(str(exc))}).",
                    variant="danger",
                    icon_name="alert",
                )

    render_salvar_registro(ano_atual, municipio_selecionado, alerta, prob, tempo_ms, nome_modelo, defaults)

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
        apenas_mun = st.checkbox(f"Filtrar apenas {municipio_selecionado}", value=False, key="aba2_filtrar_mun")
        df_base_tab = df_mun if apenas_mun else df_historico
        cols_ordem = [
            "municipio",
            "ano_safra",
            "split",
            "tmax_enchimento",
            "chuva_enchimento",
            "dias_calor_enchimento",
            "veranico_enchimento",
            "gwet_enchimento",
            "amplitude_termica",
            "quebra_safra",
        ]
        cols = [c for c in cols_ordem if c in df_base_tab.columns]
        sort_cols = [c for c in ["ano_safra", "municipio"] if c in cols]
        sort_asc = [c != "ano_safra" for c in sort_cols]
        df_display = df_base_tab[cols].sort_values(sort_cols, ascending=sort_asc).copy() if sort_cols else df_base_tab[cols].copy()
        nomes_colunas = {
            "municipio": "Município",
            "ano_safra": "Safra",
            "split": "Divisão",
            "tmax_enchimento": "Tmax Enchimento (°C)",
            "chuva_enchimento": "Chuva Enchimento (mm)",
            "dias_calor_enchimento": "Dias de Calor (≥ 35 °C)",
            "veranico_enchimento": "Veranico Máx. (dias)",
            "gwet_enchimento": "Umidade Solo (GWET)",
            "amplitude_termica": "Amplitude Térmica (°C)",
            "quebra_safra": "Quebra Observada",
        }
        df_display = df_display.rename(columns=nomes_colunas)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        render_notice(
            "Nenhum dado processado encontrado em <code>data/processed/dados_modelo_s4.csv</code>. "
            "A visualização demonstrativa utiliza valores de referência.",
            variant="info",
            icon_name="info",
        )

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
        render_notice(
            "O gráfico de desempenho requer o pipeline serializado carregado; nenhum resultado demonstrativo será apresentado como métrica real.",
            variant="warn",
            icon_name="alert",
        )
    elif faltantes_avaliacao:
        render_notice(
            f"<strong>Base incompleta:</strong> faltam colunas na base histórica ({html.escape(str(sorted(faltantes_avaliacao)))}).",
            variant="danger",
            icon_name="alert",
        )
    else:
        dados_teste = df_historico.loc[df_historico["split"].eq("teste")].copy()
        if dados_teste.empty:
            render_notice(
                "A base não contém linhas do teste temporal congelado.",
                variant="warn",
                icon_name="alert",
            )
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
            bar_cols = [
                "Quebras observadas",
                "Quebras alertadas corretamente",
                "Falsos alarmes",
                "Quebras não alertadas",
            ]
            bar_colors = (
                ["#d8e5dc", "#4ade80", "#fbbf24", "#f87171"]
                if is_dark
                else ["#153d2b", "#15803d", "#b45309", "#b91c1c"]
            )
            st.bar_chart(
                grafico_safras,
                x="Safra",
                y=bar_cols,
                color=bar_colors,
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
        conn = get_db_connection()
        try:
            df_prev = pd.read_sql_query(
                "SELECT municipio, ano_safra, modelo_utilizado, alerta_quebra, probabilidade_quebra, tempo_inferencia_ms, origem_execucao, data_previsao FROM previsoes_sistemicas ORDER BY id_previsao DESC LIMIT 30",
                conn,
            )
        finally:
            conn.close()
        if df_prev.empty:
            st.caption("Nenhuma previsão persistida até o momento. Utilize o botão 'Salvar Registro Desta Análise' na primeira aba.")
        else:
            df_prev.columns = ["Município", "Safra", "Modelo", "Alerta", "Índice de Risco", "Tempo (ms)", "Origem", "Data/Hora"]
            st.dataframe(df_prev, use_container_width=True, hide_index=True)
    except Exception as exc:
        render_notice(
            f"<strong>Falha ao consultar banco local:</strong> {html.escape(str(exc))}",
            variant="danger",
            icon_name="alert",
        )

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
<p class='section-sub'>Metodologia do protótipo experimental conforme o Model Card</p>
</div>
</div>
""",
        unsafe_allow_html=True,
    )
    passos = [
        ("01", "Captura de Dados Oficiais", "Integra séries meteorológicas diárias da NASA POWER e produtividades anuais oficiais do IBGE/PAM para nove municípios do Alto Teles Pires (MT).", "weather"),
        ("02", "Variável do Modelo e Indicadores Contextuais", "Calcula a temperatura máxima média de dezembro a fevereiro (tmax_enchimento), única entrada do modelo ativo. Chuva, veranico, umidade do solo e dias ≥ 35 °C são exibidos apenas como contexto.", "water"),
        ("03", "Cálculo do Índice de Risco", "A regressão logística L2 (C=1.0, class_weight=\"balanced\") padroniza tmax_enchimento e gera um índice de risco por calor (não é uma probabilidade calibrada de quebra); o alerta dispara a partir de 0,45 (≥ 28,34 °C).", "brain"),
        ("04", "Uso Pretendido e Limitações (Março)", "O alerta é emitido em março, após o fim do enchimento e antes da colheita — portanto não orienta manejo da lavoura. Protótipo experimental não aprovado para decisão operacional; não detecta quebras por excesso de chuva ou doenças e não deve ser usado isoladamente para crédito, seguro ou decisões comerciais.", "shield"),
    ]
    for num, titulo, desc, icon in passos:
        svg_badge = load_svg(icon, svg_color_main, 24, 24)
        st.markdown(
            f"""
<div class='panel' style='display:flex;gap:18px;align-items:flex-start;margin-bottom:12px;'>
<div style='background:var(--bg-card-alt);border:1px solid var(--border-color);border-radius:12px;padding:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0;'>
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
    render_notice(
        "<strong>Conformidade WCAG 2.1 AA:</strong> este aplicativo utiliza contraste mínimo de 4.5:1 para textos em ambos os modos (claro e escuro), "
        "ícones vetoriais com suporte a leitores de tela e paletas com distinção clara para produtores com daltonismo (Deuteranopia/Protanopia).",
        variant="info",
        icon_name="shield",
    )

    if mostrar_tecnico:
        st.markdown("#### Configurações do Sistema")
        st.json({
            "modo": status_modelo,
            "status_card": "protótipo experimental (não aprovado para decisão operacional)",
            "caminho_modelo": str(MODEL_PATH),
            "features_selecionadas": MODEL_FEATURES,
            "limiar_alerta": LIMIAR_ALERTA,
            "limiar_celsius": LIMIAR_CELSIUS,
            "municipio": municipio_selecionado,
            "codigo_ibge": cod_mun,
            "latitude": lat_mun,
            "longitude": lon_mun,
            "uf": UF,
            "tema_atual": "Dark" if is_dark else "Light",
        })

# -----------------------------------------------------------------------------
# Rodapé da Aplicação
# -----------------------------------------------------------------------------
st.markdown(
    f"""
<div class='footer'>
<span><strong>SojaRisco</strong> · Protótipo experimental de apoio analítico agroclimático ({html.escape(municipio_selecionado)} - {UF})</span>
<span>Acessibilidade WCAG 2.1 AA · Atualizado em {datetime.now().strftime('%d/%m/%Y')}</span>
</div>
""",
    unsafe_allow_html=True,
)
