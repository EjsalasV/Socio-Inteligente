"""
SocioAI - Interfaz Web con Streamlit.

Refactor incremental para convertir "Vista por area" en un workspace operativo
sin romper el flujo existente.
"""

from __future__ import annotations

import sys
from pathlib import Path
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
    options: list[tuple[str, str]] = []

    if ranking_areas is not None and not ranking_areas.empty and "area" in ranking_areas.columns:
        for _, row in ranking_areas.iterrows():
            code = normalize_text(row.get("area", ""))
            name = normalize_text(row.get("nombre", ""))
            if code:
                label = f"{code} - {name}" if name else code
                options.append((code, label))

    def _label_from_catalog(code: str) -> str:
        area = safe_call(obtener_area_por_codigo, code, default=None)
        if isinstance(area, dict):
            title = normalize_text(area.get("titulo", ""))
            if title:
                return f"{code} - {title}"
        return f"{code} - Area {code}"

    # fallback desde archivos de estado de area
    area_path = Path("data") / "clientes" / cliente / "areas"
    if area_path.exists():
        for yml in sorted(area_path.glob("*.yaml")):
            code = yml.stem.strip()
            if code and code not in {c for c, _ in options}:
                options.append((code, _label_from_catalog(code)))

    # fallback por columnas de TB
    if tb is not None and not tb.empty:
        ls_col = None
        for c in ["ls", "l/s", "l_s", "L/S"]:
            if c in tb.columns:
                ls_col = c
                break
        if ls_col:
            vals = sorted({normalize_text(v) for v in tb[ls_col].dropna().tolist() if normalize_text(v)})
            for code in vals:
                if code not in {c for c, _ in options}:
                    options.append((code, _label_from_catalog(code)))

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "Resumen",
    "Ranking de áreas",
    "Vista por área",
    "Variaciones",
    "Trial Balance",
    "Hallazgos",
    "Briefing IA",
    "Chat con IA",
    "Análisis Financiero",
])


