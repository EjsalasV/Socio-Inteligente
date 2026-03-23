"""
SocioAI - Interfaz Web con Streamlit.

Refactor incremental para convertir "Vista por area" en un workspace operativo
sin romper el flujo existente.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

# Add project root to sys.path so all internal modules
# are importable both locally and on Streamlit Cloud
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from analysis.lector_tb import leer_tb, obtener_resumen_tb, obtener_diagnostico_tb
from analysis.ranking_areas import calcular_ranking_areas, obtener_indicadores_clave
from analysis.variaciones import calcular_variaciones, resumen_variaciones
from analysis.expert_flags import detectar_expert_flags
from domain.services.leer_perfil import leer_perfil, obtener_datos_clave
from app.views.view_cliente import (
    render_sidebar_summary,
    render_area_header,
    render_area_kpis,
    render_por_que_importa,
)
from app.views.view_ranking import (
    render_contexto_tab,
    render_briefing_tab,
    render_procedimientos_tab,
    render_cobertura_tab,
    render_hallazgos_tab,
)
from app.views.view_area import (
    render_cierre_tab,
    render_decision_cierre_helper,
    render_seguimiento_tab,
    render_historial_tab,
    render_export_block,
)
from app.views.view_materialidad import render_calidad_tab
from app.views.view_chat import render_briefing_ia_tab, render_chat_tab

# Servicios opcionales (degradacion segura)
try:
    from domain.services.estado_area_yaml import (
        cargar_estado_area,
        guardar_estado_area,
        extraer_hallazgos_abiertos,
        obtener_pendientes_area,
        obtener_procedimientos_area,
    )
except Exception:
    cargar_estado_area = None
    guardar_estado_area = None
    extraer_hallazgos_abiertos = None
    obtener_pendientes_area = None
    obtener_procedimientos_area = None

try:
    from domain.services.cobertura_aseveraciones import evaluar_cobertura_aseveraciones
except Exception:
    evaluar_cobertura_aseveraciones = None

try:
    from domain.services.area_briefing import (
        construir_foco_auditoria,
        construir_foco_holding,
        construir_lectura_inicial,
        construir_resumen_area,
        top_cuentas_significativas,
    )
except Exception:
    construir_foco_auditoria = None
    construir_foco_holding = None
    construir_lectura_inicial = None
    construir_resumen_area = None
    top_cuentas_significativas = None

try:
    from domain.services.riesgos_area import detectar_riesgos_area
except Exception:
    detectar_riesgos_area = None

try:
    from domain.services.riesgos_automaticos_service import detectar_riesgos_area as detectar_riesgos_area_auto
except Exception:
    detectar_riesgos_area_auto = None

try:
    from domain.services.procedimientos_area import (
        procedimientos_por_area,
        procedimientos_por_area_estructurados,
    )
except Exception:
    procedimientos_por_area = None
    procedimientos_por_area_estructurados = None

try:
    from llm.cierre_area_llm import revisar_cierre_area_llm
except Exception:
    revisar_cierre_area_llm = None

try:
    from llm.chat_area_service import consultar_socio
except Exception:
    consultar_socio = None

try:
    from domain.catalogos_python.aseveraciones_ls import ASEVERACIONES_LS
except Exception:
    ASEVERACIONES_LS = {}

try:
    from domain.services.materialidad_service import calcular_materialidad
except Exception:
    calcular_materialidad = None

try:
    from domain.services.export_area_service import (
        build_area_resumen_markdown,
        build_area_cierre_markdown,
        save_area_markdown,
    )
except Exception:
    build_area_resumen_markdown = None
    build_area_cierre_markdown = None
    save_area_markdown = None

try:
    from domain.services.historial_area_service import (
        cargar_historial_area,
        agregar_evento_historial_area,
        resumir_historial_area,
    )
except Exception:
    cargar_historial_area = None
    agregar_evento_historial_area = None
    resumir_historial_area = None

try:
    from domain.services.metodologia_calidad_service import evaluar_alertas_metodologia
except Exception:
    evaluar_alertas_metodologia = None

try:
    from infra.repositories.catalogo_repository import obtener_area_por_codigo
except Exception:
    obtener_area_por_codigo = None

try:
    from analysis.lector_mayor import (
        mayor_existe,
        obtener_mayor_cliente,
        filtrar_por_ls,
        buscar_movimientos,
        resumen_mayor,
    )
except Exception:
    mayor_existe = None
    obtener_mayor_cliente = None
    filtrar_por_ls = None
    buscar_movimientos = None
    resumen_mayor = None

try:
    from llm.llm_client import _get_deepseek_key
except Exception:
    _get_deepseek_key = None

try:
    # Preferred remote persistence backend: Supabase
    from infra.repositories import supabase_repository as _sheets_repo
    guardar_cliente_sheets = getattr(
        _sheets_repo, "guardar_cliente_sheets", None
    )
    cargar_clientes_sheets = getattr(
        _sheets_repo, "cargar_clientes_sheets", None
    )
    eliminar_cliente_sheets = getattr(
        _sheets_repo, "eliminar_cliente_sheets", None
    )
    sheets_disponible = getattr(
        _sheets_repo, "sheets_disponible", None
    )
    obtener_ultimo_error_sheets = getattr(
        _sheets_repo, "obtener_ultimo_error_sheets", None
    )
    diagnosticar_sheets = getattr(
        _sheets_repo, "diagnosticar_sheets", None
    )
    diagnosticar_config_supabase = getattr(
        _sheets_repo, "diagnosticar_config_supabase", None
    )
    _sheets_ok = True
    _sheets_import_error = ""
except Exception:
    try:
        # Fallback legacy backend: Google Sheets
        from infra.repositories import sheets_repository as _sheets_repo
        guardar_cliente_sheets = getattr(
            _sheets_repo, "guardar_cliente_sheets", None
        )
        cargar_clientes_sheets = getattr(
            _sheets_repo, "cargar_clientes_sheets", None
        )
        eliminar_cliente_sheets = getattr(
            _sheets_repo, "eliminar_cliente_sheets", None
        )
        sheets_disponible = getattr(
            _sheets_repo, "sheets_disponible", None
        )
        obtener_ultimo_error_sheets = getattr(
            _sheets_repo, "obtener_ultimo_error_sheets", None
        )
        diagnosticar_sheets = getattr(
            _sheets_repo, "diagnosticar_sheets", None
        )
        diagnosticar_config_supabase = getattr(
            _sheets_repo, "diagnosticar_config_supabase", None
        )
        _sheets_ok = True
        _sheets_import_error = ""
    except Exception:
        guardar_cliente_sheets = None
        cargar_clientes_sheets = None
        eliminar_cliente_sheets = None
        sheets_disponible = None
        obtener_ultimo_error_sheets = None
        diagnosticar_sheets = None
        diagnosticar_config_supabase = None
        _sheets_ok = False
        _sheets_import_error = str(sys.exc_info()[1] or "")


@st.cache_data(ttl=300)
def cached_leer_tb(cliente: str):
    return leer_tb(cliente)


@st.cache_data(ttl=300)
def cached_ranking_areas(cliente: str):
    return calcular_ranking_areas(cliente)


@st.cache_data(ttl=300)
def cached_variaciones(cliente: str):
    return calcular_variaciones(cliente)


@st.cache_data(ttl=300)
def cached_resumen_tb(cliente: str):
    return obtener_resumen_tb(cliente)


@st.cache_data(ttl=300)
def cached_indicadores(cliente: str):
    return obtener_indicadores_clave(cliente)


@st.cache_data(ttl=300)
def cached_leer_perfil(cliente: str):
    return leer_perfil(cliente)


@st.cache_data(ttl=300)
def cached_datos_clave(cliente: str):
    return obtener_datos_clave(cliente)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# Configuracion
# ============================================================
st.set_page_config(
    page_title="SocioAI - Auditoria Inteligente",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  /* ── Global ── */
  html, body, [class*="css"] {
      font-family: 'Segoe UI', Arial, sans-serif;
      color: #172B4D;
  }
  .main { background-color: #FFFFFF; }
  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #003366 0%, #0066CC 100%);
      border-right: none;
  }
  [data-testid="stSidebar"] * {
      color: #FFFFFF !important;
  }
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stTextInput label,
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span,
  [data-testid="stSidebar"] small,
  [data-testid="stSidebar"] .stCaption {
      color: #FFFFFF !important;
  }
  [data-testid="stSidebar"] input,
  [data-testid="stSidebar"] [data-baseweb="select"] div,
  [data-testid="stSidebar"] [data-baseweb="input"] input {
      color: #172B4D !important;
      background-color: #FFFFFF !important;
  }
  [data-testid="stSidebar"] [data-baseweb="select"] svg {
      fill: #003366 !important;
  }
  [data-testid="stSidebar"] hr {
      border-color: rgba(255,255,255,0.25) !important;
  }
  [data-testid="stSidebar"] .stButton button {
      background: rgba(255,255,255,0.15) !important;
      color: #FFFFFF !important;
      border: 1px solid rgba(255,255,255,0.35) !important;
      border-radius: 6px;
  }
  [data-testid="stSidebar"] .stButton button:hover {
      background: rgba(255,255,255,0.28) !important;
  }

  /* ── Header banner ── */
  .socioai-header {
      background: linear-gradient(135deg, #003366 0%, #0066CC 60%, #00A3E0 100%);
      padding: 1.5rem 2rem;
      border-radius: 12px;
      margin-bottom: 1.5rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      box-shadow: 0 4px 16px rgba(0,51,102,0.18);
  }
  .socioai-header h1 {
      color: #FFFFFF !important;
      font-size: 2rem !important;
      font-weight: 800 !important;
      margin: 0 !important;
      letter-spacing: -0.5px;
  }
  .socioai-header p {
      color: #A8C8F0 !important;
      margin: 0 !important;
      font-size: 0.95rem;
  }
  .socioai-logo {
      font-size: 2.8rem;
      line-height: 1;
  }

  /* ── Metric cards ── */
  [data-testid="metric-container"] {
      background: #F4F5F7;
      border: 1px solid #DFE1E6;
      border-radius: 10px;
      padding: 1rem;
      transition: box-shadow 0.2s;
  }
  [data-testid="metric-container"]:hover {
      box-shadow: 0 4px 12px rgba(0,51,102,0.10);
  }
  [data-testid="metric-container"] [data-testid="stMetricLabel"] {
      color: #6B778C !important;
      font-size: 0.8rem !important;
      font-weight: 600 !important;
      text-transform: uppercase;
      letter-spacing: 0.5px;
  }
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
      color: #003366 !important;
      font-weight: 700 !important;
  }

  /* ── Tabs ── */
  [data-testid="stTabs"] [role="tab"] {
      font-weight: 600;
      color: #6B778C;
      border-bottom: 3px solid transparent;
      padding: 0.5rem 1rem;
  }
  [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
      color: #003366 !important;
      border-bottom: 3px solid #003366 !important;
  }

  /* ── Buttons ── */
  .stButton button {
      background: #003366 !important;
      color: #FFFFFF !important;
      border: none !important;
      border-radius: 6px !important;
      font-weight: 600 !important;
      padding: 0.4rem 1.2rem !important;
      transition: background 0.2s !important;
  }
  .stButton button:hover {
      background: #0066CC !important;
  }

  /* ── DataFrames ── */
  [data-testid="stDataFrame"] {
      border: 1px solid #DFE1E6;
      border-radius: 8px;
      overflow: hidden;
  }

  /* ── Expanders ── */
  [data-testid="stExpander"] {
      border: 1px solid #DFE1E6 !important;
      border-radius: 8px !important;
      margin-bottom: 0.5rem;
  }

  /* ── Alerts ── */
  .stSuccess { background: #E3FCEF !important; border-left: 4px solid #00875A !important; }
  .stWarning { background: #FFFAE6 !important; border-left: 4px solid #FF8B00 !important; }
  .stError   { background: #FFEBE6 !important; border-left: 4px solid #DE350B !important; }
  .stInfo    { background: #E6F0FF !important; border-left: 4px solid #0066CC !important; }

  /* ── Risk badge ── */
  .badge-alto   { background:#DE350B; color:#fff; padding:2px 10px; border-radius:12px; font-size:0.78rem; font-weight:700; }
  .badge-medio  { background:#FF8B00; color:#fff; padding:2px 10px; border-radius:12px; font-size:0.78rem; font-weight:700; }
  .badge-bajo   { background:#00875A; color:#fff; padding:2px 10px; border-radius:12px; font-size:0.78rem; font-weight:700; }

  /* ── Divider ── */
  hr { border-color: #DFE1E6 !important; margin: 1.2rem 0 !important; }

  /* ── Chat messages ── */
  [data-testid="stChatMessage"] {
      border-radius: 10px;
      margin-bottom: 0.5rem;
  }

  /* ── KPI Cards ── */
  .kpi-card {
      background: #FFFFFF;
      border: 1px solid #DFE1E6;
      border-radius: 12px;
      padding: 1.2rem 1.4rem;
      margin-bottom: 0.5rem;
      box-shadow: 0 2px 8px rgba(0,51,102,0.06);
      transition: box-shadow 0.2s;
  }
  .kpi-card:hover { box-shadow: 0 4px 16px rgba(0,51,102,0.12); }
  .kpi-label {
      color: #6B778C;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      margin-bottom: 0.3rem;
  }
  .kpi-value {
      color: #003366;
      font-size: 1.6rem;
      font-weight: 800;
      line-height: 1.1;
  }
  .kpi-sub {
      color: #6B778C;
      font-size: 0.78rem;
      margin-top: 0.2rem;
  }
  .kpi-alto   { border-left: 4px solid #DE350B; }
  .kpi-medio  { border-left: 4px solid #FF8B00; }
  .kpi-bajo   { border-left: 4px solid #00875A; }
  .kpi-info   { border-left: 4px solid #0066CC; }

  /* ── Section headers ── */
  .section-header {
      color: #003366;
      font-size: 1.1rem;
      font-weight: 700;
      border-bottom: 2px solid #DFE1E6;
      padding-bottom: 0.4rem;
      margin: 1rem 0 0.8rem 0;
  }

  /* ── AI response container ── */
  .ai-response {
      background: #F4F5F7;
      border-left: 4px solid #0066CC;
      border-radius: 0 8px 8px 0;
      padding: 1rem 1.2rem;
      margin-top: 0.5rem;
      font-size: 0.92rem;
  }

  /* ── Checklist item ── */
  .check-item {
      display: flex;
      align-items: flex-start;
      gap: 0.6rem;
      padding: 0.55rem 0.8rem;
      border-radius: 8px;
      margin-bottom: 0.35rem;
      font-size: 0.88rem;
  }
  .check-ok   { background:#E3FCEF; color:#006644; }
  .check-warn { background:#FFFAE6; color:#974F0C; }
  .check-fail { background:#FFEBE6; color:#BF2600; }
  .check-icon { font-size: 1rem; flex-shrink: 0; margin-top:1px; }

  /* ── Status badge ── */
  .status-badge {
      display: inline-block;
      padding: 3px 12px;
      border-radius: 20px;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.4px;
  }
  .badge-ok   { background:#E3FCEF; color:#006644; }
  .badge-warn { background:#FFFAE6; color:#974F0C; }
  .badge-fail { background:#FFEBE6; color:#BF2600; }

  /* ── Fix buttons visibility ── */
  .stButton > button {
      background-color: #003366 !important;
      color: #FFFFFF !important;
      border: 2px solid #003366 !important;
      border-radius: 8px !important;
      font-weight: 700 !important;
      padding: 0.5rem 1.2rem !important;
      transition: all 0.2s !important;
  }
  .stButton > button:hover {
      background-color: #0066CC !important;
      border-color: #0066CC !important;
      color: #FFFFFF !important;
  }
  .stButton > button[kind="primary"] {
      background-color: #003366 !important;
      color: #FFFFFF !important;
  }
  .stDownloadButton > button {
      background-color: #00875A !important;
      color: #FFFFFF !important;
      border: 2px solid #00875A !important;
      border-radius: 8px !important;
      font-weight: 700 !important;
  }
  .stDownloadButton > button:hover {
      background-color: #006644 !important;
      border-color: #006644 !important;
  }

  /* ── Welcome screen ── */
  .welcome-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 80vh;
      text-align: center;
      padding: 2rem;
  }
  .welcome-logo {
      font-size: 3.5rem;
      font-weight: 900;
      color: #FFFFFF;
      letter-spacing: -1px;
      margin-bottom: 0.5rem;
  }
  .welcome-sub {
      font-size: 1.1rem;
      color: #A8C4E0;
      margin-bottom: 2.5rem;
  }
  .welcome-bg {
      background: linear-gradient(135deg, #001a40 0%, #003366 60%, #0055A5 100%);
      border-radius: 20px;
      padding: 4rem 3rem;
      margin: 2rem auto;
      max-width: 700px;
      box-shadow: 0 20px 60px rgba(0,51,102,0.3);
  }
  .client-card {
      background: #FFFFFF;
      border: 2px solid #DFE1E6;
      border-radius: 12px;
      padding: 1.2rem 1.5rem;
      margin-bottom: 0.6rem;
      cursor: pointer;
      transition: all 0.2s;
      text-align: left;
  }
  .client-card:hover {
      border-color: #003366;
      box-shadow: 0 4px 16px rgba(0,51,102,0.15);
  }
  .client-card-selected {
      border-color: #003366 !important;
      background: #EBF2FF !important;
  }
  .client-card-title {
      font-weight: 700;
      color: #003366;
      font-size: 1rem;
  }
  .client-card-sub {
      color: #6B778C;
      font-size: 0.82rem;
      margin-top: 2px;
  }
  .setup-hero {
      background: linear-gradient(135deg, #EAF2FF 0%, #F5F9FF 100%);
      border: 1px solid #D5E2F5;
      border-radius: 16px;
      padding: 1.2rem 1.4rem;
      margin: 1rem 0 1.2rem 0;
  }
  .setup-hero-title {
      color: #003366;
      font-size: 1.45rem;
      font-weight: 900;
      margin-bottom: 0.25rem;
  }
  .setup-hero-sub {
      color: #44546A;
      font-size: 0.92rem;
      line-height: 1.5;
  }
  .setup-step {
      display: inline-block;
      background: #FFFFFF;
      border: 1px solid #B3C8E8;
      color: #003366;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 0.76rem;
      font-weight: 700;
      margin-right: 6px;
      margin-top: 8px;
  }
  /* ── Sidebar buttons ── */
  [data-testid="stSidebar"] .stButton > button {
      background-color: #FFFFFF !important;
      color: #003366 !important;
      border: 2px solid #003366 !important;
      border-radius: 8px !important;
      font-weight: 600 !important;
  }
  [data-testid="stSidebar"] .stButton > button:hover {
      background-color: #003366 !important;
      color: #FFFFFF !important;
  }
  [data-testid="stSidebar"] .stFileUploader label {
      color: #172B4D !important;
      font-weight: 600 !important;
  }
  [data-testid="stSidebar"] .stFileUploader
      [data-testid="stFileUploaderDropzone"] {
      background-color: #F4F5F7 !important;
      border: 2px dashed #003366 !important;
      border-radius: 8px !important;
  }
  [data-testid="stSidebar"] .stFileUploader
      [data-testid="stFileUploaderDropzone"] p {
      color: #003366 !important;
      font-weight: 600 !important;
  }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stTextInput label,
  [data-testid="stSidebar"] .stRadio label,
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] .stCaption {
      color: #172B4D !important;
  }
  /* File uploader button inside sidebar */
  [data-testid="stSidebar"]
      [data-testid="stFileUploaderDropzoneInstructions"] {
      color: #003366 !important;
  }
  [data-testid="stSidebar"] .stFileUploader button {
      background-color: #003366 !important;
      color: #FFFFFF !important;
      border-radius: 6px !important;
  }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Helpers defensivos
# ============================================================
def safe_call(func: Any, *args: Any, default: Any = None, **kwargs: Any) -> Any:
    if func is None:
        return default
    try:
        return func(*args, **kwargs)
    except Exception:
        return default


def _obtener_admin_password() -> str:
    """Load admin password from secrets or env."""
    try:
        import streamlit as st
        val = st.secrets.get("ADMIN_PASSWORD", "")
        if val and str(val).strip():
            return str(val).strip()
    except Exception:
        pass
    return os.environ.get("ADMIN_PASSWORD", "socioai2025")


def _limpiar_cliente_session(cliente_id: str) -> int:
    """
    Removes ALL session data related to a client:
    - All keys containing the client name
    - Active client references if they match
    - Upload keys, perfil, mayor, TB tipo
    """
    keys_to_delete = []

    # Keys containing client name
    for k in list(st.session_state.keys()):
        if cliente_id in str(k):
            keys_to_delete.append(k)

    # Active client keys if they point to this client
    active_keys = [
        "cliente_activo", "etapa_activa",
        "setup_cliente_sel", "auditor_nombre",
    ]
    for k in active_keys:
        if st.session_state.get(k) == cliente_id:
            keys_to_delete.append(k)

    # Remove duplicates
    keys_to_delete = list(set(keys_to_delete))

    for k in keys_to_delete:
        try:
            del st.session_state[k]
        except KeyError:
            pass

    # Also clear module-level caches
    try:
        from analysis.lector_tb import clear_tb_cache
        clear_tb_cache(cliente_id)
    except Exception:
        pass
    try:
        from domain.services.leer_perfil import clear_perfil_cache
        clear_perfil_cache(cliente_id)
    except Exception:
        pass

    # Also delete from remote persistence (Supabase/Sheets)
    if _sheets_ok and eliminar_cliente_sheets:
        safe_call(
            eliminar_cliente_sheets,
            cliente_id,
            default=False,
        )
        # Invalidate cache
        if "sheets_clientes_cache" in st.session_state:
            del st.session_state["sheets_clientes_cache"]

    return len(keys_to_delete)


def _get_clientes_dinamicos() -> list[str]:
    """
    Returns clients from:
    1. Remote persistence (Supabase/Sheets)
    2. Local repo folders (demo clients)
    3. Session-created clients (this session only)
    Excludes deleted clients.
    """
    _borrados = st.session_state.get(
        "clientes_borrados_sesion", []
    )

    # 1. From remote persistence (persistent)
    _sheets_clientes: list[str] = []
    if _sheets_ok and sheets_disponible and \
            safe_call(sheets_disponible, default=False):
        _cache_key = "sheets_clientes_cache"
        # Cache for 60 seconds to avoid too many API calls
        _cache_time_key = "sheets_clientes_cache_time"
        import time
        _now = time.time()
        _last = st.session_state.get(
            _cache_time_key, 0
        )
        if _now - _last > 60 or \
                _cache_key not in st.session_state:
            _raw = safe_call(
                cargar_clientes_sheets, default=[]
            ) or []
            _ids = [
                c["cliente_id"] for c in _raw
                if c.get("cliente_id")
            ]
            st.session_state[_cache_key] = _ids
            st.session_state[_cache_time_key] = _now

            # Also restore perfil cache for each client
            for c in _raw:
                _cid = c.get("cliente_id", "")
                _pf = c.get("perfil", {})
                if _cid and _pf:
                    try:
                        from domain.services.leer_perfil \
                            import set_perfil_cache
                        set_perfil_cache(_cid, _pf)
                    except Exception:
                        pass
                    st.session_state[
                        f"perfil_upload_{_cid}"
                    ] = _pf

        _sheets_clientes = st.session_state.get(
            _cache_key, []
        )

    # 2. From repo folders
    _base_path = Path("data/clientes")
    _base = sorted([
        d.name for d in _base_path.iterdir()
        if d.is_dir()
    ]) if _base_path.exists() else []

    # 3. Session-created
    _nuevos = st.session_state.get(
        "clientes_creados_sesion", []
    )

    _todos = list(dict.fromkeys(
        _sheets_clientes + _base + _nuevos
    ))
    return [c for c in _todos if c not in _borrados]


def fmt_num(value: Any, decimals: int = 2) -> str:
    try:
        return f"{float(value):,.{decimals}f}"
    except Exception:
        return "0.00"


def fmt_money(value: Any) -> str:
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "$0.00"


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def get_first(data: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    for k in keys:
        if k in data and data[k] is not None:
            return data[k]
    return default


def is_holding_profile(perfil: dict[str, Any] | None) -> bool:
    perfil = perfil or {}
    if not isinstance(perfil, dict):
        return False
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    contexto = perfil.get("contexto_negocio", {}) if isinstance(perfil.get("contexto_negocio"), dict) else {}
    industria = perfil.get("industria_inteligente", {}) if isinstance(perfil.get("industria_inteligente"), dict) else {}
    blob = " ".join(
        [
            str(cliente.get("sector", "")),
            str(cliente.get("subsector", "")),
            str(contexto.get("actividad_principal", "")),
            str(industria.get("sector_base", "")),
            str(industria.get("subtipo_negocio", "")),
        ]
    ).lower()
    return "holding" in blob or "sociedad_cartera" in blob or "cartera" in blob


def infer_area_options(
    ranking_areas: pd.DataFrame | None,
    tb: pd.DataFrame | None,
    cliente: str,
) -> list[tuple[str, str]]:
    """
    Returns only areas that have actual data for this client.
    Priority: areas present in ranking_areas WITH saldo > 0,
    ordered by score descending.
    Fallback: areas found in TB ls column.
    """
    options: list[tuple[str, str]] = []

    # ── Primary: ranking with real saldo ──────────────────────
    if ranking_areas is not None and not ranking_areas.empty:
        needed = {"area", "nombre"}
        if needed.issubset(set(ranking_areas.columns)):
            # Filter: only areas present with actual balance
            mask_present = pd.Series([True] * len(ranking_areas))
            if "con_saldo" in ranking_areas.columns:
                mask_present = ranking_areas["con_saldo"].astype(bool)
            elif "saldo_total" in ranking_areas.columns:
                mask_present = ranking_areas["saldo_total"].apply(
                    lambda x: abs(float(x or 0)) > 0.01
                )
            elif "estado_presencia" in ranking_areas.columns:
                mask_present = ranking_areas["estado_presencia"].astype(
                    str
                ).isin({"con_saldo", "sin_saldo"})

            df_present = ranking_areas[mask_present].copy()

            # Sort by score descending so highest-risk areas appear first
            if "score_riesgo" in df_present.columns:
                df_present = df_present.sort_values(
                    "score_riesgo", ascending=False
                )

            for _, row in df_present.iterrows():
                code = normalize_text(row.get("area", ""))
                name = normalize_text(row.get("nombre", ""))
                if code:
                    score = row.get("score_riesgo")
                    score_txt = (
                        f" [{float(score):.0f}]" if score is not None else ""
                    )
                    label = (
                        f"{code} — {name}{score_txt}" if name else code
                    )
                    options.append((code, label))

    # ── Fallback: read ls column from TB directly ──────────────
    if not options and tb is not None and not tb.empty:
        ls_col = next(
            (c for c in ["ls", "l/s", "l_s", "L/S"] if c in tb.columns),
            None,
        )
        if ls_col:
            present_ls = sorted(
                {
                    normalize_text(v)
                    for v in tb[ls_col].dropna().tolist()
                    if normalize_text(v)
                }
            )

            def _label(code: str) -> str:
                area = safe_call(obtener_area_por_codigo, code, default=None)
                if isinstance(area, dict):
                    title = normalize_text(area.get("titulo", ""))
                    if title:
                        return f"{code} — {title}"
                return f"{code} — Área {code}"

            for code in present_ls:
                options.append((code, _label(code)))

    # ── Last resort ────────────────────────────────────────────
    if not options:
        options = [("140", "140 — Efectivo y Equivalentes")]

    return options


def build_area_df(tb: pd.DataFrame | None, variaciones: pd.DataFrame | None, codigo_ls: str) -> pd.DataFrame:
    """
    Intenta construir un DataFrame de area compatible con servicios legacy.
    """
    codigo_ls_norm = str(codigo_ls or "").strip().replace(".0", "")

    def _norm(v: Any) -> str:
        return str(v or "").strip().replace(".0", "")

    def _mask_ls(series: pd.Series, code: str) -> pd.Series:
        s = series.astype(str).str.strip().str.replace(r"\.0+$", "", regex=True)
        code = str(code).strip().replace(".0", "")
        # Match exact code or subcode (e.g. 200, 200.1, 200.2)
        return s.str.match(rf"^{code}(\.|$)", na=False)

    if variaciones is not None and not variaciones.empty:
        for col in ["ls", "l/s", "l_s", "L/S"]:
            if col in variaciones.columns:
                area = variaciones[
                    _mask_ls(variaciones[col], codigo_ls_norm)
                ].copy()
                if not area.empty:
                    return area

    if tb is not None and not tb.empty:
        # Preferred: filter by L/S area code
        ls_col = next(
            (c for c in ["ls", "l/s", "l_s", "L/S", "linea_significancia"] if c in tb.columns),
            None,
        )
        codigo_col = None
        nombre_col = None
        saldo_col = None
        saldo_prev_col = None
        for c in ["codigo", "numero_de_cuenta", "cuenta", "cod_cuenta"]:
            if c in tb.columns:
                codigo_col = c
                break
        for c in ["nombre", "nombre_cuenta", "descripcion"]:
            if c in tb.columns:
                nombre_col = c
                break
        for c in ["saldo_2025", "saldo_preliminar", "saldo_actual", "saldo"]:
            if c in tb.columns:
                saldo_col = c
                break
        for c in ["saldo_2024", "saldo_anterior", "saldo_base"]:
            if c in tb.columns:
                saldo_prev_col = c
                break

        if ls_col and saldo_col:
            mask = _mask_ls(tb[ls_col], codigo_ls_norm)
            sub = tb[mask].copy()
            if not sub.empty:
                out = pd.DataFrame()
                out["numero_cuenta"] = (
                    sub[codigo_col].astype(str) if codigo_col else ""
                )
                out["nombre_cuenta"] = sub[nombre_col] if nombre_col else ""
                out["saldo_actual"] = pd.to_numeric(sub[saldo_col], errors="coerce").fillna(0.0)
                out["saldo_anterior"] = (
                    pd.to_numeric(sub[saldo_prev_col], errors="coerce").fillna(0.0)
                    if saldo_prev_col
                    else 0.0
                )
                out["variacion_absoluta"] = out["saldo_actual"] - out["saldo_anterior"]
                out["abs_variacion_absoluta"] = out["variacion_absoluta"].abs()
                out["flag_movimiento_relevante"] = out["abs_variacion_absoluta"] > 0
                out["flag_sin_base"] = True
                out["ls"] = codigo_ls_norm
                return out

        # Fallback: filtrar por prefijo de numero de cuenta
        if codigo_col and saldo_col:
            mask = tb[codigo_col].astype(str).str.startswith(codigo_ls_norm)
            sub = tb[mask].copy()
            if not sub.empty:
                out = pd.DataFrame()
                out["numero_cuenta"] = sub[codigo_col].astype(str)
                out["nombre_cuenta"] = sub[nombre_col] if nombre_col else ""
                out["saldo_actual"] = pd.to_numeric(sub[saldo_col], errors="coerce").fillna(0.0)
                out["saldo_anterior"] = (
                    pd.to_numeric(sub[saldo_prev_col], errors="coerce").fillna(0.0)
                    if saldo_prev_col
                    else 0.0
                )
                out["variacion_absoluta"] = out["saldo_actual"] - out["saldo_anterior"]
                out["abs_variacion_absoluta"] = out["variacion_absoluta"].abs()
                out["flag_movimiento_relevante"] = out["abs_variacion_absoluta"] > 0
                out["flag_sin_base"] = True
                out["ls"] = codigo_ls_norm
                return out

    return pd.DataFrame()


def prepare_area_workspace(
    cliente: str,
    etapa: str,
    codigo_ls: str,
    perfil: dict[str, Any] | None,
    tb: pd.DataFrame | None,
    variaciones: pd.DataFrame | None,
    ranking_areas: pd.DataFrame | None,
) -> dict[str, Any]:
    perfil = perfil or {}

    estado_area = safe_call(cargar_estado_area, cliente, codigo_ls, default={}) or {}
    area_df = build_area_df(tb, variaciones, codigo_ls)

    # Nombre y score desde ranking cuando exista
    area_name = f"Area {codigo_ls}"
    area_score = None
    saldo_total = 0.0
    pct_total = 0.0
    materialidad_relativa = 0.0
    justificacion = ""
    prioridad = "media"
    expert_flags_count = 0
    expert_flags: list[dict[str, Any]] = []
    materialidad_sugerida = 0.0
    materialidad_ejecucion = 0.0
    trivialidad = 0.0

    if ranking_areas is not None and not ranking_areas.empty and "area" in ranking_areas.columns:
        rows = ranking_areas[ranking_areas["area"].astype(str).str.strip() == str(codigo_ls).strip()]
        if not rows.empty:
            row0 = rows.iloc[0]
            area_name = normalize_text(row0.get("nombre", "")) or area_name
            area_score = row0.get("score_riesgo")
            saldo_total = float(row0.get("saldo_total", 0) or 0)
            pct_total = float(row0.get("pct_total", 0) or 0)
            materialidad_relativa = float(row0.get("materialidad_relativa", 0) or 0)
            justificacion = normalize_text(row0.get("justificacion", ""))
            prioridad = normalize_text(row0.get("prioridad", "media")) or "media"
            expert_flags_count = int(row0.get("expert_flags_count", 0) or 0)
            raw_flags = row0.get("expert_flags", [])
            expert_flags = raw_flags if isinstance(raw_flags, list) else []
            materialidad_sugerida = float(row0.get("materialidad_sugerida", 0) or 0)
            materialidad_ejecucion = float(row0.get("materialidad_ejecucion", 0) or 0)
            trivialidad = float(row0.get("trivialidad", 0) or 0)

    if not area_name or area_name == f"Area {codigo_ls}":
        area_name = normalize_text(estado_area.get("nombre", "")) or area_name

    # Materialidad (fallback si ranking no viene enriquecido)
    if materialidad_ejecucion <= 0:
        mat = safe_call(calcular_materialidad, cliente, default={}) or {}
        materialidad_sugerida = float(mat.get("materialidad_sugerida", 0) or 0)
        materialidad_ejecucion = float(mat.get("materialidad_desempeno", 0) or 0)
        trivialidad = float(mat.get("error_trivial", 0) or 0)
        if materialidad_ejecucion > 0:
            materialidad_relativa = (saldo_total / materialidad_ejecucion) * 100 if saldo_total else 0.0

    # Riesgos
    riesgos = safe_call(detectar_riesgos_area, area_df, str(codigo_ls), perfil, default=[]) or []
    riesgo_estado = normalize_text(estado_area.get("riesgo", ""))
    if not riesgo_estado and riesgos:
        niveles = [normalize_text(r.get("nivel", "")).upper() for r in riesgos]
        if "ALTO" in niveles:
            riesgo_estado = "ALTO"
        elif "MEDIO" in niveles:
            riesgo_estado = "MEDIO"
        elif "BAJO" in niveles:
            riesgo_estado = "BAJO"

    # Flags expertas directas (fallback si ranking no las trae)
    if not expert_flags:
        expert_flags = safe_call(
            detectar_expert_flags,
            codigo_area=str(codigo_ls),
            perfil=perfil,
            metricas_area={
                "saldo_total": saldo_total,
                "pct_total": pct_total,
                "materialidad_relativa": materialidad_relativa,
                "variacion_abs_total": float(area_df.get("abs_variacion_absoluta", pd.Series(dtype=float)).sum())
                if not area_df.empty
                else 0.0,
            },
            default=[],
        ) or []
        expert_flags_count = len(expert_flags)

    # Procedimientos
    proc_estado = safe_call(obtener_procedimientos_area, estado_area, default=[]) or []
    if not proc_estado:
        proc_estado = safe_call(procedimientos_por_area_estructurados, str(codigo_ls), perfil, riesgos, default=[]) or []

    if proc_estado and isinstance(proc_estado[0], str):
        proc_estado = [
            {"id": f"proc_{idx+1}", "descripcion": desc, "estado": "planificado"}
            for idx, desc in enumerate(proc_estado)
        ]

    proc_df = pd.DataFrame(proc_estado) if proc_estado else pd.DataFrame(columns=["id", "descripcion", "estado"])
    if "estado" not in proc_df.columns:
        proc_df["estado"] = "planificado"
    if "descripcion" not in proc_df.columns:
        proc_df["descripcion"] = ""

    done_states = {"ejecutado", "completado", "cerrado", "no_aplicable", "no_aplica"}
    pending_count = int((~proc_df["estado"].astype(str).str.lower().isin(done_states)).sum()) if not proc_df.empty else 0

    # Hallazgos
    hallazgos = safe_call(extraer_hallazgos_abiertos, estado_area, default=[]) or []
    if not hallazgos:
        raw_hallazgos = estado_area.get("hallazgos_abiertos", []) or []
        for h in raw_hallazgos:
            if isinstance(h, dict):
                desc = normalize_text(h.get("descripcion", ""))
                if desc:
                    hallazgos.append(desc)
            elif normalize_text(h):
                hallazgos.append(normalize_text(h))

    # Cobertura
    cobertura = safe_call(
        evaluar_cobertura_aseveraciones,
        codigo_ls=str(codigo_ls),
        procedimientos=proc_df.to_dict("records") if not proc_df.empty else [],
        hallazgos_abiertos=hallazgos,
        default=None,
    )

    if cobertura is None:
        esperadas = ASEVERACIONES_LS.get(str(codigo_ls), []) if isinstance(ASEVERACIONES_LS, dict) else []
        cobertura = {
            "esperadas": esperadas,
            "cubiertas": [],
            "debiles": [],
            "no_cubiertas": esperadas,
            "excluidas_no_aplica": [],
            "cobertura_porcentaje": 0.0,
            "conclusion": "sin_mapeo",
        }

    # Briefing
    area_summary = safe_call(construir_resumen_area, area_df, default={}) or {}
    lectura = safe_call(construir_lectura_inicial, str(codigo_ls), area_df, perfil, default="") or ""
    focos = safe_call(construir_foco_auditoria, str(codigo_ls), perfil, area_df, default=[]) or []
    if not isinstance(focos, list):
        focos = []
    foco_holding = safe_call(construir_foco_holding, str(codigo_ls), perfil, area_df, default=[]) or []
    if not isinstance(foco_holding, list):
        foco_holding = []

    if not area_summary:
        area_summary = {
            "cuentas": int(len(area_df)) if not area_df.empty else 0,
            "saldo_actual": float(area_df.get("saldo_actual", pd.Series(dtype=float)).sum()) if not area_df.empty else saldo_total,
            "variacion_neta": float(area_df.get("variacion_absoluta", pd.Series(dtype=float)).sum()) if not area_df.empty else 0.0,
            "variacion_acumulada": float(area_df.get("abs_variacion_absoluta", pd.Series(dtype=float)).sum()) if not area_df.empty else 0.0,
            "cuentas_relevantes": int(area_df.get("flag_movimiento_relevante", pd.Series(dtype=bool)).sum()) if not area_df.empty else 0,
        }

    if not lectura:
        lectura = (
            f"El area {area_name} (L/S {codigo_ls}) presenta saldo {fmt_money(area_summary.get('saldo_actual', 0))} "
            f"y variacion neta {fmt_money(area_summary.get('variacion_neta', 0))}."
        )

    # Cierre
    cierre_texto = safe_call(revisar_cierre_area_llm, cliente, str(codigo_ls), etapa=etapa, default="") or ""
    pendientes = safe_call(obtener_pendientes_area, estado_area, default=[]) or []

    if not cierre_texto:
        cierre_texto = (
            f"Revision de cierre para {area_name}. "
            f"Cobertura actual: {fmt_num(cobertura.get('cobertura_porcentaje', 0), 1)}%."
        )

    if not justificacion:
        justificacion = (
            f"Impacto relativo {fmt_num(materialidad_relativa, 1)}% sobre materialidad de ejecucion; "
            f"{expert_flags_count} bandera(s) experta(s)."
        )

    ws_base = {
        "codigo_ls": str(codigo_ls),
        "area_name": area_name,
        "etapa": etapa,
        "area_score": area_score,
        "riesgo": riesgo_estado or "N/A",
        "coverage": float(cobertura.get("cobertura_porcentaje", 0) or 0),
        "hallazgos": hallazgos,
        "hallazgos_count": len(hallazgos),
        "proc_df": proc_df,
        "pending_count": pending_count,
        "estado_area": estado_area,
        "area_df": area_df,
        "area_summary": area_summary,
        "riesgos": riesgos,
        "focos": focos,
        "foco_holding": foco_holding,
        "es_holding": is_holding_profile(perfil),
        "lectura": lectura,
        "cobertura": cobertura,
        "cierre_texto": cierre_texto,
        "pendientes": pendientes,
        "materialidad_relativa": materialidad_relativa,
        "materialidad_sugerida": materialidad_sugerida,
        "materialidad_ejecucion": materialidad_ejecucion,
        "trivialidad": trivialidad,
        "expert_flags": expert_flags,
        "expert_flags_count": expert_flags_count,
        "justificacion": justificacion,
        "prioridad": prioridad,
        "perfil": perfil,
        "contexto": perfil,
    }

    area_info = {
        "nombre": area_name,
        "codigo_ls": str(codigo_ls),
        "saldo": saldo_total,
        "variacion_pct": float(pct_total / 100.0) if pct_total else 0.0,
        "score_riesgo": float(area_score or 0.0) if area_score is not None else 0.0,
        "cobertura": float(cobertura.get("cobertura_porcentaje", 0) or 0),
        "estado": str(ws_base.get("estado_presencia", "NO_PRESENTE")).upper(),
    }
    ws_base["area_info"] = area_info
    ws_base["materialidad_desempeno"] = materialidad_ejecucion
    ws_base["sector"] = normalize_text(
        perfil.get("cliente", {}).get("sector", perfil.get("sector", ""))
        if isinstance(perfil, dict)
        else ""
    ).lower()
    ws_base["marco_niif"] = normalize_text(
        perfil.get("encargo", {}).get("marco_referencial", "")
        if isinstance(perfil, dict)
        else ""
    )
    ws_base["cliente"] = cliente

    riesgos_automaticos = safe_call(detectar_riesgos_area_auto, ws_base, default=[]) or []
    if not isinstance(riesgos_automaticos, list):
        riesgos_automaticos = []
    ws_base["riesgos_automaticos"] = riesgos_automaticos

    calidad_eval = safe_call(
        evaluar_alertas_metodologia,
        cliente,
        str(codigo_ls),
        ws_base,
        default={},
    ) or {}

    ws_base["calidad_metodologia"] = calidad_eval if isinstance(calidad_eval, dict) else {}
    return ws_base




def render_consultar_socio_tab(ws: dict[str, Any], cliente: str) -> None:
    st.subheader("Consulta al Socio")

    if consultar_socio is None:
        st.info("Servicio de chat no disponible en este entorno.")
        return

    chat_key = f"chat_area_{cliente}_{ws.get('codigo_ls', 'na')}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    pregunta = st.text_input("Haz una pregunta sobre esta area", key=f"q_{chat_key}")

    if st.button("Consultar", key=f"b_{chat_key}"):
        respuesta = safe_call(consultar_socio, pregunta, ws, default="No se pudo obtener respuesta.")
        st.session_state[chat_key].append(("Usuario", pregunta))
        st.session_state[chat_key].append(("Socio", respuesta))

    for rol, msg in st.session_state[chat_key]:
        if rol == "Usuario":
            st.markdown(f"**Tu:** {msg}")
        else:
            st.markdown(f"**Socio:** {msg}")


def render_welcome_screen():
    """Full-page welcome screen."""
    # Hide sidebar on welcome screen
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex; justify-content:center;
                align-items:center; min-height:80vh;">
      <div class="welcome-bg">
        <div style="text-align:center;">
          <div style="font-size:4rem; margin-bottom:0.5rem;">📊</div>
          <div class="welcome-logo">SocioAI</div>
          <div class="welcome-sub">
            Plataforma Inteligente de Auditoría Financiera
          </div>
          <div style="color:#A8C4E0; font-size:0.9rem;
                      margin-bottom:2.5rem; line-height:1.6;">
            Análisis de riesgo · Briefings con IA · Programas de auditoría<br>
            Ranking de áreas · Reporte PDF ejecutivo
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button(
            "🚀 Comenzar",
            key="btn_welcome_start",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["app_screen"] = "setup"
            st.rerun()


def render_setup_screen(clientes_disponibles: list[str]):
    """Client setup screen: auditor + client + upload."""
    # Hide sidebar on setup screen
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; padding:1.2rem 0 0.2rem 0;">
      <span style="font-size:1.95rem; font-weight:900;
                   color:#003366;">📊 SocioAI</span>
      <div style="color:#6B778C; font-size:0.98rem;
                  margin-top:0.25rem;">
        Configura tu sesión de auditoría
      </div>
    </div>
    <div class="setup-hero">
      <div class="setup-hero-title">Iniciemos tu análisis</div>
      <div class="setup-hero-sub">
        Completa 3 pasos para entrar al dashboard:
        selecciona cliente, sube tu Trial Balance y define la etapa.
      </div>
      <span class="setup-step">1. Cliente</span>
      <span class="setup-step">2. Archivos</span>
      <span class="setup-step">3. Etapa</span>
    </div>
    """, unsafe_allow_html=True)

    main_col, _ = st.columns([2, 1])
    with main_col:

        # ── Auditor name ──────────────────────────────────────
        st.markdown(
            "<div class='section-header'>👤 Auditor</div>",
            unsafe_allow_html=True,
        )
        nombre_auditor = st.text_input(
            "Nombre del auditor",
            placeholder="ej: Erick Salas",
            key="setup_auditor",
            label_visibility="collapsed",
        )

        st.markdown("<div style='margin-top:1.2rem;'></div>",
                    unsafe_allow_html=True)

        # ── Client selection ──────────────────────────────────
        st.markdown(
            "<div class='section-header'>🏢 Cliente</div>",
            unsafe_allow_html=True,
        )

        modo = st.radio(
            "Modo",
            ["Seleccionar cliente existente", "Crear cliente nuevo"],
            key="setup_modo",
            horizontal=True,
            label_visibility="collapsed",
        )

        cliente_elegido = ""

        if modo == "Seleccionar cliente existente":
            if clientes_disponibles:
                st.markdown("**Clientes disponibles:**")
                # Check if any client has session data loaded
                clientes_con_datos = [
                    c for c in clientes_disponibles
                    if any(
                        c in str(k)
                        for k in st.session_state.keys()
                        if any(
                            prefix in str(k)
                            for prefix in [
                                "tb_upload_", "perfil_upload_",
                                "mayor_upload_",
                            ]
                        )
                    )
                ]
                for c in clientes_disponibles:
                    label = c.replace("_", " ").title()
                    is_selected = (
                        st.session_state.get("setup_cliente_sel") == c
                    )
                    has_data = c in clientes_con_datos

                    card_class = (
                        "client-card client-card-selected"
                        if is_selected
                        else "client-card"
                    )

                    # Data badge
                    data_badge = (
                        "<span style='background:#E3FCEF; color:#006644;"
                        " padding:2px 8px; border-radius:10px;"
                        " font-size:0.75rem; font-weight:700;"
                        " margin-left:8px;'>✅ Con datos</span>"
                        if has_data else
                        "<span style='background:#F4F5F7; color:#6B778C;"
                        " padding:2px 8px; border-radius:10px;"
                        " font-size:0.75rem;'>Sin datos</span>"
                    )

                    st.markdown(
                        f"""<div class="{card_class}">
                            <div class="client-card-title">
                                🏢 {label} {data_badge}
                            </div>
                            <div class="client-card-sub">{c}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                    btn_col1, btn_col2 = st.columns([3, 1])
                    with btn_col1:
                        if st.button(
                            "Seleccionar",
                            key=f"sel_{c}",
                            use_container_width=True,
                        ):
                            st.session_state["setup_cliente_sel"] = c
                            st.rerun()

                    with btn_col2:
                        if st.button(
                            "🗑️ Borrar",
                            key=f"del_{c}",
                            use_container_width=True,
                            help="Borra los datos cargados de este cliente",
                        ):
                            # Open delete confirmation for this client
                            st.session_state[
                                "delete_confirm_cliente"
                            ] = c
                            st.rerun()

                # ── Delete confirmation dialog ────────────────────────
                cliente_a_borrar = st.session_state.get(
                    "delete_confirm_cliente", ""
                )
                if cliente_a_borrar:
                    st.markdown("<div style='margin-top:1rem;'></div>",
                                unsafe_allow_html=True)
                    st.markdown(
                        f"<div class='check-item check-fail'>"
                        f"<span class='check-icon'>⚠️</span>"
                        f"<span>Vas a borrar los datos de "
                        f"<b>{cliente_a_borrar}</b> "
                        f"de esta sesión. "
                        f"Ingresa la contraseña para confirmar."
                        f"</span></div>",
                        unsafe_allow_html=True,
                    )

                    conf_col1, conf_col2, conf_col3 = st.columns(
                        [2, 1, 1]
                    )
                    with conf_col1:
                        pwd_input = st.text_input(
                            "Contraseña de administrador",
                            type="password",
                            key="delete_pwd_input",
                            label_visibility="collapsed",
                            placeholder="Contraseña...",
                        )
                    with conf_col2:
                        if st.button(
                            "✅ Confirmar borrado",
                            key="btn_confirm_delete",
                            use_container_width=True,
                        ):
                            admin_pwd = _obtener_admin_password()
                            if pwd_input == admin_pwd:
                                # Real delete: clear all session data
                                n = _limpiar_cliente_session(cliente_a_borrar)

                                # Remove from dynamic clients list
                                _creados = st.session_state.get(
                                    "clientes_creados_sesion", []
                                )
                                if cliente_a_borrar in _creados:
                                    _creados = [
                                        c for c in _creados
                                        if c != cliente_a_borrar
                                    ]
                                    st.session_state[
                                        "clientes_creados_sesion"
                                    ] = _creados

                                # Add to permanent blocklist for this session
                                _borrados = st.session_state.get(
                                    "clientes_borrados_sesion", []
                                )
                                if cliente_a_borrar not in _borrados:
                                    _borrados.append(cliente_a_borrar)
                                st.session_state[
                                    "clientes_borrados_sesion"
                                ] = _borrados

                                # Clear active client if it was deleted
                                if st.session_state.get(
                                    "setup_cliente_sel"
                                ) == cliente_a_borrar:
                                    del st.session_state["setup_cliente_sel"]

                                if st.session_state.get(
                                    "cliente_activo"
                                ) == cliente_a_borrar:
                                    del st.session_state["cliente_activo"]

                                # Clean up confirmation state
                                del st.session_state["delete_confirm_cliente"]
                                for k in ["delete_pwd_input"]:
                                    if k in st.session_state:
                                        del st.session_state[k]

                                st.success(
                                    f"✅ Cliente **{cliente_a_borrar}** "
                                    f"eliminado completamente ({n} "
                                    f"entradas borradas)."
                                )
                                st.rerun()
                            else:
                                st.error("❌ Contraseña incorrecta.")

                    with conf_col3:
                        if st.button(
                            "✗ Cancelar",
                            key="btn_cancel_delete",
                            use_container_width=True,
                        ):
                            del st.session_state[
                                "delete_confirm_cliente"
                            ]
                            if "delete_pwd_input" in st.session_state:
                                del st.session_state["delete_pwd_input"]
                            st.rerun()

                cliente_elegido = st.session_state.get(
                    "setup_cliente_sel", ""
                )
            else:
                st.info(
                    "No hay clientes guardados. "
                    "Crea uno nuevo."
                )
        else:
            st.markdown("**Identificador del cliente** (sin espacios)")
            cliente_id_input = st.text_input(
                "ID único",
                placeholder="ej: empresa_abc_2025",
                key="setup_cliente_id",
                help="Identificador interno. Solo letras, números y guiones bajos.",
            )
            # Clean ID: only alphanumeric and underscores
            if cliente_id_input.strip():
                import re as _re
                cliente_elegido = _re.sub(
                    r"[^a-z0-9_]", "_",
                    cliente_id_input.strip().lower()
                ).strip("_")
                if cliente_elegido:
                    st.caption(
                        f"✅ ID interno: `{cliente_elegido}`"
                    )
                else:
                    st.warning(
                        "ID inválido. Usa solo letras y números."
                    )
                    cliente_elegido = ""

        st.markdown("<div style='margin-top:1.2rem;'></div>",
                    unsafe_allow_html=True)

        # ── Stage selection ───────────────────────────────────
        st.markdown("<div style='margin-top:1.2rem;'></div>",
                    unsafe_allow_html=True)
        st.markdown(
            "<div class='section-header'>📋 Etapa</div>",
            unsafe_allow_html=True,
        )
        etapa_setup = st.selectbox(
            "Etapa de auditoría",
            ["planificacion", "ejecucion", "cierre"],
            key="setup_etapa",
            label_visibility="collapsed",
        )

        # ── File uploads ──────────────────────────────────────
        st.markdown(
            "<div class='section-header'>📂 Archivos</div>",
            unsafe_allow_html=True,
        )
        # ── Check if client already has data ─────────────────
        _tiene_tb_repo = (
            (Path("data/clientes") / cliente_elegido / "tb.xlsx")
            .exists()
            if cliente_elegido else False
        )
        _tiene_tb_session = (
            f"tb_upload_{cliente_elegido}"
            in st.session_state
            if cliente_elegido else False
        )
        _tiene_tb = _tiene_tb_repo or _tiene_tb_session

        if _tiene_tb and cliente_elegido:
            st.markdown(
                f"<div class='check-item check-ok'>"
                f"<span class='check-icon'>✅</span>"
                f"<span>Trial Balance ya disponible para "
                f"<b>{cliente_elegido}</b>. "
                f"Puedes subir uno nuevo para actualizarlo.</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        up_col1, up_col2 = st.columns(2)
        with up_col1:
            tb_label = (
                "Trial Balance (.xlsx) — actualizar"
                if _tiene_tb
                else "Trial Balance (.xlsx) *"
            )
            uploaded_tb = st.file_uploader(
                tb_label,
                type=["xlsx"],
                key="setup_tb",
                help=(
                    "Opcional — ya tienes TB cargado"
                    if _tiene_tb
                    else "Obligatorio para el análisis"
                ),
            )

            # TB type selector (preliminar vs final)
            tb_tipo = st.radio(
                "Tipo de TB",
                ["preliminar", "final"],
                key="setup_tb_tipo",
                horizontal=True,
                help=(
                    "Preliminar: saldos de avance. "
                    "Final: saldos definitivos al cierre."
                ),
            )

        with up_col2:
            uploaded_mayor = st.file_uploader(
                "Libro Mayor (.xlsx) — opcional",
                type=["xlsx"],
                key="setup_mayor",
            )

        if modo == "Crear cliente nuevo":
            st.markdown(
                "<div style='margin-top:1rem;'></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div class='section-header'>"
                "📋 Datos del cliente</div>",
                unsafe_allow_html=True,
            )
            st.caption(
                "Completa los datos para un análisis "
                "más preciso. Todos son opcionales "
                "excepto el nombre."
            )

            # ── Section 1: Basic data ─────────────────────────────
            st.markdown("**Datos básicos**")
            p1, p2 = st.columns(2)
            with p1:
                perfil_nombre = st.text_input(
                    "Nombre legal del cliente *",
                    placeholder="ABC Corporation S.A.",
                    key="pf_nombre",
                )
                perfil_ruc = st.text_input(
                    "RUC / NIT",
                    placeholder="1234567890001",
                    key="pf_ruc",
                )
                perfil_sector = st.selectbox(
                    "Sector",
                    [
                        "comerciales", "servicios",
                        "holding", "manufactura",
                        "financiero", "agricultura",
                        "sin_fines_de_lucro", "otro",
                    ],
                    key="pf_sector",
                )
                perfil_tipo = st.selectbox(
                    "Tipo de entidad",
                    [
                        "SOCIEDAD_ANONIMA",
                        "COMPANIA_LIMITADA",
                        "SAS", "COOPERATIVA",
                        "ONG", "PERSONA_NATURAL",
                        "otro",
                    ],
                    key="pf_tipo",
                )
            with p2:
                perfil_periodo = st.number_input(
                    "Año del encargo",
                    min_value=2020, max_value=2030,
                    value=2025, key="pf_periodo",
                )
                perfil_marco = st.selectbox(
                    "Marco referencial",
                    ["NIIF_PYMES", "NIIF_COMPLETAS", "otro"],
                    key="pf_marco",
                )
                perfil_riesgo = st.selectbox(
                    "Riesgo global estimado",
                    ["bajo", "medio", "medio_alto", "alto"],
                    key="pf_riesgo",
                )
                perfil_moneda = st.selectbox(
                    "Moneda funcional",
                    ["USD", "EUR", "COP", "PEN", "MXN", "otro"],
                    key="pf_moneda",
                )

            st.markdown("<div style='margin-top:1rem;'></div>",
                        unsafe_allow_html=True)

            # ── Section 2: Operational flags ─────────────────────
            st.markdown("**Características operativas**")
            st.caption(
                "Esta información mejora el ranking de riesgo "
                "y las recomendaciones por área."
            )
            op1, op2, op3 = st.columns(3)
            with op1:
                pf_partes_rel = st.checkbox(
                    "Tiene partes relacionadas",
                    key="pf_partes_rel",
                    help="Socios, subsidiarias, empresas vinculadas",
                )
                pf_inventarios = st.checkbox(
                    "Inventarios significativos",
                    key="pf_inventarios",
                )
                pf_cartera = st.checkbox(
                    "Cartera significativa (CxC)",
                    key="pf_cartera",
                )
            with op2:
                pf_prestamos_socios = st.checkbox(
                    "Préstamos a socios",
                    key="pf_prestamos_socios",
                )
                pf_anticipos = st.checkbox(
                    "Anticipos a proveedores",
                    key="pf_anticipos",
                )
                pf_reembolsos = st.checkbox(
                    "Reembolsos de gastos",
                    key="pf_reembolsos",
                )
            with op3:
                pf_operaciones_ext = st.checkbox(
                    "Operaciones en el exterior",
                    key="pf_operaciones_ext",
                )
                pf_primera_auditoria = st.checkbox(
                    "Primera auditoría",
                    key="pf_primera_auditoria",
                )
                pf_empleados = st.checkbox(
                    "Tiene empleados",
                    key="pf_empleados",
                    value=True,
                )

            st.markdown("<div style='margin-top:0.5rem;'></div>",
                        unsafe_allow_html=True)

            # ── Section 3: Risk flags ─────────────────────────────
            st.markdown("**Banderas de riesgo**")
            rf1, rf2 = st.columns(2)
            with rf1:
                pf_doc_debil = st.checkbox(
                    "Documentación débil",
                    key="pf_doc_debil",
                )
                pf_riesgo_tributario = st.checkbox(
                    "Riesgo tributario",
                    key="pf_riesgo_tributario",
                )
            with rf2:
                pf_ajustes_cierre = st.checkbox(
                    "Ajustes frecuentes al cierre",
                    key="pf_ajustes_cierre",
                )
                pf_negocio_marcha = st.checkbox(
                    "Riesgo negocio en marcha",
                    key="pf_negocio_marcha",
                )

            # Build complete perfil_form dict
            perfil_form = {
                "cliente": {
                    "nombre_legal": perfil_nombre or "Cliente",
                    "nombre_corto": (
                        perfil_nombre.split()[0]
                        if perfil_nombre else "Cliente"
                    ),
                    "ruc": perfil_ruc,
                    "tipo_entidad": perfil_tipo,
                    "sector": perfil_sector,
                    "moneda_funcional": perfil_moneda,
                    "pais": "Ecuador",
                    "domicilio": "",
                },
                "encargo": {
                    "anio_activo": int(perfil_periodo),
                    "marco_referencial": perfil_marco,
                    "tipo_encargo": "auditoria_externa",
                    "fase_actual": etapa_setup,
                    "primera_auditoria": pf_primera_auditoria,
                },
                "riesgo_global": {
                    "nivel": perfil_riesgo,
                    "riesgo_negocio_en_marcha": pf_negocio_marcha,
                    "requiere_enfoque_reforzado": (
                        perfil_riesgo in ["alto", "medio_alto"]
                    ),
                },
                "contexto_negocio": {
                    "tiene_partes_relacionadas": pf_partes_rel,
                    "tiene_operaciones_extranjero": pf_operaciones_ext,
                    "actividad_principal": perfil_sector,
                    "descripcion_breve_negocio": "",
                    "pertenece_a_grupo": pf_partes_rel,
                    "regulador_principal": "SUPERCIAS",
                },
                "operacion": {
                    "tiene_cartera_significativa": pf_cartera,
                    "tiene_provision_cartera": pf_cartera,
                    "tiene_inventarios_significativos": pf_inventarios,
                    "tiene_prestamos_socios": pf_prestamos_socios,
                    "tiene_anticipos_proveedores": pf_anticipos,
                    "maneja_reembolsos_gastos": pf_reembolsos,
                },
                "nomina": {
                    "tiene_empleados": pf_empleados,
                },
                "banderas_generales": {
                    "documentacion_debil": pf_doc_debil,
                    "riesgo_tributario_general": pf_riesgo_tributario,
                    "ajustes_cierre_frecuentes": pf_ajustes_cierre,
                },
                "materialidad": {
                    "estado_materialidad": "preliminar",
                    "base_utilizada": (
                        "ingresos" if perfil_sector == "servicios"
                        else "activos"
                    ),
                    "preliminar": {},
                    "final": {},
                },
                "industria_inteligente": {
                    "sector_base": perfil_sector,
                    "subtipo_negocio": perfil_sector,
                    "tags": [
                        t for t, v in [
                            ("partes_relacionadas", pf_partes_rel),
                            ("inventarios_significativos", pf_inventarios),
                            ("cartera_significativa", pf_cartera),
                            ("prestamos_socios", pf_prestamos_socios),
                            ("anticipos_proveedores", pf_anticipos),
                            ("reembolsos_gastos", pf_reembolsos),
                            ("operaciones_extranjero", pf_operaciones_ext),
                            ("tiene_empleados", pf_empleados),
                        ]
                        if v
                    ],
                },
                "tesoreria": {
                    "tiene_caja": True,
                    "usa_efectivo_intensivo": False,
                    "numero_bancos_nacionales": 1,
                },
                "notas_generales": {
                    "resumen_cliente": (
                        f"Cliente creado desde formulario. "
                        f"Sector: {perfil_sector}. "
                        f"Marco: {perfil_marco}."
                    ),
                },
                "reguladores_secundarios": ["SRI"],
            }
        else:
            # Existing client — use defaults
            perfil_nombre = cliente_elegido
            perfil_form = None

        st.markdown("<div style='margin-top:1.5rem;'></div>",
                    unsafe_allow_html=True)

        # ── Validation & Enter ────────────────────────────────
        puede_entrar = bool(
            cliente_elegido and (_tiene_tb or uploaded_tb)
        )

        if not puede_entrar:
            faltante = []
            if not cliente_elegido:
                faltante.append("seleccionar o crear un cliente")
            if not (_tiene_tb or uploaded_tb):
                faltante.append("subir el Trial Balance (.xlsx)")
            st.warning(
                "Para continuar debes: "
                + " y ".join(faltante) + "."
            )

        if st.button(
            "✅ Entrar al análisis",
            key="btn_setup_enter",
            use_container_width=True,
            type="primary",
            disabled=not puede_entrar,
        ):
            # Save everything to session state
            st.session_state["cliente_activo"] = cliente_elegido
            st.session_state["etapa_activa"] = etapa_setup
            st.session_state["auditor_nombre"] = nombre_auditor

            # Process TB
            if uploaded_tb:
                try:
                    import io
                    from analysis.lector_tb import (
                        _normalizar_columnas,
                        _mapear_columnas_canonicas,
                        _validar_tb,
                        _enriquecer_tb,
                    )

                    raw = pd.read_excel(
                        io.BytesIO(uploaded_tb.read()),
                        sheet_name=0,
                        engine="openpyxl",
                    )
                    raw = raw.dropna(how="all").reset_index(drop=True)
                    raw = _normalizar_columnas(raw)
                    raw = _mapear_columnas_canonicas(raw)
                    raw = _validar_tb(raw)
                    raw = _enriquecer_tb(raw)
                    st.session_state[
                        f"tb_upload_{cliente_elegido}"
                    ] = raw
                    st.session_state[
                        f"tb_tipo_{cliente_elegido}"
                    ] = tb_tipo
                except Exception as e:
                    st.error(f"Error procesando TB: {e}")
            elif _tiene_tb_session:
                # Keep existing, just update tipo
                st.session_state[
                    f"tb_tipo_{cliente_elegido}"
                ] = tb_tipo

            # Save perfil in session when using form
            if perfil_form is not None:
                st.session_state[
                    f"perfil_upload_{cliente_elegido}"
                ] = perfil_form

            # Save to remote persistence
            # (new client or existing one with available perfil)
            _perfil_to_save = None
            if isinstance(perfil_form, dict) and perfil_form:
                _perfil_to_save = perfil_form
            else:
                _pk = f"perfil_upload_{cliente_elegido}"
                _p_session = st.session_state.get(_pk, {})
                if isinstance(_p_session, dict) and _p_session:
                    _perfil_to_save = _p_session
                else:
                    _p_repo = safe_call(
                        leer_perfil, cliente_elegido, default={}
                    ) or {}
                    if isinstance(_p_repo, dict) and _p_repo:
                        _perfil_to_save = _p_repo

            if (
                _sheets_ok
                and guardar_cliente_sheets
                and isinstance(_perfil_to_save, dict)
                and _perfil_to_save
            ):
                _saved = safe_call(
                    guardar_cliente_sheets,
                    cliente_elegido,
                    _perfil_to_save,
                    default=False,
                )
                if _saved:
                    # Invalidate cache so new client appears
                    if "sheets_clientes_cache" in st.session_state:
                        del st.session_state[
                            "sheets_clientes_cache"
                        ]
                    st.success(
                        "✅ Cliente guardado en persistencia remota."
                    )
                else:
                    _err = safe_call(
                        obtener_ultimo_error_sheets,
                        default="",
                    ) if obtener_ultimo_error_sheets else ""
                    st.warning(
                        "⚠️ No se pudo guardar en persistencia remota. "
                        "Verifica credenciales de Supabase (o Sheets fallback)."
                    )
                    if _err:
                        st.error(f"Detalle persistencia: {_err}")

            # Process mayor
            if uploaded_mayor:
                import io

                df_mayor_up = pd.read_excel(
                    io.BytesIO(uploaded_mayor.read()),
                    sheet_name=0, engine="openpyxl",
                )
                st.session_state[
                    f"mayor_upload_{cliente_elegido}"
                ] = df_mayor_up

            # Register new client in session list
            if modo == "Crear cliente nuevo" and cliente_elegido:
                _creados = st.session_state.get(
                    "clientes_creados_sesion", []
                )
                if cliente_elegido not in _creados:
                    _creados.append(cliente_elegido)
                    st.session_state[
                        "clientes_creados_sesion"
                    ] = _creados

                # Explicit persistence on new-client creation
                _perfil_new = st.session_state.get(
                    f"perfil_upload_{cliente_elegido}", {}
                )
                if (
                    _sheets_ok
                    and guardar_cliente_sheets
                    and isinstance(_perfil_new, dict)
                    and _perfil_new
                ):
                    _saved_new = safe_call(
                        guardar_cliente_sheets,
                        cliente_elegido,
                        _perfil_new,
                        default=False,
                    )
                    if _saved_new:
                        if "sheets_clientes_cache" in st.session_state:
                            del st.session_state["sheets_clientes_cache"]
                        st.success(
                            "✅ Cliente nuevo guardado en persistencia remota."
                        )

            st.session_state["app_screen"] = "dashboard"
            st.rerun()

    # Back button
    st.markdown("<div style='margin-top:1rem;'></div>",
                unsafe_allow_html=True)
    if st.button("← Volver", key="btn_setup_back"):
        st.session_state["app_screen"] = "welcome"
        st.rerun()


# ══ Screen router ══════════════════════════════════════════════
if "app_screen" not in st.session_state:
    st.session_state["app_screen"] = "welcome"

if st.session_state["app_screen"] == "welcome":
    render_welcome_screen()
    st.stop()

if st.session_state["app_screen"] == "setup":
    render_setup_screen(_get_clientes_dinamicos())
    st.stop()

# ── From here: dashboard screen ────────────────────────────────
# Override sidebar defaults with setup values
if "cliente_activo" in st.session_state:
    _cliente_override = st.session_state["cliente_activo"]
if "etapa_activa" in st.session_state:
    _etapa_override = st.session_state["etapa_activa"]


# ============================================================
# Sidebar
# ============================================================
st.sidebar.title("Configuracion")

clientes_disponibles = _get_clientes_dinamicos()

if not clientes_disponibles:
    st.sidebar.warning("No hay clientes disponibles en data/clientes/. Usando modo carga manual.")
    clientes_disponibles = ["cliente_demo"]

# Default to setup values if coming from setup screen
_default_cliente = st.session_state.get(
    "cliente_activo", clientes_disponibles[0]
    if clientes_disponibles else ""
)
_default_etapa = st.session_state.get(
    "etapa_activa", "planificacion"
)

_clientes_opts = list(clientes_disponibles)
if _default_cliente and _default_cliente not in _clientes_opts:
    _clientes_opts = [_default_cliente] + _clientes_opts

cliente_seleccionado = st.sidebar.selectbox(
    "Seleccionar cliente",
    options=_clientes_opts,
    index=_clientes_opts.index(_default_cliente)
    if _default_cliente in _clientes_opts else 0,
)

etapa_seleccionada = st.sidebar.selectbox(
    "Etapa",
    options=["planificacion", "ejecucion", "cierre"],
    index=["planificacion", "ejecucion", "cierre"].index(
        _default_etapa
    ),
)

if st.sidebar.button("Cargar cliente", width="stretch"):
    st.session_state.cliente_cargado = cliente_seleccionado

if st.sidebar.button(
    "← Volver al inicio",
    key="btn_back_home",
    use_container_width=True,
):
    st.session_state["app_screen"] = "welcome"
    st.rerun()

auditor = st.session_state.get("auditor_nombre", "")
if auditor:
    st.sidebar.caption(f"👤 Auditor: {auditor}")

st.sidebar.divider()
st.sidebar.markdown("**📂 Cargar archivos del cliente**")

# TB uploader
uploaded_tb = st.sidebar.file_uploader(
    "Trial Balance (.xlsx)",
    type=["xlsx"],
    key="uploader_tb",
    help="Sube el tb.xlsx del cliente seleccionado",
)
if uploaded_tb is not None:
    try:
        import io
        from analysis.lector_tb import (
            _normalizar_columnas,
            _mapear_columnas_canonicas,
            _validar_tb,
            _enriquecer_tb,
        )

        raw = pd.read_excel(
            io.BytesIO(uploaded_tb.read()),
            sheet_name=0,
            engine="openpyxl",
        )
        raw = raw.dropna(how="all").reset_index(drop=True)
        raw = _normalizar_columnas(raw)
        raw = _mapear_columnas_canonicas(raw)
        raw = _validar_tb(raw)
        raw = _enriquecer_tb(raw)
        st.session_state[
            f"tb_upload_{cliente_seleccionado}"
        ] = raw
        st.sidebar.success(
            f"✅ TB cargado: {len(raw)} filas"
        )
    except Exception as e:
        st.sidebar.error(f"Error procesando TB: {e}")

# Perfil uploader
uploaded_perfil = st.sidebar.file_uploader(
    "Perfil del cliente (.yaml)",
    type=["yaml", "yml"],
    key="uploader_perfil",
    help="Sube el perfil.yaml del cliente (opcional)",
)
if uploaded_perfil is not None:
    try:
        import yaml as _yaml

        perfil_data = _yaml.safe_load(
            uploaded_perfil.read().decode("utf-8")
        )
        st.session_state[
            f"perfil_upload_{cliente_seleccionado}"
        ] = perfil_data
        st.sidebar.success("✅ Perfil cargado")
    except Exception as e:
        st.sidebar.error(f"Error leyendo perfil: {e}")

# Mayor uploader (optional)
uploaded_mayor = st.sidebar.file_uploader(
    "Libro Mayor (.xlsx) — opcional",
    type=["xlsx"],
    key="uploader_mayor",
    help="Sube el mayor.xlsx del cliente (opcional)",
)
if uploaded_mayor is not None:
    try:
        import io

        df_mayor_up = pd.read_excel(
            io.BytesIO(uploaded_mayor.read()),
            sheet_name=0,
            engine="openpyxl",
        )
        st.session_state[
            f"mayor_upload_{cliente_seleccionado}"
        ] = df_mayor_up
        st.sidebar.success(
            f"✅ Mayor cargado: {len(df_mayor_up)} movimientos"
        )
    except Exception as e:
        st.sidebar.error(f"Error leyendo mayor: {e}")

if "cliente_cargado" not in st.session_state:
    st.session_state.cliente_cargado = cliente_seleccionado

cliente = st.session_state.cliente_cargado


# ============================================================
# Carga de datos base
# ============================================================
# ── Perfil: uploaded file takes priority ──────────────────
_perfil_key = f"perfil_upload_{cliente}"
_perfil_key_active = f"perfil_upload_{st.session_state.get('cliente_activo', '')}"

_perfil_from_session = None
for _k in [_perfil_key, _perfil_key_active]:
    if _k in st.session_state and isinstance(
        st.session_state.get(_k), dict
    ) and st.session_state[_k]:
        _perfil_from_session = st.session_state[_k]
        break

if _perfil_from_session is not None:
    perfil = _perfil_from_session
else:
    perfil = safe_call(leer_perfil, cliente, default={}) or {}

# Populate module cache so internal services find perfil
if isinstance(perfil, dict) and perfil:
    try:
        from domain.services.leer_perfil import set_perfil_cache
        set_perfil_cache(cliente, perfil)
    except Exception:
        pass

datos_clave = safe_call(cached_datos_clave, cliente, default={}) or {}
# ── TB: uploaded file takes priority ──────────────────────
_tb_key = f"tb_upload_{cliente}"
_tb_key_active = f"tb_upload_{st.session_state.get('cliente_activo', '')}"

_tb_from_session = None
for _k in [_tb_key, _tb_key_active]:
    if _k in st.session_state and isinstance(
        st.session_state.get(_k), pd.DataFrame
    ) and not st.session_state[_k].empty:
        _tb_from_session = st.session_state[_k]
        break

if _tb_from_session is not None:
    tb = _tb_from_session
else:
    tb = safe_call(leer_tb, cliente, default=pd.DataFrame())

# Populate module cache so internal services
# (ranking, materialidad, contexto) can find the TB
if isinstance(tb, pd.DataFrame) and not tb.empty:
    try:
        from analysis.lector_tb import set_tb_cache
        set_tb_cache(cliente, tb)
    except Exception:
        pass

# Debug indicator (remove after confirming fix)
if isinstance(tb, pd.DataFrame) and not tb.empty:
    print(f"[OK] TB activo para {cliente}: {len(tb)} filas")
else:
    print(f"[WARN] Sin TB para {cliente} — keys disponibles: "
          f"{[k for k in st.session_state.keys() if 'tb_upload' in str(k)]}")

# Pass the already-loaded tb DataFrame directly
# so uploaded TBs are used, not just file-based ones
if isinstance(tb, pd.DataFrame) and not tb.empty:
    from analysis.lector_tb import obtener_resumen_tb as _get_resumen
    try:
        resumen_tb = _get_resumen(cliente, df=tb) or {}
    except TypeError:
        # Fallback if signature doesn't match yet
        resumen_tb = safe_call(
            obtener_resumen_tb, cliente, default={}
        ) or {}
else:
    resumen_tb = safe_call(
        obtener_resumen_tb, cliente, default={}
    ) or {}
diag_tb = safe_call(obtener_diagnostico_tb, cliente, default={}) or {}
ranking_areas = safe_call(cached_ranking_areas, cliente, default=pd.DataFrame())
indicadores = safe_call(cached_indicadores, cliente, default={}) or {}
variaciones = safe_call(cached_variaciones, cliente, default=pd.DataFrame())

# Build lightweight ranking/variaciones from uploaded TB when available
if _tb_from_session is not None and isinstance(tb, pd.DataFrame) and not tb.empty:
    try:
        tb_cols = {str(c).strip().lower(): c for c in tb.columns}
        col_ls = next((tb_cols[k] for k in ["ls", "l/s", "l_s"] if k in tb_cols), None)
        col_nombre = next((tb_cols[k] for k in ["agrupacion", "nombre cuenta", "nombre_cuenta", "nombre"] if k in tb_cols), None)
        col_s24 = next((tb_cols[k] for k in ["saldo 2024", "saldo_2024"] if k in tb_cols), None)
        col_s25 = next((tb_cols[k] for k in ["saldo 2025", "saldo_2025", "saldo preliminar", "saldo_preliminar"] if k in tb_cols), None)

        if col_ls and col_s25:
            tmp = tb.copy()
            tmp["_ls"] = tmp[col_ls].astype(str).str.strip().str.replace(r"\.0+$", "", regex=True)
            tmp["_s25"] = pd.to_numeric(tmp[col_s25], errors="coerce").fillna(0.0)
            tmp["_s24"] = pd.to_numeric(tmp[col_s24], errors="coerce").fillna(0.0) if col_s24 else 0.0
            tmp["_nombre"] = tmp[col_nombre].astype(str) if col_nombre else tmp["_ls"]

            # Variaciones
            tmp["_impacto"] = tmp["_s25"] - tmp["_s24"]
            variaciones = tmp[["_ls", "_nombre", "_s25", "_impacto"]].copy()
            variaciones.columns = ["codigo", "nombre", "saldo", "impacto"]
            variaciones["impacto_abs"] = variaciones["impacto"].abs()
            variaciones = variaciones.sort_values("impacto_abs", ascending=False).drop(columns=["impacto_abs"])

            # Ranking por LS
            grp = tmp.groupby("_ls", as_index=False).agg(
                saldo_total=("_s25", "sum"),
                impacto_total=("_impacto", "sum"),
            )
            name_map = tmp.groupby("_ls")["_nombre"].first().to_dict()
            grp["area"] = grp["_ls"]
            grp["nombre"] = grp["_ls"].map(name_map).astype(str).str[:50]
            grp["con_saldo"] = grp["saldo_total"].abs() > 0.01
            if grp["saldo_total"].abs().max() > 0:
                grp["score_riesgo"] = (
                    grp["saldo_total"].abs() / grp["saldo_total"].abs().max() * 100
                ).round(1)
            else:
                grp["score_riesgo"] = 0.0
            grp["prioridad"] = grp["score_riesgo"].apply(
                lambda x: "alta" if x >= 70 else "media" if x >= 40 else "baja"
            )
            ranking_areas = grp[["area", "nombre", "score_riesgo", "prioridad", "saldo_total", "con_saldo"]].sort_values(
                "score_riesgo", ascending=False
            )
    except Exception:
        pass

# ── Mayor: uploaded file takes priority ───────────────────
_mayor_key = f"mayor_upload_{cliente}"
if _mayor_key in st.session_state and isinstance(
    st.session_state[_mayor_key], pd.DataFrame
):
    df_mayor = st.session_state[_mayor_key]
elif mayor_existe and safe_call(
    mayor_existe, cliente, default=False
):
    df_mayor = safe_call(
        obtener_mayor_cliente, cliente, default=None
    )
else:
    df_mayor = None

if isinstance(diag_tb, dict):
    rows_loaded = int(diag_tb.get("rows_loaded", 0) or 0)
    rows_saldo_no_cero = int(diag_tb.get("rows_saldo_no_cero", 0) or 0)
    if rows_loaded > 0 and rows_saldo_no_cero == 0:
        st.warning(
            "Se cargó el TB pero no se detectaron saldos no cero. Revisar mapeo de columnas para este cliente."
        )
    elif rows_loaded == 0:
        st.warning("No se pudieron cargar filas del TB para el cliente seleccionado.")

# Selected area — driven by ranking click,
# not sidebar dropdown
_area_key = f"selected_area_{cliente}"
if _area_key not in st.session_state:
    # Default to top area from ranking
    if (
        isinstance(ranking_areas, pd.DataFrame)
        and not ranking_areas.empty
        and "area" in ranking_areas.columns
    ):
        _mask = pd.Series([True]*len(ranking_areas))
        if "con_saldo" in ranking_areas.columns:
            _mask = ranking_areas[
                "con_saldo"
            ].astype(bool)
        _top = ranking_areas[_mask]
        if not _top.empty:
            st.session_state[_area_key] = str(
                _top.iloc[0]["area"]
            )
        else:
            st.session_state[_area_key] = "14"
    else:
        st.session_state[_area_key] = "14"

selected_area_code = st.session_state[_area_key]

if st.sidebar.button("Limpiar cache", width="stretch"):
    st.cache_data.clear()
    st.rerun()

# RAG status
st.sidebar.divider()
try:
    from infra.rag.vector_store import esta_indexado, total_indexado
    if esta_indexado():
        st.sidebar.caption(
            f"Base normativa: {total_indexado()} chunks indexados"
        )
    else:
        st.sidebar.caption("Base normativa: no indexada")
        st.sidebar.caption("Ejecuta: python -m app.cli_commands indexar")
except Exception:
    pass

render_sidebar_summary(cliente, perfil, datos_clave, ranking_areas)
# Remote persistence connection indicator
st.sidebar.divider()
_sheets_ready = bool(
    _sheets_ok and safe_call(
        sheets_disponible, default=False
    )
)
if _sheets_ready:
    st.sidebar.caption("☁️ Persistencia remota conectada")
else:
    st.sidebar.caption("💾 Modo local (sin persistencia)")
    if _sheets_import_error:
        st.sidebar.caption(f"Sheets import: {_sheets_import_error}")

if st.sidebar.button(
    "🔎 Probar persistencia",
    key="btn_test_sheets",
    use_container_width=True,
):
    if not _sheets_ok or not callable(diagnosticar_sheets):
        st.sidebar.warning("⚠️ Diagnóstico avanzado no disponible.")
        _rows_basic = safe_call(cargar_clientes_sheets, default=[]) or []
        _err_basic = safe_call(
            obtener_ultimo_error_sheets, default=""
        ) if callable(obtener_ultimo_error_sheets) else ""
        st.sidebar.caption(
            f"Básico: rows={len(_rows_basic)} | "
            f"sheets_ok={_sheets_ok}"
        )
        if _sheets_import_error:
            st.sidebar.error(f"ImportError: {_sheets_import_error}")
        if _err_basic:
            st.sidebar.error(f"Detalle: {_err_basic}")
        # Do not stop app render
    else:
        _diag = safe_call(diagnosticar_sheets, default={}) or {}
        _rows = safe_call(cargar_clientes_sheets, default=[]) or []
        if _diag.get("ok"):
            st.sidebar.success(
                f"Conexión OK. Clientes remotos: {len(_rows)}"
            )
            if _diag.get("spreadsheet_title"):
                st.sidebar.caption(
                    f"Sheet: {_diag.get('spreadsheet_title')}"
                )
        else:
            st.sidebar.error("❌ Falla en diagnóstico de persistencia.")
            st.sidebar.write(
                f"auth={_diag.get('auth_ok')} | "
                f"open={_diag.get('open_ok')} | "
                f"sheet={_diag.get('sheet_ok')} | "
                f"read={_diag.get('read_ok')} | "
                f"write={_diag.get('write_ok')}"
            )
            _err = _diag.get("error", "") or safe_call(
                obtener_ultimo_error_sheets,
                default="",
            )
            if _err:
                st.sidebar.error(f"Detalle: {_err}")
            _cfg = safe_call(
                diagnosticar_config_supabase, default={}
            ) if callable(diagnosticar_config_supabase) else {}
            if _cfg:
                st.sidebar.caption(
                    "Keys detectadas (nombres): "
                    f"{_cfg.get('secrets_keys', [])}"
                )
                st.sidebar.caption(
                    "Env detectadas: "
                    f"{_cfg.get('env_keys', [])}"
                )
                st.sidebar.caption(
                    f"has_url={_cfg.get('has_url')} | "
                    f"has_key={_cfg.get('has_key')}"
                )


# ============================================================
# Header principal
# ============================================================
st.markdown("""
    <div class="socioai-header">
        <div class="socioai-logo">📊</div>
        <div>
            <h1>SocioAI</h1>
            <p>Plataforma Inteligente de Auditoría Financiera</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cliente", normalize_text(get_first(datos_clave, ["nombre"], perfil.get("cliente", {}).get("nombre_legal", "N/A"))) or "N/A")
c2.metric("RUC", normalize_text(get_first(datos_clave, ["ruc"], perfil.get("cliente", {}).get("ruc", "N/A"))) or "N/A")
c3.metric("Sector", normalize_text(get_first(datos_clave, ["sector"], perfil.get("cliente", {}).get("sector", "N/A"))) or "N/A")
c4.metric("Moneda", normalize_text(get_first(datos_clave, ["moneda"], perfil.get("cliente", {}).get("moneda_funcional", "N/A"))) or "N/A")

st.divider()


# ============================================================
# Tabs principales
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "🎯 Áreas",
    "🤖 Inteligencia IA",
    "📋 Datos",
])


