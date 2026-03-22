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
    if variaciones is not None and not variaciones.empty:
        for col in ["ls", "l/s", "l_s", "L/S"]:
            if col in variaciones.columns:
                area = variaciones[variaciones[col].astype(str).str.strip() == str(codigo_ls).strip()].copy()
                if not area.empty:
                    return area

    if tb is not None and not tb.empty:
        # fallback simple: filtrar por prefijo de codigo
        codigo_col = None
        nombre_col = None
        saldo_col = None
        for c in ["codigo", "numero_de_cuenta", "cuenta", "cod_cuenta"]:
            if c in tb.columns:
                codigo_col = c
                break
        for c in ["nombre", "nombre_cuenta", "descripcion"]:
            if c in tb.columns:
                nombre_col = c
                break
        for c in ["saldo", "saldo_2025", "saldo_actual", "saldo_preliminar"]:
            if c in tb.columns:
                saldo_col = c
                break

        if codigo_col and saldo_col:
            mask = tb[codigo_col].astype(str).str.startswith(str(codigo_ls))
            sub = tb[mask].copy()
            if not sub.empty:
                out = pd.DataFrame()
                out["numero_cuenta"] = sub[codigo_col].astype(str)
                out["nombre_cuenta"] = sub[nombre_col] if nombre_col else ""
                out["saldo_actual"] = pd.to_numeric(sub[saldo_col], errors="coerce").fillna(0.0)
                out["saldo_anterior"] = 0.0
                out["variacion_absoluta"] = out["saldo_actual"] - out["saldo_anterior"]
                out["abs_variacion_absoluta"] = out["variacion_absoluta"].abs()
                out["flag_movimiento_relevante"] = out["abs_variacion_absoluta"] > 0
                out["flag_sin_base"] = True
                out["ls"] = str(codigo_ls)
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


# ============================================================
# Sidebar
# ============================================================
st.sidebar.title("Configuracion")

clientes_disponibles: list[str] = []
data_path = Path("data/clientes")
if data_path.exists():
    clientes_disponibles = sorted([d.name for d in data_path.iterdir() if d.is_dir()])

if not clientes_disponibles:
    st.sidebar.warning("No hay clientes disponibles en data/clientes/")
    st.stop()

cliente_seleccionado = st.sidebar.selectbox(
    "Seleccionar cliente",
    options=clientes_disponibles,
    index=0 if "cliente_demo" in clientes_disponibles else 0,
)

etapa_seleccionada = st.sidebar.selectbox(
    "Etapa",
    options=["planificacion", "ejecucion", "cierre"],
    index=2,
)

if st.sidebar.button("Cargar cliente", width="stretch"):
    st.session_state.cliente_cargado = cliente_seleccionado

if "cliente_cargado" not in st.session_state:
    st.session_state.cliente_cargado = cliente_seleccionado

cliente = st.session_state.cliente_cargado


# ============================================================
# Carga de datos base
# ============================================================
perfil = safe_call(cached_leer_perfil, cliente, default={}) or {}
datos_clave = safe_call(cached_datos_clave, cliente, default={}) or {}
tb = safe_call(cached_leer_tb, cliente, default=pd.DataFrame())
resumen_tb = safe_call(cached_resumen_tb, cliente, default={}) or {}
diag_tb = safe_call(obtener_diagnostico_tb, cliente, default={}) or {}
ranking_areas = safe_call(cached_ranking_areas, cliente, default=pd.DataFrame())
indicadores = safe_call(cached_indicadores, cliente, default={}) or {}
variaciones = safe_call(cached_variaciones, cliente, default=pd.DataFrame())

# Mayor (optional — only if file exists)
df_mayor = None
if mayor_existe and safe_call(mayor_existe, cliente, default=False):
    df_mayor = safe_call(
        obtener_mayor_cliente, cliente, default=None
    )

if isinstance(diag_tb, dict):
    rows_loaded = int(diag_tb.get("rows_loaded", 0) or 0)
    rows_saldo_no_cero = int(diag_tb.get("rows_saldo_no_cero", 0) or 0)
    if rows_loaded > 0 and rows_saldo_no_cero == 0:
        st.warning(
            "Se cargó el TB pero no se detectaron saldos no cero. Revisar mapeo de columnas para este cliente."
        )
    elif rows_loaded == 0:
        st.warning("No se pudieron cargar filas del TB para el cliente seleccionado.")