with tab1:
    st.subheader("Balance general")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Activos", fmt_money(resumen_tb.get("ACTIVO", 0)))
    col2.metric("Pasivos", fmt_money(resumen_tb.get("PASIVO", 0)))
    col3.metric("Patrimonio", fmt_money(resumen_tb.get("PATRIMONIO", 0)))
    col4.metric("# Cuentas", int(tb.shape[0]) if isinstance(tb, pd.DataFrame) else 0)

    st.divider()
    st.subheader("Indicadores de riesgo")
    r1, r2, r3 = st.columns(3)
    r1.metric("Areas alto riesgo", indicadores.get("areas_alto_riesgo", 0))
    r2.metric("Areas medio riesgo", indicadores.get("areas_medio_riesgo", 0))
    r3.metric("Areas bajo riesgo", indicadores.get("areas_bajo_riesgo", 0))

    concentracion = float(indicadores.get("concentracion_principal_area", 0) or 0)
    st.markdown("**Concentración principal área**")
    conc_value = max(0.0, min(concentracion / 100.0, 1.0))
    color_conc = (
        "#DE350B" if concentracion >= 50
        else "#FF8B00" if concentracion >= 30
        else "#00875A"
    )
    st.markdown(f"""
    <div style="background:#F4F5F7; border-radius:8px; padding:4px; margin-bottom:4px;">
        <div style="background:{color_conc}; width:{min(concentracion,100):.1f}%;
                    height:18px; border-radius:6px; transition:width 0.5s;
                    display:flex; align-items:center; padding-left:8px;">
            <span style="color:white; font-size:0.75rem; font-weight:700;">
                {concentracion:.1f}%
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    try:
        import plotly.express as px
        alto   = indicadores.get("areas_alto_riesgo", 0)
        medio  = indicadores.get("areas_medio_riesgo", 0)
        bajo   = indicadores.get("areas_bajo_riesgo", 0)
        if alto + medio + bajo > 0:
            fig_pie = px.pie(
                names=["Alto", "Medio", "Bajo"],
                values=[alto, medio, bajo],
                color=["Alto", "Medio", "Bajo"],
                color_discrete_map={
                    "Alto": "#DE350B",
                    "Medio": "#FF8B00",
                    "Bajo": "#00875A",
                },
                title="Distribución de riesgo por áreas",
                hole=0.45,
            )
            fig_pie.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_color="#172B4D",
                title_font_color="#003366",
                title_font_size=15,
                height=300,
                margin=dict(l=10, r=10, t=40, b=10),
                legend=dict(orientation="h", y=-0.1),
            )
            fig_pie.update_traces(
                textposition="inside",
                textinfo="percent+label",
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    except ImportError:
        pass


with tab2:
    st.subheader("Ranking explicable de áreas")

    if isinstance(ranking_areas, pd.DataFrame) and not ranking_areas.empty:
        cols = [
            "area",
            "nombre",
            "estado_presencia",
            "score_riesgo",
            "pct_total",
            "materialidad_relativa",
            "expert_flags_count",
            "prioridad",
            "justificacion",
        ]
        show_cols = [c for c in cols if c in ranking_areas.columns]
        rank_view = ranking_areas[show_cols].copy()

        if "score_riesgo" in rank_view.columns:
            rank_view["score_riesgo"] = rank_view["score_riesgo"].apply(lambda x: f"{float(x):.2f}")
        if "pct_total" in rank_view.columns:
            rank_view["pct_total"] = rank_view["pct_total"].apply(lambda x: f"{float(x):.2f}%")
        if "materialidad_relativa" in rank_view.columns:
            rank_view["materialidad_relativa"] = rank_view["materialidad_relativa"].apply(lambda x: f"{float(x):.2f}%")
        if "prioridad" in rank_view.columns:
            rank_view["prioridad"] = rank_view["prioridad"].astype(str).str.upper()
        if "estado_presencia" in rank_view.columns:
            rank_view["estado_presencia"] = rank_view["estado_presencia"].astype(str).str.upper()

        def _color_score(val):
            try:
                v = float(str(val).replace("%",""))
                if v >= 70: return "background-color: #FFEBE6; color: #DE350B; font-weight: 700"
                if v >= 40: return "background-color: #FFFAE6; color: #FF8B00; font-weight: 700"
                return "background-color: #E3FCEF; color: #00875A; font-weight: 700"
            except Exception:
                return ""

        if "score_riesgo" in rank_view.columns:
            st.dataframe(
                rank_view.style.applymap(_color_score, subset=["score_riesgo"]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.dataframe(rank_view, use_container_width=True, hide_index=True)
        try:
            import plotly.express as px
            if isinstance(ranking_areas, pd.DataFrame) and not ranking_areas.empty:
                chart_df = ranking_areas.head(8).copy()
                chart_df["nombre_corto"] = chart_df["nombre"].str[:25]
                chart_df["color"] = chart_df["score_riesgo"].apply(
                    lambda x: "#DE350B" if x >= 70
                    else "#FF8B00" if x >= 40
                    else "#00875A"
                )
                fig = px.bar(
                    chart_df,
                    x="score_riesgo",
                    y="nombre_corto",
                    orientation="h",
                    title="Score de riesgo por área",
                    labels={"score_riesgo": "Score", "nombre_corto": "Área"},
                    color="score_riesgo",
                    color_continuous_scale=["#00875A", "#FF8B00", "#DE350B"],
                )
                fig.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font_color="#172B4D",
                    title_font_color="#003366",
                    title_font_size=16,
                    showlegend=False,
                    height=350,
                    margin=dict(l=10, r=10, t=40, b=10),
                    coloraxis_showscale=False,
                )
                fig.update_xaxes(showgrid=True, gridcolor="#DFE1E6")
                fig.update_yaxes(showgrid=False)
                st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass
    else:
        st.info("No se pudo construir el ranking enriquecido para este cliente.")


with tab3:
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
    render_por_que_importa(ws)
    render_export_block(ws, cliente, datos_clave, perfil)
    st.divider()

    t_ctx, t_brf, t_proc, t_cov, t_hal, t_seg, t_his, t_cal, t_cie, t_soc = st.tabs([
        "Contexto",
        "Briefing",
        "Procedimientos",
        "Cobertura",
        "Hallazgos",
        "Seguimiento",
        "Historial",
        "Revision de calidad",
        "Cierre",
        "Consultar Socio",
    ])

    with t_ctx:
        render_contexto_tab(ws)
    with t_brf:
        render_briefing_tab(ws)
    with t_proc:
        render_procedimientos_tab(ws)
    with t_cov:
        render_cobertura_tab(ws)
    with t_hal:
        render_hallazgos_tab(ws)
    with t_seg:
        render_seguimiento_tab(ws, cliente)
    with t_his:
        render_historial_tab(ws, cliente)
    with t_cal:
        render_calidad_tab(ws)
    with t_cie:
        render_cierre_tab(ws)
    with t_soc:
        render_consultar_socio_tab(ws, cliente)


with tab4:
    st.subheader("Analisis de variaciones")

    resumen_var = safe_call(resumen_variaciones, cliente, default={}) or {}
    v1, v2, v3 = st.columns(3)
    v1.metric("Cuentas con variacion", resumen_var.get("total_cuentas_variacion", 0))
    v2.metric("Mayor variacion", fmt_money(resumen_var.get("mayor_variacion", 0)))
    v3.metric("Suma variaciones", fmt_money(resumen_var.get("suma_variaciones", 0)))

    if isinstance(variaciones, pd.DataFrame) and not variaciones.empty:
        cols = [c for c in ["codigo", "nombre", "saldo", "impacto"] if c in variaciones.columns]
        show = variaciones[cols].head(15).copy() if cols else variaciones.head(15).copy()
        if "saldo" in show.columns:
            show["saldo"] = show["saldo"].apply(fmt_money)
        if "impacto" in show.columns:
            show["impacto"] = show["impacto"].apply(fmt_money)
        st.dataframe(show, width="stretch", hide_index=True)
    else:
        st.info("No hay variaciones significativas detectadas.")


with tab5:
    st.subheader("Trial Balance")

    if not isinstance(tb, pd.DataFrame) or tb.empty:
        st.error("No se pudo cargar el trial balance.")
    else:
        tb_filtrado = tb.copy()

        if "tipo_cuenta" in tb_filtrado.columns:
            tipos = sorted([str(x) for x in tb_filtrado["tipo_cuenta"].dropna().unique().tolist()])
            sel_tipos = st.multiselect("Filtrar por tipo de cuenta", options=tipos, default=tipos)
            if sel_tipos:
                tb_filtrado = tb_filtrado[tb_filtrado["tipo_cuenta"].astype(str).isin(sel_tipos)]

        st.dataframe(tb_filtrado, width="stretch", hide_index=True)

        num_col = None
        for c in ["saldo", "saldo_2025", "saldo_actual", "saldo_preliminar"]:
            if c in tb_filtrado.columns:
                num_col = c
                break

        if num_col:
            vals = pd.to_numeric(tb_filtrado[num_col], errors="coerce").fillna(0)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Numero de cuentas", int(len(tb_filtrado)))
            c2.metric("Suma de saldos", fmt_money(vals.sum()))
            c3.metric("Mayor saldo", fmt_money(vals.max()))
            c4.metric("Menor saldo", fmt_money(vals.min()))


with tab6:
    st.subheader("Gestión de Hallazgos")

    from domain.services.hallazgos_service import (
        cargar_hallazgos_gestion,
        crear_hallazgo,
        actualizar_estado_hallazgo,
        resumen_hallazgos,
    )
    from domain.services.export_service import exportar_hallazgos_excel, exportar_resumen_txt

    resumen_h = resumen_hallazgos(cliente)
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Total", resumen_h["total"])
    h2.metric("Abiertos", resumen_h["abiertos"])
    h3.metric("Cerrados", resumen_h["cerrados"])
    h4.metric("Alto riesgo abiertos", resumen_h["alto_riesgo_abiertos"])

    st.divider()

    with st.expander("Registrar nuevo hallazgo"):
        col_a, col_b = st.columns(2)
        with col_a:
            desc_input = st.text_area("Descripción del hallazgo")
            area_input = st.text_input("Código área L/S (ej: 14, 130.1)")
        with col_b:
            asev_input = st.text_input("Aseveración afectada")
            nivel_input = st.selectbox("Nivel", ["alto", "medio", "bajo"])
            resp_input = st.text_input("Responsable")

        if st.button("Guardar hallazgo"):
            if desc_input and area_input:
                nuevo = crear_hallazgo(
                    cliente=cliente,
                    codigo_area=area_input,
                    descripcion=desc_input,
                    aseveracion=asev_input,
                    nivel=nivel_input,
                    responsable=resp_input,
                )
                st.success(f"Hallazgo {nuevo['id']} creado.")
                st.rerun()
            else:
                st.warning("Descripción y área son obligatorios.")

    st.divider()
    st.subheader("Hallazgos registrados")

    todos = cargar_hallazgos_gestion(cliente)
    if todos:
        filtro_estado = st.selectbox(
            "Filtrar por estado", ["todos", "abierto", "cerrado"]
        )
        lista = todos if filtro_estado == "todos" else [
            h for h in todos if h.get("estado") == filtro_estado
        ]
        for h in lista:
            nivel_color = {"alto": "🔴", "medio": "🟡", "bajo": "🟢"}.get(
                h.get("nivel", ""), "⚪"
            )
            with st.expander(
                f"{nivel_color} {h.get('id')} | {h.get('codigo_area')} | {h.get('estado')} | {h.get('descripcion','')[:60]}"
            ):
                st.json(h)
                if h.get("estado") == "abierto":
                    nota_cierre = st.text_input(
                        "Nota de cierre", key=f"nota_{h['id']}"
                    )
                    if st.button("Cerrar hallazgo", key=f"cerrar_{h['id']}"):
                        actualizar_estado_hallazgo(
                            cliente, h["id"], "cerrado", nota_cierre
                        )
                        st.rerun()
    else:
        st.info("Sin hallazgos registrados para este cliente.")

    st.divider()
    st.subheader("Exportar")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        if st.button("Exportar hallazgos a Excel"):
            ruta = exportar_hallazgos_excel(cliente)
            if ruta:
                st.success(f"Exportado: {ruta}")
            else:
                st.warning("Sin hallazgos para exportar.")
    with col_e2:
        if st.button("Exportar resumen ejecutivo"):
            ruta = exportar_resumen_txt(cliente, ranking_areas if isinstance(ranking_areas, pd.DataFrame) else None)
            if ruta:
                st.success(f"Exportado: {ruta}")
            else:
                st.error("Error al exportar.")


with tab7:
    render_briefing_ia_tab(cliente, selected_area_code)


with tab8:
    from llm.llm_client import llamar_llm_seguro
    render_chat_tab(cliente, cached_leer_perfil, llamar_llm_seguro)

with tab9:
    st.subheader("Análisis Financiero")

    from analysis.ratios import resumen_ratios, calcular_ratios
    from analysis.benchmark import resumen_benchmark
    from analysis.tendencias import resumen_tendencias, alertas_tendencias

    col_r, col_b = st.columns(2)

    with col_r:
        st.markdown("#### Ratios financieros")
        ratios_data = resumen_ratios(cliente)
        if ratios_data:
            df_ratios = pd.DataFrame(ratios_data)
            show_cols = ["categoria", "ratio", "valor", "interpretacion"]
            show_cols = [c for c in show_cols if c in df_ratios.columns]
            st.dataframe(df_ratios[show_cols], use_container_width=True, hide_index=True)
        else:
            st.info("Sin datos suficientes para calcular ratios.")

    with col_b:
        st.markdown("#### Benchmark sectorial")
        bench = resumen_benchmark(cliente)
        if bench.get("total", 0) > 0:
            b1, b2, b3 = st.columns(3)
            b1.metric("OK", bench["ok"])
            b2.metric("Alerta", bench["alerta"])
            b3.metric("Crítico", bench["critico"])
            df_bench = pd.DataFrame(bench["detalle"])
            show_b = ["ratio", "valor_cliente", "benchmark_optimo", "estado"]
            show_b = [c for c in show_b if c in df_bench.columns]
            st.dataframe(df_bench[show_b], use_container_width=True, hide_index=True)
        else:
            st.info("Sin benchmark disponible para este cliente.")

    st.divider()
    st.markdown("#### Tendencias de cuentas")
    res_tend = resumen_tendencias(cliente)
    if res_tend:
        t1, t2, t3 = st.columns(3)
        t1.metric("Total cuentas", res_tend.get("total_cuentas", 0))
        t2.metric("Cuentas en alerta", res_tend.get("cuentas_alerta", 0))
        t3.metric("Mayor crecimiento", 
            res_tend.get("mayor_crecimiento", {}).get("nombre", "N/A")
            if res_tend.get("mayor_crecimiento") else "N/A"
        )
        alertas = alertas_tendencias(cliente)
        if alertas:
            st.markdown("**Cuentas que requieren atención**")
            df_alertas = pd.DataFrame(alertas[:15])
            show_t = ["codigo", "nombre", "saldo_actual",
                      "variacion_absoluta", "variacion_porcentual", "tendencia"]
            show_t = [c for c in show_t if c in df_alertas.columns]
            st.dataframe(df_alertas[show_t], use_container_width=True, hide_index=True)
    else:
        st.info("Sin datos de tendencias disponibles.")


st.divider()
f1, f2, f3 = st.columns(3)
f1.caption("SocioAI - Auditoria Inteligente con IA")
f2.caption("Ultima actualizacion: 2026-03-17")
f3.caption("Modo: analisis + workspace por area")