def _calcular_estado_encargo(
    ranking_areas: pd.DataFrame | None,
    cliente: str,
) -> dict[str, Any]:
    """
    Calculates engagement completion status
    based on area states in session_state and ranking.
    """
    if not isinstance(ranking_areas, pd.DataFrame) \
            or ranking_areas.empty:
        return {
            "areas": [],
            "pct_completado": 0,
            "total": 0,
            "completas": 0,
            "en_proceso": 0,
            "no_iniciadas": 0,
        }

    mask = pd.Series([True] * len(ranking_areas))
    if "con_saldo" in ranking_areas.columns:
        mask = ranking_areas["con_saldo"].astype(bool)
    df_areas = ranking_areas[mask].copy()

    areas_estado = []
    for _, row in df_areas.iterrows():
        codigo = str(row.get("area", "")).strip()
        nombre_a = str(row.get("nombre", codigo))
        score = float(row.get("score_riesgo", 0) or 0)
        prior = str(row.get("prioridad", "baja")).lower()

        # Check state from session
        _estado_key = f"area_estado_{cliente}_{codigo}"
        _estado_yaml = st.session_state.get(
            _estado_key, ""
        )

        # Also check saved YAML state
        try:
            from domain.services.estado_area_yaml import (
                cargar_estado_area,
            )
            _yaml = cargar_estado_area(cliente, codigo)
            _estado_yaml = (
                _yaml.get("estado_area", "") or _estado_yaml
            )
        except Exception:
            pass

        # Determine semaphore
        _estados_completos = {
            "cerrada", "lista_para_cierre", "completada"
        }
        _estados_proceso = {
            "en_revision", "en_ejecucion",
            "pendiente_cliente", "en_proceso",
        }

        if _estado_yaml in _estados_completos:
            semaforo = "completa"
            emoji = "🟢"
        elif _estado_yaml in _estados_proceso:
            semaforo = "en_proceso"
            emoji = "🟡"
        else:
            semaforo = "no_iniciada"
            emoji = "🔴"

        areas_estado.append({
            "codigo": codigo,
            "nombre": nombre_a,
            "score": score,
            "prioridad": prior,
            "semaforo": semaforo,
            "emoji": emoji,
            "estado_txt": _estado_yaml or "No iniciada",
        })

    total = len(areas_estado)
    completas = sum(
        1 for a in areas_estado if a["semaforo"] == "completa"
    )
    en_proceso = sum(
        1 for a in areas_estado
        if a["semaforo"] == "en_proceso"
    )
    no_iniciadas = total - completas - en_proceso

    pct = int((completas / total * 100)) if total > 0 else 0

    return {
        "areas": areas_estado,
        "pct_completado": pct,
        "total": total,
        "completas": completas,
        "en_proceso": en_proceso,
        "no_iniciadas": no_iniciadas,
    }