area_options = infer_area_options(ranking_areas, tb, cliente)
if not area_options:
    area_options = [("140", "140 - Area 140")]

selected_area_code = st.sidebar.selectbox(
    "Area L/S",
    options=[x[0] for x in area_options],
    format_func=lambda v: dict(area_options).get(v, v),
)

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


with tab2:
    col_rank, col_ws = st.columns([1, 2])

    with col_rank:
        st.markdown("<div class='section-header'>Ranking de Áreas</div>",
                    unsafe_allow_html=True)
        if isinstance(ranking_areas, pd.DataFrame) and not ranking_areas.empty:
            cols_show = ["area", "nombre", "score_riesgo", "prioridad"]
            cols_show = [c for c in cols_show if c in ranking_areas.columns]
            rank_small = ranking_areas[cols_show].head(10).copy()
            if "score_riesgo" in rank_small.columns:
                rank_small["score_riesgo"] = rank_small["score_riesgo"].apply(
                    lambda x: f"{float(x):.1f}"
                )
            if "prioridad" in rank_small.columns:
                rank_small["prioridad"] = rank_small["prioridad"].str.upper()
            st.dataframe(rank_small, use_container_width=True, hide_index=True)
        else:
            st.info("Sin datos de ranking.")

    with col_ws:
        st.markdown("<div class='section-header'>Workspace por Área</div>",
                    unsafe_allow_html=True)
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
        ])

        # ── Tab 1: Resumen ────────────────────────────────────────
        with inner_tabs[0]:
            # Only show KPIs if there is actual data
            saldo_val = float(
                ws.get("area_summary", {}).get("saldo_actual", 0) or 0
            )
            var_val = float(
                ws.get("area_summary", {}).get("variacion_acumulada", 0) or 0
            )
            has_data = saldo_val != 0 or var_val != 0

            if has_data:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Saldo actual", fmt_money(saldo_val))
                m2.metric("Variación acum.", fmt_money(var_val))
                m3.metric(
                    "Cobertura",
                    f"{fmt_num(ws.get('coverage', 0), 1)}%"
                )
                m4.metric(
                    "Hallazgos abiertos",
                    ws.get("hallazgos_count", 0)
                )
            else:
                st.info("Sin movimientos registrados en el período para esta área.")

            st.divider()
            render_contexto_tab(ws)

            with st.expander("📌 Briefing del área", expanded=False):
                render_briefing_tab(ws)

            with st.expander("📂 Procedimientos", expanded=False):
                render_procedimientos_tab(ws)

        # ── Tab 2: Trabajo ────────────────────────────────────────
        with inner_tabs[1]:
            left_w, right_w = st.columns(2)
            with left_w:
                render_hallazgos_tab(ws)
            with right_w:
                render_seguimiento_tab(ws, cliente)
            st.divider()
            with st.expander("🕐 Historial de cambios", expanded=False):
                render_historial_tab(ws, cliente)

        # ── Tab 3: Calidad ────────────────────────────────────────
        with inner_tabs[2]:
            with st.expander("🔬 Cobertura de aseveraciones", expanded=True):
                render_cobertura_tab(ws)
            with st.expander("✅ Revisión de calidad metodológica",
                             expanded=False):
                render_calidad_tab(ws)

        # ── Tab 4: Cierre ─────────────────────────────────────────
        with inner_tabs[3]:
            _render_cierre_cards(ws)


with tab3:
    ia_tab1, ia_tab2, ia_tab3 = st.tabs([
        "💡 Briefing", "📝 Programa", "💬 Chat"
    ])

    with ia_tab1:
        st.markdown("<div class='section-header'>Briefing de Área</div>",
                    unsafe_allow_html=True)
        render_briefing_ia_tab(cliente, selected_area_code)

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
        st.markdown("<div class='section-header'>Chat con IA</div>",
                    unsafe_allow_html=True)
        from llm.llm_client import llamar_llm_seguro
        render_chat_tab(cliente, cached_leer_perfil, llamar_llm_seguro)


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