with tab1:
    # ── KPI Row ──────────────────────────────────────────────
    activo = resumen_tb.get("ACTIVO", 0)
    pasivo = resumen_tb.get("PASIVO", 0)
    patrimonio = resumen_tb.get("PATRIMONIO", 0)
    n_alto = indicadores.get("areas_alto_riesgo", 0)
    n_medio = indicadores.get("areas_medio_riesgo", 0)
    n_bajo = indicadores.get("areas_bajo_riesgo", 0)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card kpi-info">
            <div class="kpi-label">Activos Totales</div>
            <div class="kpi-value">${float(activo):,.0f}</div>
            <div class="kpi-sub">Balance general</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-card kpi-info">
            <div class="kpi-label">Patrimonio</div>
            <div class="kpi-value">${float(patrimonio):,.0f}</div>
            <div class="kpi-sub">Vs pasivos ${float(pasivo):,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        color_riesgo = "kpi-alto" if n_alto > 0 else "kpi-bajo"
        st.markdown(f"""
        <div class="kpi-card {color_riesgo}">
            <div class="kpi-label">Áreas Alto Riesgo</div>
            <div class="kpi-value">{n_alto}</div>
            <div class="kpi-sub">{n_medio} medio · {n_bajo} bajo</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        tb_count = int(tb.shape[0]) if isinstance(tb, pd.DataFrame) else 0
        st.markdown(f"""
        <div class="kpi-card kpi-info">
            <div class="kpi-label">Cuentas en TB</div>
            <div class="kpi-value">{tb_count}</div>
            <div class="kpi-sub">Trial Balance cargado</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Distribución de Riesgo por Áreas</div>",
                unsafe_allow_html=True)

    col_pie, col_top = st.columns([1, 2])
    with col_pie:
        try:
            import plotly.express as px
            if n_alto + n_medio + n_bajo > 0:
                fig_pie = px.pie(
                    names=["Alto", "Medio", "Bajo"],
                    values=[n_alto, n_medio, n_bajo],
                    color_discrete_map={
                        "Alto": "#DE350B",
                        "Medio": "#FF8B00",
                        "Bajo": "#00875A",
                    },
                    hole=0.5,
                )
                fig_pie.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font_color="#172B4D",
                    height=250,
                    margin=dict(l=0, r=0, t=20, b=0),
                    legend=dict(orientation="h", y=-0.15),
                    showlegend=True,
                )
                fig_pie.update_traces(
                    textposition="inside",
                    textinfo="percent",
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        except Exception:
            st.metric("Alto", n_alto)

    with col_top:
        st.markdown("<div class='section-header'>Top Áreas por Score</div>",
                    unsafe_allow_html=True)
        if isinstance(ranking_areas, pd.DataFrame) and not ranking_areas.empty:
            for _, row in ranking_areas.head(5).iterrows():
                score = float(row.get("score_riesgo", 0))
                nombre_a = str(row.get("nombre", ""))[:30]
                area_c = str(row.get("area", ""))
                prior = str(row.get("prioridad", "")).upper()
                color_badge = (
                    "#DE350B" if score >= 70
                    else "#FF8B00" if score >= 40
                    else "#00875A"
                )
                bar_w = min(int(score), 100)
                st.markdown(f"""
                <div class="kpi-card" style="padding:0.8rem 1rem; margin-bottom:0.4rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:700; color:#003366;">{area_c} — {nombre_a}</span>
                        <span style="background:{color_badge}; color:white; padding:2px 10px;
                               border-radius:12px; font-size:0.75rem; font-weight:700;">
                            {score:.1f}
                        </span>
                    </div>
                    <div style="background:#F4F5F7; border-radius:4px; height:6px;
                                margin-top:6px; overflow:hidden;">
                        <div style="background:{color_badge}; width:{bar_w}%;
                                    height:100%; border-radius:4px;"></div>
                    </div>
                    <div style="color:#6B778C; font-size:0.72rem; margin-top:4px;">
                        Prioridad: {prior}
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Sin datos de ranking disponibles.")

    # ── Data source indicator ─────────────────────────────────
    _tb_loaded = (
        isinstance(tb, pd.DataFrame) and not tb.empty
    )
    _perfil_loaded = (
        isinstance(perfil, dict) and bool(perfil)
    )
    _from_upload = f"tb_upload_{cliente}" in st.session_state

    src1, src2, src3 = st.columns(3)
    with src1:
        if _tb_loaded and _from_upload:
            st.success("✅ TB cargado desde archivo")
        elif _tb_loaded:
            st.success("✅ TB cargado desde repo")
        else:
            st.warning(
                "⚠️ Sin TB — sube el archivo en el sidebar"
            )
    with src2:
        if _perfil_loaded:
            st.success("✅ Perfil disponible")
        else:
            st.info("ℹ️ Sin perfil — usando defaults")
    with src3:
        if df_mayor is not None:
            st.success("✅ Libro Mayor disponible")
        else:
            st.info("ℹ️ Sin Mayor cargado")

    # ── Client info card ─────────────────────────────────────
    st.markdown("<div class='section-header'>Información del Encargo</div>",
                unsafe_allow_html=True)
    nombre_c = normalize_text(get_first(
        datos_clave, ["nombre"],
        perfil.get("cliente", {}).get("nombre_legal", "N/A")
    ))
    sector_c = normalize_text(get_first(
        datos_clave, ["sector"],
        perfil.get("cliente", {}).get("sector", "N/A")
    ))
    periodo_c = normalize_text(get_first(
        datos_clave, ["periodo"],
        str(perfil.get("encargo", {}).get("anio_activo", "N/A"))
    ))
    marco_c = normalize_text(get_first(
        datos_clave, ["marco_referencial"],
        perfil.get("encargo", {}).get("marco_referencial", "N/A")
    ))
    riesgo_g = normalize_text(
        perfil.get("riesgo_global", {}).get("nivel", "N/A")
    )
    color_rg = (
        "#DE350B" if "alto" in riesgo_g
        else "#FF8B00" if "medio" in riesgo_g
        else "#00875A"
    )
    st.markdown(f"""
    <div class="kpi-card kpi-info" style="padding:1rem 1.4rem;">
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr 1fr; gap:1rem;">
            <div><div class="kpi-label">Cliente</div>
                 <div style="font-weight:700; color:#003366;">{nombre_c}</div></div>
            <div><div class="kpi-label">Sector</div>
                 <div style="font-weight:600;">{sector_c}</div></div>
            <div><div class="kpi-label">Período</div>
                 <div style="font-weight:600;">{periodo_c}</div></div>
            <div><div class="kpi-label">Marco</div>
                 <div style="font-weight:600;">{marco_c}</div></div>
            <div><div class="kpi-label">Riesgo Global</div>
                 <div style="font-weight:700; color:{color_rg};">
                     {riesgo_g.upper()}</div></div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Engagement Status ─────────────────────────────────
    st.markdown(
        "<div class='section-header'>"
        "Estado del Encargo</div>",
        unsafe_allow_html=True,
    )

    _estado_enc = _calcular_estado_encargo(
        ranking_areas, cliente
    )

    # Progress bar
    _pct = _estado_enc["pct_completado"]
    _total = _estado_enc["total"]
    _completas = _estado_enc["completas"]
    _proceso = _estado_enc["en_proceso"]
    _no_ini = _estado_enc["no_iniciadas"]

    prog_color = (
        "#00875A" if _pct >= 80
        else "#FF8B00" if _pct >= 40
        else "#DE350B"
    )

    st.markdown(
        f"""
        <div class="kpi-card kpi-info"
             style="padding:1rem 1.4rem;">
          <div style="display:flex;
                      justify-content:space-between;
                      align-items:center;
                      margin-bottom:0.6rem;">
            <span style="font-weight:700;
                         color:#003366;
                         font-size:1rem;">
              Progreso del encargo
            </span>
            <span style="font-size:1.4rem;
                         font-weight:900;
                         color:{prog_color};">
              {_pct}%
            </span>
          </div>
          <div style="background:#F4F5F7;
                      border-radius:6px;
                      height:12px;
                      overflow:hidden;
                      margin-bottom:0.8rem;">
            <div style="background:{prog_color};
                        width:{_pct}%;
                        height:100%;
                        border-radius:6px;
                        transition:width 0.5s;">
            </div>
          </div>
          <div style="display:grid;
                      grid-template-columns:1fr 1fr 1fr;
                      gap:0.5rem; text-align:center;">
            <div>
              <div style="font-size:1.4rem;">🟢</div>
              <div style="font-weight:700;
                          color:#006644;
                          font-size:1.1rem;">
                {_completas}
              </div>
              <div style="color:#6B778C;
                          font-size:0.75rem;">
                Completas
              </div>
            </div>
            <div>
              <div style="font-size:1.4rem;">🟡</div>
              <div style="font-weight:700;
                          color:#974F0C;
                          font-size:1.1rem;">
                {_proceso}
              </div>
              <div style="color:#6B778C;
                          font-size:0.75rem;">
                En proceso
              </div>
            </div>
            <div>
              <div style="font-size:1.4rem;">🔴</div>
              <div style="font-weight:700;
                          color:#BF2600;
                          font-size:1.1rem;">
                {_no_ini}
              </div>
              <div style="color:#6B778C;
                          font-size:0.75rem;">
                No iniciadas
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Semaphore table by area
    if _estado_enc["areas"]:
        st.markdown(
            "<div style='margin-top:0.8rem;'></div>",
            unsafe_allow_html=True,
        )
        for area_e in sorted(
            _estado_enc["areas"],
            key=lambda x: x["score"],
            reverse=True,
        ):
            _color_bg = {
                "completa": "#E3FCEF",
                "en_proceso": "#FFFAE6",
                "no_iniciada": "#FFEBE6",
            }.get(area_e["semaforo"], "#F4F5F7")

            _color_txt = {
                "completa": "#006644",
                "en_proceso": "#974F0C",
                "no_iniciada": "#BF2600",
            }.get(area_e["semaforo"], "#172B4D")

            st.markdown(
                f"""
                <div style="background:{_color_bg};
                            border-radius:8px;
                            padding:0.5rem 1rem;
                            margin-bottom:0.3rem;
                            display:flex;
                            justify-content:space-between;
                            align-items:center;">
                  <div>
                    <span style="font-weight:700;
                                 color:#003366;">
                      {area_e['emoji']}
                      {area_e['codigo']} —
                      {area_e['nombre'][:35]}
                    </span>
                    <span style="color:#6B778C;
                                 font-size:0.78rem;
                                 margin-left:8px;">
                      Score: {area_e['score']:.1f}
                    </span>
                  </div>
                  <span style="color:{_color_txt};
                               font-size:0.8rem;
                               font-weight:700;">
                    {area_e['estado_txt'].replace('_',' ').title()}
                  </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── PDF Export ────────────────────────────────────────────
    st.markdown(
        "<div class='section-header'>Exportar Reporte</div>",
        unsafe_allow_html=True,
    )
    col_pdf, col_info = st.columns([1, 3])
    with col_pdf:
        if st.button(
            "📄 Generar PDF",
            key="btn_gen_pdf",
            use_container_width=True,
            type="primary",
        ):
            with st.spinner("Generando reporte PDF..."):
                try:
                    from domain.services.pdf_report_service import (
                        generar_pdf_resumen,
                    )
                    pdf_bytes = generar_pdf_resumen(
                        cliente=cliente,
                        perfil=perfil,
                        resumen_tb=resumen_tb,
                        ranking_areas=ranking_areas,
                        variaciones=variaciones,
                        datos_clave=datos_clave,
                    )
                    nombre_archivo = (
                        f"SocioAI_{cliente}_"
                        f"{datetime.now().strftime('%Y%m%d')}.pdf"
                    )
                    st.session_state["pdf_bytes"] = pdf_bytes
                    st.session_state["pdf_filename"] = nombre_archivo
                    st.success("✅ PDF listo para descargar.")
                except Exception as e:
                    st.error(f"Error generando PDF: {e}")

    with col_info:
        st.caption(
            "El reporte incluye: balance general, ranking de áreas "
            "por riesgo, top variaciones y estado de cierre."
        )

    if st.session_state.get("pdf_bytes"):
        st.download_button(
            label="⬇️ Descargar PDF",
            data=st.session_state["pdf_bytes"],
            file_name=st.session_state.get(
                "pdf_filename", f"SocioAI_{cliente}.pdf"
            ),
            mime="application/pdf",
            key="btn_dl_pdf",
            use_container_width=False,
        )


def _render_cierre_cards(ws: dict[str, Any]) -> None:
    """Cierre tab with visual status cards instead of raw text."""
    from app.views.view_area import _closure_readiness

    lista_para_cerrar, razones = _closure_readiness(ws)
    cobertura = float(ws.get("coverage", 0) or 0)
    hallazgos_count = int(ws.get("hallazgos_count", 0) or 0)
    pending_count = int(ws.get("pending_count", 0) or 0)
    nivel_riesgo = normalize_text(
        ws.get("riesgo", ws.get("area_summary", {}).get("nivel_riesgo", ""))
    )
    calidad = (
        ws.get("calidad_metodologia", {})
        if isinstance(ws.get("calidad_metodologia", {}), dict)
        else {}
    )
    alertas_criticas = int(
        calidad.get("resumen", {}).get("alertas_criticas", 0) or 0
    )

    # ── Estado general ────────────────────────────────────────
    if lista_para_cerrar:
        badge_cls = "badge-ok"
        badge_txt = "✅ Lista para cerrar"
        st.markdown(
            f"<span class='status-badge {badge_cls}'>"
            f"{badge_txt}</span>",
            unsafe_allow_html=True,
        )
    else:
        badge_cls = "badge-fail"
        badge_txt = "⛔ No lista para cerrar"
        st.markdown(
            f"<span class='status-badge {badge_cls}'>"
            f"{badge_txt}</span>",
            unsafe_allow_html=True,
        )

    st.markdown("")  # spacer

    # ── Checklist cards ───────────────────────────────────────
    st.markdown(
        "<div class='section-header'>Checklist de cierre</div>",
        unsafe_allow_html=True,
    )

    checks = [
        (
            cobertura >= 80,
            f"Cobertura de aseveraciones: {cobertura:.1f}%",
            "Cobertura insuficiente (mínimo 80%)",
        ),
        (
            hallazgos_count == 0,
            "Sin hallazgos abiertos",
            f"{hallazgos_count} hallazgo(s) abierto(s) pendiente(s)",
        ),
        (
            pending_count == 0,
            "Todos los procedimientos ejecutados",
            f"{pending_count} procedimiento(s) pendiente(s)",
        ),
        (
            alertas_criticas == 0,
            "Sin alertas metodológicas críticas",
            f"{alertas_criticas} alerta(s) crítica(s) de calidad",
        ),
        (
            nivel_riesgo not in {"alto", "medio_alto"},
            "Nivel de riesgo controlado",
            f"Riesgo del área: {nivel_riesgo.upper()}",
        ),
    ]

    for ok, msg_ok, msg_fail in checks:
        if ok:
            st.markdown(
                f"<div class='check-item check-ok'>"
                f"<span class='check-icon'>✅</span>"
                f"<span>{msg_ok}</span></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='check-item check-fail'>"
                f"<span class='check-icon'>⚠️</span>"
                f"<span>{msg_fail}</span></div>",
                unsafe_allow_html=True,
            )

    # ── Acciones recomendadas ─────────────────────────────────
    acciones = []
    if pending_count > 0:
        acciones.append("Completar procedimientos pendientes con evidencia.")
    if hallazgos_count > 0:
        acciones.append(
            "Resolver hallazgos abiertos o documentar plan de remediación."
        )
    if cobertura < 80:
        acciones.append(
            "Fortalecer cobertura en aseveraciones débiles o no cubiertas."
        )
    if alertas_criticas > 0:
        acciones.append(
            "Resolver alertas metodológicas críticas (ver tab Calidad)."
        )
    if not acciones:
        acciones.append(
            "Documentar conclusión final y referencias cruzadas de evidencia."
        )

    if acciones:
        st.markdown(
            "<div class='section-header' style='margin-top:1rem;'>"
            "Próximas acciones</div>",
            unsafe_allow_html=True,
        )
        for a in acciones:
            st.markdown(
                f"<div class='check-item check-warn'>"
                f"<span class='check-icon'>→</span>"
                f"<span>{a}</span></div>",
                unsafe_allow_html=True,
            )

    # ── Seguimiento manual (colapsado) ────────────────────────
    with st.expander("📝 Registrar estado y conclusión", expanded=False):
        render_cierre_tab(ws)


def _render_requerimientos_tab(ws: dict[str, Any]) -> None:
    """Requerimientos de auditoría por área y aseveración."""
    st.markdown(
        "<div class='section-header'>"
        "📎 Guía de Requerimientos</div>",
        unsafe_allow_html=True,
    )

    codigo_ls = str(ws.get("codigo_ls", ""))
    area_name = ws.get("area_name", f"Área {codigo_ls}")

    try:
        from domain.services.requerimientos_service import (
            obtener_requerimientos_area,
            construir_checklist,
        )
        area_req = obtener_requerimientos_area(codigo_ls)
    except Exception:
        area_req = {}

    if not area_req:
        st.info(
            f"No hay guía de requerimientos configurada "
            f"para {area_name} (L/S {codigo_ls}). "
            f"Puedes agregarla en "
            f"data/catalogos/requerimientos_por_area.yaml"
        )
        return

    asev_data = area_req.get("aseveraciones", {})
    if not asev_data:
        st.info("Sin aseveraciones configuradas para esta área.")
        return

    # ── Filter by aseveracion ─────────────────────────────────
    asev_options = list(asev_data.keys())
    sel_asev = st.multiselect(
        "Filtrar por aseveración",
        options=asev_options,
        default=asev_options,
        key=f"req_asev_{codigo_ls}",
    )

    st.divider()

    # ── Render by type ────────────────────────────────────────
    tipo_icons = {
        "documento": "📄",
        "pregunta": "❓",
        "procedimiento": "🔧",
    }
    tipo_labels = {
        "documento": "Documentos a solicitar",
        "pregunta": "Preguntas clave al cliente",
        "procedimiento": "Procedimientos sugeridos",
    }
    tipo_colors = {
        "documento": "#EBF2FF",
        "pregunta": "#FFFAE6",
        "procedimiento": "#E3FCEF",
    }
    tipo_border = {
        "documento": "#0066CC",
        "pregunta": "#FF8B00",
        "procedimiento": "#00875A",
    }

    # Group by aseveracion first
    for asev in sel_asev:
        if asev not in asev_data:
            continue

        contenido = asev_data[asev]
        if not isinstance(contenido, dict):
            continue

        st.markdown(
            f"<div style='font-size:1rem; font-weight:700;"
            f"color:#003366; margin:1rem 0 0.5rem 0;"
            f"border-bottom:2px solid #DFE1E6;"
            f"padding-bottom:4px;'>"
            f"Aseveración: {asev.title()}</div>",
            unsafe_allow_html=True,
        )

        for tipo in ["documento", "pregunta", "procedimiento"]:
            # Handle key variants
            key_map = {
                "documento": "documentos",
                "pregunta": "preguntas",
                "procedimiento": "procedimientos",
            }
            items = contenido.get(key_map[tipo], [])

            if not items:
                continue

            st.markdown(
                f"<div style='font-size:0.85rem;"
                f"font-weight:700; color:#6B778C;"
                f"margin:0.6rem 0 0.3rem 0;'>"
                f"{tipo_icons[tipo]} "
                f"{tipo_labels[tipo]}</div>",
                unsafe_allow_html=True,
            )

            for item in items:
                st.markdown(
                    f"<div style='background:"
                    f"{tipo_colors[tipo]};"
                    f"border-left:3px solid "
                    f"{tipo_border[tipo]};"
                    f"border-radius:0 6px 6px 0;"
                    f"padding:0.4rem 0.8rem;"
                    f"margin-bottom:0.3rem;"
                    f"font-size:0.88rem;'>"
                    f"{item}</div>",
                    unsafe_allow_html=True,
                )

    st.divider()

    # ── Download checklist ────────────────────────────────────
    st.markdown(
        "<div class='section-header'>Exportar checklist</div>",
        unsafe_allow_html=True,
    )

    try:
        from domain.services.requerimientos_service import (
            construir_checklist,
        )
        checklist = construir_checklist(
            codigo_ls,
            aseveraciones=sel_asev,
        )
    except Exception:
        checklist = []

    if checklist:
        c1, c2 = st.columns(2)

        with c1:
            # CSV download
            import io as _io
            df_check = pd.DataFrame(checklist)
            df_check.columns = [
                "Aseveración", "Tipo",
                "Descripción", "Completado",
            ]
            # Generate and cache CSV in session_state
            _csv_key = f"req_csv_data_{codigo_ls}"
            if _csv_key not in st.session_state:
                _csv_buf = _io.StringIO()
                df_check.to_csv(
                    _csv_buf, index=False, encoding="utf-8"
                )
                st.session_state[_csv_key] = (
                    _csv_buf.getvalue().encode("utf-8")
                )

            st.download_button(
                "⬇️ Descargar checklist (.csv)",
                data=st.session_state[_csv_key],
                file_name=(
                    f"requerimientos_{codigo_ls}_"
                    f"{area_name[:15].replace(' ','_')}.csv"
                ),
                mime="text/csv",
                key=f"dl_req_csv_{codigo_ls}",
                use_container_width=True,
            )

        with c2:
            # PDF download
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.units import cm
                from reportlab.lib import colors
                from reportlab.platypus import (
                    SimpleDocTemplate, Paragraph,
                    Spacer, Table, TableStyle,
                )
                from reportlab.lib.styles import (
                    getSampleStyleSheet, ParagraphStyle,
                )
                import io as _io2

                # Generate and cache PDF in session_state
                _pdf_key = f"req_pdf_data_{codigo_ls}"
                if _pdf_key not in st.session_state:
                    buf = _io2.BytesIO()
                    doc = SimpleDocTemplate(
                        buf, pagesize=A4,
                        leftMargin=2*cm, rightMargin=2*cm,
                        topMargin=2*cm, bottomMargin=2*cm,
                    )
                    NAVY = colors.Color(0/255, 51/255, 102/255)

                    story = []
                    story.append(Paragraph(
                        "Requerimientos de Auditoría",
                        ParagraphStyle(
                            "title", fontSize=16,
                            fontName="Helvetica-Bold",
                            textColor=NAVY, spaceAfter=4,
                        ),
                    ))
                    story.append(Paragraph(
                        f"{area_name} · L/S {codigo_ls}",
                        ParagraphStyle(
                            "sub", fontSize=10,
                            textColor=colors.Color(0.44,0.47,0.52),
                            spaceAfter=16,
                        ),
                    ))

                    tipo_color_pdf = {
                        "documento": colors.Color(0.85,0.91,1.0),
                        "pregunta": colors.Color(1.0,0.98,0.9),
                        "procedimiento": colors.Color(0.88,0.99,0.93),
                    }

                    for item in checklist:
                        asev = str(item["aseveracion"]).title()
                        tipo = str(item["tipo"])
                        desc = str(item["descripcion"])
                        icon = {
                            "documento": "📄",
                            "pregunta": "❓",
                            "procedimiento": "🔧",
                        }.get(tipo, "•")

                        row = [[
                            Paragraph(
                                f"<b>{asev}</b> · {icon} {tipo.title()}",
                                ParagraphStyle(
                                    "lbl", fontSize=8,
                                    textColor=NAVY,
                                ),
                            ),
                            Paragraph(
                                desc,
                                ParagraphStyle(
                                    "desc", fontSize=9,
                                    leading=12,
                                ),
                            ),
                            Paragraph(
                                "☐",
                                ParagraphStyle(
                                    "chk", fontSize=12,
                                    alignment=1,
                                ),
                            ),
                        ]]
                        t = Table(row, colWidths=[
                            4*cm, 11*cm, 1*cm
                        ])
                        t.setStyle(TableStyle([
                            ("BACKGROUND", (0,0), (-1,-1),
                             tipo_color_pdf.get(
                                 tipo,
                                 colors.white,
                             )),
                            ("TOPPADDING", (0,0),(-1,-1), 5),
                            ("BOTTOMPADDING",(0,0),(-1,-1),5),
                            ("LEFTPADDING",(0,0),(-1,-1),6),
                            ("GRID",(0,0),(-1,-1),0.3,
                             colors.Color(0.88,0.88,0.90)),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 0.15*cm))

                    doc.build(story)
                    buf.seek(0)
                    st.session_state[_pdf_key] = buf.read()

                st.download_button(
                    "⬇️ Descargar checklist (.pdf)",
                    data=st.session_state[_pdf_key],
                    file_name=(
                        f"requerimientos_{codigo_ls}.pdf"
                    ),
                    mime="application/pdf",
                    key=f"dl_req_pdf_{codigo_ls}",
                    use_container_width=True,
                )
            except Exception as e:
                st.caption(f"PDF no disponible: {e}")
    else:
        st.info("Sin items para exportar con los filtros actuales.")


with tab2:
    # ── Build area list ───────────────────────────────────
    _area_key = f"selected_area_{cliente}"
    _selected = st.session_state.get(_area_key, "")

    # Get areas with saldo from ranking
    _areas_list: list[dict] = []
    if (
        isinstance(ranking_areas, pd.DataFrame)
        and not ranking_areas.empty
    ):
        _needed = {"area", "nombre", "score_riesgo"}
        if _needed.issubset(set(ranking_areas.columns)):
            _mask2 = pd.Series(
                [True] * len(ranking_areas)
            )
            if "con_saldo" in ranking_areas.columns:
                _mask2 = ranking_areas[
                    "con_saldo"
                ].astype(bool)
            for _, _row in ranking_areas[
                _mask2
            ].iterrows():
                _areas_list.append({
                    "codigo": str(
                        _row.get("area", "")
                    ).strip(),
                    "nombre": str(
                        _row.get("nombre", "")
                    ),
                    "score": float(
                        _row.get("score_riesgo", 0) or 0
                    ),
                    "prioridad": str(
                        _row.get("prioridad", "baja")
                    ).upper(),
                    "saldo": float(
                        _row.get("saldo_total", 0) or 0
                    ),
                })

    if not _areas_list:
        st.info(
            "Sube un Trial Balance para ver las áreas."
        )
    else:
        col_rank2, col_ws2 = st.columns([1, 2])

        with col_rank2:
            st.markdown(
                "<div class='section-header'>"
                "Ranking de Áreas</div>",
                unsafe_allow_html=True,
            )
            st.caption(
                "Haz clic en un área para verla "
                "en detalle →"
            )

            for _area in _areas_list:
                _cod = _area["codigo"]
                _score = _area["score"]
                _is_sel = (_cod == _selected)

                # Color by score
                _sc = (
                    "#DE350B" if _score >= 70
                    else "#FF8B00" if _score >= 40
                    else "#00875A"
                )
                # Card style
                _border = (
                    "3px solid #003366"
                    if _is_sel
                    else "1px solid #DFE1E6"
                )
                _bg = "#EBF2FF" if _is_sel else "#FFFFFF"
                _bar_w = min(int(_score), 100)

                st.markdown(
                    f"""
                    <div style="background:{_bg};
                        border:{_border};
                        border-radius:10px 10px 0 0;
                        padding:0.7rem 1rem 0.4rem 1rem;
                        margin-bottom:0;">
                      <div style="display:flex;
                          justify-content:space-between;
                          align-items:center;">
                        <div>
                          <span style="font-weight:700;
                              color:#003366;
                              font-size:0.9rem;">
                            {_cod}
                          </span>
                          <span style="color:#6B778C;
                              font-size:0.82rem;
                              margin-left:6px;">
                            {_area['nombre'][:22]}
                          </span>
                        </div>
                        <span style="background:{_sc};
                            color:white;
                            padding:2px 8px;
                            border-radius:10px;
                            font-size:0.75rem;
                            font-weight:700;">
                          {_score:.0f}
                        </span>
                      </div>
                      <div style="background:#F4F5F7;
                          border-radius:3px;
                          height:4px;
                          margin-top:5px;
                          overflow:hidden;">
                        <div style="background:{_sc};
                            width:{_bar_w}%;
                            height:100%;
                            border-radius:3px;">
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Button sits flush below the card
                st.markdown(
                    "<div style='margin-top:0; "
                    "margin-bottom:0.5rem;'>",
                    unsafe_allow_html=True,
                )
                _btn = st.button(
                    "▶ Abrir área" if not _is_sel
                    else "✅ Área activa",
                    key=f"sel_area_{cliente}_{_cod}",
                    use_container_width=True,
                    type="primary" if _is_sel else "secondary",
                )
                st.markdown("</div>", unsafe_allow_html=True)
                if _btn:
                    st.session_state[_area_key] = _cod
                    st.rerun()

        with col_ws2:
            # Always read fresh from session after rerun
            selected_area_code = st.session_state.get(
                _area_key,
                _areas_list[0]["codigo"] if _areas_list else "14",
            )
            # Update global selected_area_code for other tabs
            st.session_state[f"selected_area_{cliente}"] = \
                selected_area_code

            ws = prepare_area_workspace(
                cliente=cliente,
                etapa=etapa_seleccionada,
                codigo_ls=selected_area_code,
                perfil=perfil,
                tb=tb,
                variaciones=variaciones,
                ranking_areas=ranking_areas,
            )
            render_area_header(ws)
            render_area_kpis(ws)

            inner_tabs = st.tabs([
                "📋 Resumen",
                "⚙️ Trabajo",
                "🔍 Calidad",
                "🏁 Cierre",
                "📎 Requerimientos",
            ])
            with inner_tabs[0]:
                render_contexto_tab(ws)
                with st.expander(
                    "📌 Briefing del área",
                    expanded=False,
                ):
                    render_briefing_tab(ws)
                with st.expander(
                    "📂 Procedimientos",
                    expanded=False,
                ):
                    render_procedimientos_tab(ws)
            with inner_tabs[1]:
                left_w, right_w = st.columns(2)
                with left_w:
                    render_hallazgos_tab(ws)
                with right_w:
                    render_seguimiento_tab(ws, cliente)
                st.divider()
                with st.expander(
                    "🕐 Historial de cambios",
                    expanded=False,
                ):
                    render_historial_tab(ws, cliente)
            with inner_tabs[2]:
                with st.expander(
                    "🔬 Cobertura de aseveraciones",
                    expanded=True,
                ):
                    render_cobertura_tab(ws)
                with st.expander(
                    "✅ Revisión de calidad",
                    expanded=False,
                ):
                    render_calidad_tab(ws)
            with inner_tabs[3]:
                _render_cierre_cards(ws)
            with inner_tabs[4]:
                _render_requerimientos_tab(ws)


with tab3:
    # ── API key check ─────────────────────────────────────
    try:
        import streamlit as st
        _api_key_ok = bool(
            st.secrets.get("DEEPSEEK_API_KEY", "")
            or __import__("os").environ.get(
                "DEEPSEEK_API_KEY", ""
            )
        )
    except Exception:
        _api_key_ok = bool(
            __import__("os").environ.get(
                "DEEPSEEK_API_KEY", ""
            )
        )

    if not _api_key_ok:
        st.warning(
            "⚠️ **Sin API key configurada.** "
            "Para usar la IA, agrega `DEEPSEEK_API_KEY` "
            "en Streamlit Cloud → tu app → "
            "Settings → Secrets.",
            icon="🔑",
        )

    ia_tab1, ia_tab2, ia_tab3 = st.tabs([
        "💡 Briefing", "📝 Programa", "💬 Chat"
    ])

    with ia_tab1:
        st.markdown("<div class='section-header'>Briefing de Área</div>",
                    unsafe_allow_html=True)
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            area_briefing = st.text_input(
                "Área L/S",
                value=selected_area_code or "14",
                key="briefing_area_input",
            )
        with col_b2:
            etapa_briefing = st.selectbox(
                "Etapa",
                ["planificacion", "ejecucion", "cierre"],
                key="briefing_etapa_input",
            )

        if st.button(
            "🤖 Generar Briefing con IA",
            key="btn_briefing_ia",
            type="primary",
        ):
            _key_check = _get_deepseek_key() if callable(
                globals().get("_get_deepseek_key")
            ) else ""
            if not _key_check:
                st.warning(
                    "⚠️ Sin DEEPSEEK_API_KEY. "
                    "Agrégala en Streamlit Cloud → "
                    "Settings → Secrets."
                )
            else:
                with st.spinner("Generando briefing..."):
                    try:
                        # Inject uploaded TB into the
                        # module-level reader so briefing
                        # functions find data
                        _tb_for_brief = tb if (
                            isinstance(tb, pd.DataFrame)
                            and not tb.empty
                        ) else None

                        if _tb_for_brief is None:
                            st.warning(
                                "Sube el Trial Balance "
                                "primero para un briefing "
                                "con datos reales."
                            )
                        else:
                            from llm.briefing_llm import (
                                generar_briefing_area_llm,
                            )
                            # Build minimal context for briefing
                            _perfil_brief = perfil if (
                                isinstance(perfil, dict)
                                and perfil
                            ) else {}

                            briefing_txt = (
                                generar_briefing_area_llm(
                                    nombre_cliente=cliente,
                                    codigo_ls=area_briefing,
                                    etapa=etapa_briefing,
                                )
                            )
                            if briefing_txt:
                                st.markdown(
                                    "<div class='ai-response'>"
                                    + briefing_txt.replace(
                                        "\n", "<br>"
                                    )
                                    + "</div>",
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.info(
                                    "El modelo no devolvió "
                                    "respuesta. Verifica la "
                                    "API key."
                                )
                    except Exception as e:
                        st.error(f"Error en briefing: {e}")

        st.caption(
            "Requiere DEEPSEEK_API_KEY en "
            "Streamlit Cloud → Settings → Secrets."
        )

    with ia_tab2:
        st.markdown("<div class='section-header'>Programa de Auditoría</div>",
                    unsafe_allow_html=True)
        from domain.services.programa_ia_service import generar_programa_auditoria_ia
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            area_prog = st.text_input(
                "Código área L/S",
                value=selected_area_code or "14",
                key="prog_area",
            )
        with col_p2:
            etapa_prog = st.selectbox(
                "Etapa",
                ["planificacion", "ejecucion", "cierre"],
                key="prog_etapa",
            )
        if st.button("Generar Programa", key="btn_prog_ia"):
            with st.spinner("Generando programa..."):
                prog = generar_programa_auditoria_ia(cliente, area_prog, etapa_prog)
            with st.expander("Ver programa completo", expanded=True):
                st.markdown(prog)
            st.download_button(
                "Descargar (.md)",
                data=prog,
                file_name=f"programa_{cliente}_{area_prog}.md",
                mime="text/markdown",
                key="dl_prog",
            )

    with ia_tab3:
        st.markdown(
            "<div class='section-header'>"
            "🤖 Asistente SocioAI</div>",
            unsafe_allow_html=True,
        )

        try:
            from llm.asistente_llm import (
                construir_contexto_sistema,
                generar_respuesta_asistente,
                SUGERENCIAS_INICIALES,
            )
            _asistente_ok = True
        except Exception:
            _asistente_ok = False

        if not _asistente_ok:
            st.error("Error cargando el asistente.")
        else:
            # Build system context
            _sistema = construir_contexto_sistema(
                cliente=cliente,
                perfil=perfil,
                resumen_tb=resumen_tb,
                ranking_areas=ranking_areas,
                variaciones=variaciones,
                etapa=etapa_seleccionada,
            )

            # ── Perfil completeness check ─────────────────
            _perfil_score = 0
            _perfil_missing = []
            _cliente_info = perfil.get("cliente", {}) if isinstance(perfil, dict) else {}
            _checks = [
                ("cliente.nombre_legal",
                 bool(_cliente_info.get("nombre_legal"))),
                ("sector",
                 bool(_cliente_info.get("sector"))),
                ("partes_relacionadas",
                 "tiene_partes_relacionadas" in str(perfil)),
                ("operacion",
                 bool(perfil.get("operacion")
                      if isinstance(perfil, dict) else False)),
                ("materialidad",
                 bool(perfil.get("materialidad", {})
                      .get("preliminar", {})
                      if isinstance(perfil, dict) else False)),
            ]
            for campo, ok in _checks:
                if ok:
                    _perfil_score += 1
                else:
                    _perfil_missing.append(campo)

            _pct_perfil = int(
                (_perfil_score / len(_checks)) * 100
            )

            if _pct_perfil < 80:
                st.markdown(
                    f"<div class='check-item check-warn'>"
                    f"<span class='check-icon'>💡</span>"
                    f"<span>El perfil del cliente está "
                    f"<b>{_pct_perfil}% completo</b>. "
                    f"Puedes pedirme que complete la "
                    f"información faltante: "
                    f"<i>{', '.join(_perfil_missing)}</i>"
                    f"</span></div>",
                    unsafe_allow_html=True,
                )

            # Chat history key per client
            _hist_key = f"chat_history_{cliente}"
            if _hist_key not in st.session_state:
                st.session_state[_hist_key] = []

            # Show suggestion chips if no history
            if not st.session_state[_hist_key]:
                st.markdown(
                    "<div style='color:#6B778C; "
                    "font-size:0.88rem; "
                    "margin-bottom:0.8rem;'>"
                    "💡 Sugerencias para empezar:"
                    "</div>",
                    unsafe_allow_html=True,
                )
                chip_cols = st.columns(3)
                for i, sug in enumerate(
                    SUGERENCIAS_INICIALES[:6]
                ):
                    with chip_cols[i % 3]:
                        if st.button(
                            sug,
                            key=f"chip_{i}_{cliente}",
                            use_container_width=True,
                        ):
                            st.session_state[
                                _hist_key
                            ].append({
                                "role": "user",
                                "content": sug,
                            })
                            with st.spinner(
                                "Consultando..."
                            ):
                                resp = (
                                    generar_respuesta_asistente(
                                        st.session_state[
                                            _hist_key
                                        ],
                                        _sistema,
                                    )
                                )
                            st.session_state[
                                _hist_key
                            ].append({
                                "role": "assistant",
                                "content": resp,
                            })
                            st.rerun()

            # Render chat history
            chat_container = st.container()
            with chat_container:
                for msg in st.session_state[_hist_key]:
                    if msg["role"] == "user":
                        st.markdown(
                            f"<div style='background:#EBF2FF;"
                            f"border-radius:12px 12px 2px 12px;"
                            f"padding:0.7rem 1rem;"
                            f"margin:0.4rem 0 0.4rem 20%;"
                            f"font-size:0.9rem;'>"
                            f"👤 {msg['content']}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"<div style='background:#F4F5F7;"
                            f"border-left:3px solid #003366;"
                            f"border-radius:0 12px 12px 0;"
                            f"padding:0.7rem 1rem;"
                            f"margin:0.4rem 20% 0.4rem 0;"
                            f"font-size:0.9rem;'>"
                            f"🤖 {msg['content']}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

            # Input
            st.markdown(
                "<div style='margin-top:1rem;'></div>",
                unsafe_allow_html=True,
            )
            inp_col, btn_col = st.columns([5, 1])
            with inp_col:
                user_input = st.text_input(
                    "Escribe tu pregunta",
                    key=f"chat_input_{cliente}",
                    placeholder=(
                        "ej: ¿Qué área tiene mayor riesgo?"
                    ),
                    label_visibility="collapsed",
                )
            with btn_col:
                send = st.button(
                    "Enviar →",
                    key=f"chat_send_{cliente}",
                    use_container_width=True,
                    type="primary",
                )

            if send and user_input.strip():
                st.session_state[_hist_key].append({
                    "role": "user",
                    "content": user_input.strip(),
                })
                with st.spinner("SocioAI está pensando..."):
                    resp = generar_respuesta_asistente(
                        st.session_state[_hist_key],
                        _sistema,
                    )
                st.session_state[_hist_key].append({
                    "role": "assistant",
                    "content": resp,
                })
                st.rerun()

            # Clear chat button
            if st.session_state[_hist_key]:
                if st.button(
                    "🗑️ Limpiar conversación",
                    key=f"clear_chat_{cliente}",
                ):
                    st.session_state[_hist_key] = []
                    st.rerun()


def _build_chart_data(
    tb: pd.DataFrame | None,
    ranking_areas: pd.DataFrame | None,
    resumen_tb: dict,
) -> dict[str, Any]:
    """
    Prepares data structures for the 3 financial charts.
    Returns a dict with keys: areas_bar, balance_stack, riesgo_line.
    Returns empty dicts per key if data is insufficient.
    """
    result = {
        "areas_bar": {},
        "balance_stack": {},
        "riesgo_line": {},
    }

    # ── Chart 1: Evolución por área (2024 vs 2025) ────────────
    if (
        isinstance(tb, pd.DataFrame)
        and not tb.empty
        and "saldo_2024" in tb.columns
        and "saldo_2025" in tb.columns
        and isinstance(ranking_areas, pd.DataFrame)
        and not ranking_areas.empty
        and "area" in ranking_areas.columns
        and "con_saldo" in ranking_areas.columns
    ):
        # Only areas with real balance, top 8 by score
        df_rank = ranking_areas.copy()
        if "score_riesgo" in df_rank.columns:
            df_rank = df_rank.sort_values("score_riesgo", ascending=False)

        present = df_rank[df_rank["con_saldo"].astype(bool)].head(8)

        nombres_areas = []
        vals_2024 = []
        vals_2025 = []

        ls_col = next(
            (c for c in ["ls", "l/s", "l_s"] if c in tb.columns), None
        )

        for _, row in present.iterrows():
            codigo = str(row.get("area", "")).strip()
            nombre = str(row.get("nombre", codigo))[:20]

            if ls_col:
                mask = tb[ls_col].astype(str).str.strip() == codigo
                sub = tb[mask]
            else:
                sub = tb[tb["codigo"].astype(str).str.startswith(codigo)]

            s24 = abs(float(
                pd.to_numeric(sub["saldo_2024"], errors="coerce")
                .fillna(0).sum()
            ))
            s25 = abs(float(
                pd.to_numeric(sub["saldo_2025"], errors="coerce")
                .fillna(0).sum()
            ))

            if s24 > 0 or s25 > 0:
                nombres_areas.append(f"{codigo}\n{nombre}")
                vals_2024.append(s24)
                vals_2025.append(s25)

        if nombres_areas:
            result["areas_bar"] = {
                "nombres": nombres_areas,
                "vals_2024": vals_2024,
                "vals_2025": vals_2025,
            }

    # ── Chart 2: Composición del balance ─────────────────────
    activo = abs(float(resumen_tb.get("ACTIVO", 0) or 0))
    pasivo = abs(float(resumen_tb.get("PASIVO", 0) or 0))
    patrimonio = abs(float(resumen_tb.get("PATRIMONIO", 0) or 0))
    ingresos = abs(float(resumen_tb.get("INGRESOS", 0) or 0))
    gastos = abs(float(resumen_tb.get("GASTOS", 0) or 0))

    if activo + pasivo + patrimonio > 0:
        result["balance_stack"] = {
            "activo": activo,
            "pasivo": pasivo,
            "patrimonio": patrimonio,
            "ingresos": ingresos,
            "gastos": gastos,
        }

    # ── Chart 3: Riesgo por área (2024 estimado vs 2025) ──────
    # Since we only have 2 periods, estimate 2024 score from
    # saldo_2024 proportions vs saldo_2025
    if (
        isinstance(ranking_areas, pd.DataFrame)
        and not ranking_areas.empty
        and "score_riesgo" in ranking_areas.columns
        and result["areas_bar"]
    ):
        nombres_r = []
        scores_r = []

        df_r = ranking_areas.copy()
        if "score_riesgo" in df_r.columns:
            df_r = df_r.sort_values("score_riesgo", ascending=False)

        present_r = df_r[df_r["con_saldo"].astype(bool)].head(6)

        bar = result["areas_bar"]
        for _, row in present_r.iterrows():
            codigo = str(row.get("area", "")).strip()
            nombre = str(row.get("nombre", codigo))[:15]
            score_25 = float(row.get("score_riesgo", 0) or 0)

            # Estimate 2024 score based on saldo ratio
            idx = next(
                (i for i, n in enumerate(bar["nombres"])
                 if n.startswith(codigo)), None
            )
            if idx is not None and bar["vals_2025"][idx] > 0:
                ratio = bar["vals_2024"][idx] / bar["vals_2025"][idx]
                score_24 = round(score_25 * ratio * 0.9, 1)
            else:
                score_24 = round(score_25 * 0.85, 1)

            nombres_r.append(f"{codigo} {nombre}")
            scores_r.append((score_24, score_25))

        if nombres_r:
            result["riesgo_line"] = {
                "nombres": nombres_r,
                "scores": scores_r,
            }

    return result


with tab4:
    d_tab1, d_tab2, d_tab3, d_tab4, d_tab5 = st.tabs([
        "📈 Variaciones", "🔢 Trial Balance",
        "📊 Análisis Financiero", "🗂️ Hallazgos",
        "📒 Mayor",
    ])

    with d_tab1:
        st.markdown("<div class='section-header'>Variaciones Significativas</div>",
                    unsafe_allow_html=True)
        resumen_var = safe_call(resumen_variaciones, cliente, default={}) or {}
        v1, v2, v3 = st.columns(3)
        v1.metric("Cuentas con variación",
                  resumen_var.get("total_cuentas_variacion", 0))
        v2.metric("Mayor variación",
                  fmt_money(resumen_var.get("mayor_variacion", 0)))
        v3.metric("Suma variaciones",
                  fmt_money(resumen_var.get("suma_variaciones", 0)))
        if isinstance(variaciones, pd.DataFrame) and not variaciones.empty:
            cols_var = [c for c in ["codigo", "nombre", "saldo", "impacto"]
                       if c in variaciones.columns]
            show_var = variaciones[cols_var].head(15).copy() if cols_var \
                       else variaciones.head(15).copy()
            if "saldo" in show_var.columns:
                show_var["saldo"] = show_var["saldo"].apply(fmt_money)
            if "impacto" in show_var.columns:
                show_var["impacto"] = show_var["impacto"].apply(fmt_money)
            st.dataframe(show_var, use_container_width=True, hide_index=True)
        else:
            st.info("Sin variaciones significativas detectadas.")

    with d_tab2:
        st.markdown("<div class='section-header'>Trial Balance</div>",
                    unsafe_allow_html=True)
        if not isinstance(tb, pd.DataFrame) or tb.empty:
            st.error("No se pudo cargar el trial balance.")
        else:
            tb_filtrado = tb.copy()
            if "tipo_cuenta" in tb_filtrado.columns:
                tipos = sorted([str(x) for x in
                               tb_filtrado["tipo_cuenta"].dropna().unique()])
                sel_tipos = st.multiselect(
                    "Filtrar por tipo", options=tipos, default=tipos
                )
                if sel_tipos:
                    tb_filtrado = tb_filtrado[
                        tb_filtrado["tipo_cuenta"].astype(str).isin(sel_tipos)
                    ]
            st.dataframe(tb_filtrado, use_container_width=True, hide_index=True)
            num_col = next(
                (c for c in ["saldo", "saldo_2025", "saldo_actual"]
                 if c in tb_filtrado.columns), None
            )
            if num_col:
                vals = pd.to_numeric(
                    tb_filtrado[num_col], errors="coerce"
                ).fillna(0)
                cc1, cc2, cc3 = st.columns(3)
                cc1.metric("Cuentas", len(tb_filtrado))
                cc2.metric("Suma", fmt_money(vals.sum()))
                cc3.metric("Mayor saldo", fmt_money(vals.max()))

    with d_tab3:
        st.markdown(
            "<div class='section-header'>Análisis Financiero</div>",
            unsafe_allow_html=True,
        )

        chart_data = _build_chart_data(tb, ranking_areas, resumen_tb)

        try:
            import plotly.graph_objects as go

            # ── Chart 1: Evolución 2024 vs 2025 por área ─────
            bar_d = chart_data.get("areas_bar", {})
            if bar_d:
                st.markdown("**Evolución de saldo por área · 2024 vs 2025**")
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(
                    name="2024",
                    x=bar_d["nombres"],
                    y=bar_d["vals_2024"],
                    marker_color="#A8C4E0",
                    text=[f"${v:,.0f}" for v in bar_d["vals_2024"]],
                    textposition="outside",
                    textfont=dict(size=10),
                ))
                fig_bar.add_trace(go.Bar(
                    name="2025",
                    x=bar_d["nombres"],
                    y=bar_d["vals_2025"],
                    marker_color="#003366",
                    text=[f"${v:,.0f}" for v in bar_d["vals_2025"]],
                    textposition="outside",
                    textfont=dict(size=10),
                ))
                fig_bar.update_layout(
                    barmode="group",
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font=dict(color="#172B4D", size=11),
                    height=340,
                    margin=dict(l=10, r=10, t=30, b=60),
                    legend=dict(
                        orientation="h", y=1.1, x=0.5,
                        xanchor="center"
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor="#F4F5F7",
                        tickformat="$,.0f",
                    ),
                    xaxis=dict(tickangle=-20),
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info(
                    "Sin datos comparativos 2024/2025. "
                    "Verificar columnas saldo_2024 y saldo_2025 en el TB."
                )

            st.divider()

            col_left, col_right = st.columns(2)

            # ── Chart 2: Composición del balance ─────────────
            with col_left:
                bal_d = chart_data.get("balance_stack", {})
                if bal_d:
                    st.markdown("**Composición del balance**")
                    categorias = []
                    valores = []
                    colores = []

                    mapping = [
                        ("Activo", bal_d["activo"], "#003366"),
                        ("Pasivo", bal_d["pasivo"], "#DE350B"),
                        ("Patrimonio", bal_d["patrimonio"], "#00875A"),
                        ("Ingresos", bal_d["ingresos"], "#0066CC"),
                        ("Gastos", bal_d["gastos"], "#FF8B00"),
                    ]
                    for label, val, color in mapping:
                        if val > 0:
                            categorias.append(label)
                            valores.append(val)
                            colores.append(color)

                    if categorias:
                        fig_stack = go.Figure(go.Bar(
                            x=categorias,
                            y=valores,
                            marker_color=colores,
                            text=[f"${v:,.0f}" for v in valores],
                            textposition="outside",
                            textfont=dict(size=10),
                        ))
                        fig_stack.update_layout(
                            plot_bgcolor="white",
                            paper_bgcolor="white",
                            font=dict(color="#172B4D", size=11),
                            height=300,
                            margin=dict(l=10, r=10, t=20, b=20),
                            yaxis=dict(
                                showgrid=True,
                                gridcolor="#F4F5F7",
                                tickformat="$,.0f",
                            ),
                            showlegend=False,
                        )
                        st.plotly_chart(
                            fig_stack, use_container_width=True
                        )
                else:
                    st.info("Sin datos de balance.")

            # ── Chart 3: Tendencia de riesgo ──────────────────
            with col_right:
                riesgo_d = chart_data.get("riesgo_line", {})
                if riesgo_d:
                    st.markdown("**Tendencia de score de riesgo por área**")
                    fig_line = go.Figure()

                    periodos = ["2024 (est.)", "2025"]
                    colores_line = [
                        "#003366", "#0066CC", "#DE350B",
                        "#00875A", "#FF8B00", "#6554C0",
                    ]

                    for i, (nombre, (s24, s25)) in enumerate(
                        zip(
                            riesgo_d["nombres"],
                            riesgo_d["scores"],
                        )
                    ):
                        color_l = colores_line[i % len(colores_line)]
                        fig_line.add_trace(go.Scatter(
                            x=periodos,
                            y=[s24, s25],
                            mode="lines+markers+text",
                            name=nombre,
                            line=dict(color=color_l, width=2),
                            marker=dict(size=8, color=color_l),
                            text=[f"{s24:.0f}", f"{s25:.0f}"],
                            textposition="top center",
                            textfont=dict(size=9),
                        ))

                    fig_line.update_layout(
                        plot_bgcolor="white",
                        paper_bgcolor="white",
                        font=dict(color="#172B4D", size=11),
                        height=300,
                        margin=dict(l=10, r=10, t=20, b=20),
                        legend=dict(
                            font=dict(size=9),
                            orientation="v",
                            x=1.01,
                        ),
                        yaxis=dict(
                            showgrid=True,
                            gridcolor="#F4F5F7",
                            range=[0, 100],
                            title="Score",
                        ),
                        xaxis=dict(title="Período"),
                    )
                    st.plotly_chart(
                        fig_line, use_container_width=True
                    )
                else:
                    st.info("Sin datos de tendencia de riesgo.")

        except Exception as e:
            st.warning(f"Error generando gráficos: {e}")

        st.divider()

        # ── Ratios y benchmark (existing, keep below charts) ──
        from analysis.ratios import resumen_ratios
        from analysis.benchmark import resumen_benchmark

        col_r, col_b = st.columns(2)
        with col_r:
            st.markdown("**Ratios financieros**")
            ratios_data = resumen_ratios(cliente)
            if ratios_data:
                df_ratios = pd.DataFrame(ratios_data)
                show_r = [
                    c for c in ["ratio", "valor", "interpretacion"]
                    if c in df_ratios.columns
                ]
                st.dataframe(
                    df_ratios[show_r],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Sin datos de ratios.")
        with col_b:
            st.markdown("**Benchmark sectorial**")
            bench = resumen_benchmark(cliente)
            if bench.get("total", 0) > 0:
                bb1, bb2, bb3 = st.columns(3)
                bb1.metric("OK", bench["ok"])
                bb2.metric("Alerta", bench["alerta"])
                bb3.metric("Crítico", bench["critico"])
            else:
                st.info("Sin benchmark disponible.")

    with d_tab4:
        st.markdown("<div class='section-header'>Gestión de Hallazgos</div>",
                    unsafe_allow_html=True)
        from domain.services.hallazgos_service import (
            cargar_hallazgos_gestion, crear_hallazgo,
            actualizar_estado_hallazgo, resumen_hallazgos,
        )
        from domain.services.export_service import (
            exportar_hallazgos_excel, exportar_resumen_txt
        )
        res_h = resumen_hallazgos(cliente)
        hh1, hh2, hh3, hh4 = st.columns(4)
        hh1.metric("Total", res_h["total"])
        hh2.metric("Abiertos", res_h["abiertos"])
        hh3.metric("Cerrados", res_h["cerrados"])
        hh4.metric("Alto riesgo", res_h["alto_riesgo_abiertos"])
        with st.expander("Registrar nuevo hallazgo"):
            ca, cb = st.columns(2)
            with ca:
                di = st.text_area("Descripción", key="h_desc")
                ai_input = st.text_input("Área L/S", key="h_area")
            with cb:
                asv = st.text_input("Afirmación", key="h_asev")
                niv = st.selectbox("Nivel", ["alto","medio","bajo"],
                                   key="h_nivel")
                resp = st.text_input("Responsable", key="h_resp")
            if st.button("Guardar hallazgo", key="h_save"):
                if di and ai_input:
                    nuevo_h = crear_hallazgo(
                        cliente, ai_input, di, asv, niv, resp
                    )
                    st.success(f"Hallazgo {nuevo_h['id']} creado.")
                    st.rerun()
        todos_h = cargar_hallazgos_gestion(cliente)
        if todos_h:
            filtro_h = st.selectbox(
                "Filtrar", ["todos","abierto","cerrado"], key="h_filtro"
            )
            lista_h = todos_h if filtro_h == "todos" else [
                h for h in todos_h if h.get("estado") == filtro_h
            ]
            for h in lista_h:
                ic = {"alto":"🔴","medio":"🟡","bajo":"🟢"}.get(
                    h.get("nivel",""), "⚪"
                )
                with st.expander(
                    f"{ic} {h.get('id')} | {h.get('codigo_area')} | "
                    f"{h.get('estado')} | {h.get('descripcion','')[:50]}"
                ):
                    st.json(h)
                    if h.get("estado") == "abierto":
                        nc = st.text_input("Nota cierre",
                                          key=f"nc_{h['id']}")
                        if st.button("Cerrar", key=f"ch_{h['id']}"):
                            actualizar_estado_hallazgo(
                                cliente, h["id"], "cerrado", nc
                            )
                            st.rerun()
        else:
            st.info("Sin hallazgos registrados.")
        ec1, ec2 = st.columns(2)
        with ec1:
            if st.button("Exportar hallazgos Excel", key="exp_h"):
                r = exportar_hallazgos_excel(cliente)
                st.success(f"Exportado: {r}") if r else st.warning("Sin datos.")
        with ec2:
            if st.button("Exportar resumen TXT", key="exp_r"):
                r = exportar_resumen_txt(
                    cliente,
                    ranking_areas if isinstance(ranking_areas, pd.DataFrame)
                    else None
                )
                st.success(f"Exportado: {r}") if r else st.error("Error.")

    with d_tab5:
        st.markdown(
            "<div class='section-header'>Libro Mayor</div>",
            unsafe_allow_html=True,
        )

        if df_mayor is None or (
            isinstance(df_mayor, pd.DataFrame) and df_mayor.empty
        ):
            st.info(
                "No se encontró mayor.xlsx para este cliente. "
                "Carga el archivo en: "
                f"data/clientes/{cliente}/mayor.xlsx"
            )
            st.markdown(
                "**Formato esperado del archivo:**\n\n"
                "| fecha | numero_cuenta | nombre_cuenta | ls | "
                "descripcion | referencia | debe | haber | saldo | tipo |"
            )
        else:
            # ── Summary KPIs ──────────────────────────────────
            res_m = safe_call(
                resumen_mayor, df_mayor, default={}
            ) or {}
            mk1, mk2, mk3, mk4 = st.columns(4)
            mk1.metric(
                "Total movimientos",
                res_m.get("total_movimientos", 0)
            )
            mk2.metric(
                "Total debe",
                fmt_money(res_m.get("total_debe", 0))
            )
            mk3.metric(
                "Total haber",
                fmt_money(res_m.get("total_haber", 0))
            )
            mk4.metric(
                "Cuentas distintas",
                res_m.get("cuentas_distintas", 0)
            )

            st.divider()

            # ── Filters ───────────────────────────────────────
            st.markdown(
                "<div class='section-header'>Filtros</div>",
                unsafe_allow_html=True,
            )
            f1, f2, f3, f4 = st.columns([1, 1, 2, 1])
            with f1:
                filtro_ls = st.text_input(
                    "Área L/S",
                    value=selected_area_code or "",
                    key="m_ls",
                    placeholder="ej. 14",
                )
            with f2:
                filtro_cuenta = st.text_input(
                    "Código cuenta",
                    key="m_cuenta",
                    placeholder="ej. 1.02",
                )
            with f3:
                filtro_texto = st.text_input(
                    "Buscar en descripción / referencia",
                    key="m_texto",
                    placeholder="ej. VPP, honorarios...",
                )
            with f4:
                filtro_monto = st.number_input(
                    "Monto mínimo",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    key="m_monto",
                )

            # ── Apply filters ─────────────────────────────────
            df_view = df_mayor.copy()

            if filtro_ls.strip() and filtrar_por_ls:
                filtered = safe_call(
                    filtrar_por_ls, df_view,
                    filtro_ls.strip(), default=df_view
                )
                if isinstance(filtered, pd.DataFrame):
                    df_view = filtered

            if filtro_cuenta.strip():
                try:
                    from analysis.lector_mayor import filtrar_por_cuenta as _fpc

                    filtered = safe_call(
                        _fpc, df_view,
                        filtro_cuenta.strip(), default=df_view
                    )
                    if isinstance(filtered, pd.DataFrame):
                        df_view = filtered
                except Exception:
                    pass

            if (filtro_texto.strip() or filtro_monto > 0) and buscar_movimientos:
                filtered = safe_call(
                    buscar_movimientos,
                    df_view,
                    texto=filtro_texto,
                    monto_min=filtro_monto,
                    default=df_view,
                )
                if isinstance(filtered, pd.DataFrame):
                    df_view = filtered

            st.caption(
                f"Mostrando {len(df_view)} de "
                f"{len(df_mayor)} movimientos"
            )

            # ── Table ─────────────────────────────────────────
            show_cols = [
                c for c in [
                    "fecha", "numero_cuenta", "nombre_cuenta",
                    "ls", "descripcion", "referencia",
                    "debe", "haber", "saldo",
                ]
                if c in df_view.columns
            ]

            if not df_view.empty:
                disp = df_view[show_cols].copy()
                for mc in ["debe", "haber", "saldo"]:
                    if mc in disp.columns:
                        disp[mc] = disp[mc].apply(fmt_money)
                if "fecha" in disp.columns:
                    disp["fecha"] = disp["fecha"].astype(str).str[:10]

                st.dataframe(
                    disp,
                    use_container_width=True,
                    hide_index=True,
                )

                # Download filtered mayor
                csv_bytes = df_view[show_cols].to_csv(
                    index=False
                ).encode("utf-8")
                st.download_button(
                    "⬇️ Exportar filtrado (.csv)",
                    data=csv_bytes,
                    file_name=f"mayor_{cliente}_{filtro_ls or 'all'}.csv",
                    mime="text/csv",
                    key="dl_mayor_csv",
                )
            else:
                st.info("Sin movimientos para los filtros aplicados.")

st.divider()
f1, f2, f3 = st.columns(3)
f1.caption("SocioAI - Auditoria Inteligente con IA")
f2.caption("Ultima actualizacion: 2026-03-17")
f3.caption("Modo: analisis + workspace por area")

