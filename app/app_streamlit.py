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
    .header-title { font-size: 1.8rem; font-weight: 700; color: #1a1a2e; margin-bottom: 0.5rem; }
    [data-testid="metric-container"] {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
    }
    [data-testid="stExpander"] { border: 1px solid #e0e0e0; border-radius: 8px; }
    .stButton button {
        border-radius: 6px;
        font-weight: 600;
    }
    div[data-testid="stSidebar"] { background: #1a1a2e; }
    div[data-testid="stSidebar"] * { color: #ffffff !important; }
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


def render_sidebar_summary(
    cliente: str,
    perfil: dict[str, Any] | None,
    datos_clave: dict[str, Any] | None,
    ranking_areas: pd.DataFrame | None,
) -> None:
    st.sidebar.divider()
    st.sidebar.subheader("Resumen rapido")

    perfil = perfil or {}
    datos_clave = datos_clave or {}

    periodo = get_first(datos_clave, ["periodo"], perfil.get("encargo", {}).get("anio_activo", "N/A"))
    marco = get_first(datos_clave, ["marco_referencial"], perfil.get("encargo", {}).get("marco_referencial", "N/A"))
    riesgo_global = normalize_text(perfil.get("riesgo_global", {}).get("nivel", "N/A")) or "N/A"

    top_area = "N/A"
    if ranking_areas is not None and not ranking_areas.empty:
        row0 = ranking_areas.iloc[0]
        top_area = f"{normalize_text(row0.get('area', ''))} ({fmt_num(row0.get('score_riesgo', 0), 1)})"

    st.sidebar.caption(f"Cliente: {cliente}")
    st.sidebar.caption(f"Periodo: {periodo}")
    st.sidebar.caption(f"Marco: {marco}")
    st.sidebar.caption(f"Riesgo global: {riesgo_global}")
    st.sidebar.caption(f"Top area score: {top_area}")


def render_area_header(ws: dict[str, Any]) -> None:
    st.subheader(f"{ws['area_name']} (L/S {ws['codigo_ls']})")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Etapa", ws["etapa"].capitalize())
    c2.metric("Riesgo", ws["riesgo"])
    c3.metric("Cobertura", f"{fmt_num(ws['coverage'], 1)}%")
    c4.metric("Hallazgos abiertos", ws["hallazgos_count"])
    c5.metric("Procedimientos pendientes", ws["pending_count"])
    c6.metric("Score area", fmt_num(ws["area_score"], 1) if ws["area_score"] is not None else "N/A")


def render_area_kpis(ws: dict[str, Any]) -> None:
    s = ws["area_summary"]
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Saldo actual", fmt_money(s.get("saldo_actual", 0)))
    c2.metric("Variacion neta", fmt_money(s.get("variacion_neta", 0)))
    c3.metric("Variacion acumulada", fmt_money(s.get("variacion_acumulada", 0)))
    c4.metric("Cuentas relevantes", int(s.get("cuentas_relevantes", 0) or 0))
    c5.metric("Cobertura %", f"{fmt_num(ws['coverage'], 1)}%")
    c6.metric("Hallazgos abiertos", ws["hallazgos_count"])


def render_por_que_importa(ws: dict[str, Any]) -> None:
    st.markdown("### Por qué importa esta área")
    st.markdown(
        f"- **Saldo / materialidad de ejecución:** {fmt_money(ws['area_summary'].get('saldo_actual', 0))} / {fmt_money(ws.get('materialidad_ejecucion', 0))} "
        f"({fmt_num(ws.get('materialidad_relativa', 0), 1)}%)"
    )
    st.markdown(f"- **Cobertura de aseveraciones:** {fmt_num(ws.get('coverage', 0), 1)}%")
    st.markdown(f"- **Hallazgos previos abiertos:** {ws.get('hallazgos_count', 0)}")
    st.markdown(f"- **Prioridad sugerida:** {normalize_text(ws.get('prioridad', 'media')).upper()}")

    if ws.get("expert_flags"):
        st.markdown("**Principales señales expertas**")
        for flag in ws["expert_flags"][:3]:
            st.markdown(
                f"- [{normalize_text(flag.get('nivel', 'medio')).upper()}] "
                f"{normalize_text(flag.get('titulo', 'Bandera experta'))}: "
                f"{normalize_text(flag.get('mensaje', 'Sin detalle'))}"
            )
    else:
        st.info("No se detectaron señales expertas adicionales para esta área.")

    if ws.get("es_holding") and str(ws.get("codigo_ls", "")).strip() in {"14", "200", "425.2", "1600", "1500"}:
        st.markdown("**Foco holding**")
        st.markdown(
            "- Esta area se interpreta con enfoque holding: inversiones, patrimonio, relacionadas y consistencia de presentacion."
        )
        if str(ws.get("codigo_ls", "")).strip() in {"14", "200"}:
            st.caption("Prioridad consistente con naturaleza holding.")

    st.caption(normalize_text(ws.get("justificacion", "")) or "Sin justificación automática disponible.")


def _lines_to_list(text: str) -> list[str]:
    return [x.strip() for x in str(text or "").splitlines() if x.strip()]


def _manual_state_from_ws(ws: dict[str, Any]) -> dict[str, Any]:
    estado = ws.get("estado_area", {}) or {}
    notas = estado.get("notas", []) if isinstance(estado.get("notas", []), list) else []
    pendientes = estado.get("pendientes", []) if isinstance(estado.get("pendientes", []), list) else []
    return {
        "estado_area": normalize_text(estado.get("estado_area", "")) or "no_iniciada",
        "notas": [normalize_text(x) for x in notas if normalize_text(x)],
        "pendientes": [normalize_text(x) for x in pendientes if normalize_text(x)],
        "conclusion_preliminar": normalize_text(estado.get("conclusion_preliminar", "")),
        "decision_cierre": normalize_text(estado.get("decision_cierre", "")) or "requiere_revision",
        "fecha_actualizacion": normalize_text(estado.get("fecha_actualizacion", "")),
    }


def _pending_procedures_details(ws: dict[str, Any]) -> list[str]:
    proc_df = ws.get("proc_df", pd.DataFrame())
    if not isinstance(proc_df, pd.DataFrame) or proc_df.empty:
        return []
    if "estado" not in proc_df.columns:
        return []
    done_states = {"ejecutado", "completado", "cerrado", "no_aplicable", "no_aplica"}
    mask = ~proc_df["estado"].astype(str).str.lower().isin(done_states)
    pending = proc_df[mask].copy()
    desc_col = "descripcion" if "descripcion" in pending.columns else None
    if desc_col is None:
        return []
    return [normalize_text(x) for x in pending[desc_col].tolist() if normalize_text(x)]


def _closure_readiness(ws: dict[str, Any]) -> tuple[bool, list[str]]:
    manual = _manual_state_from_ws(ws)
    hallazgos_abiertos = int(ws.get("hallazgos_count", 0) or 0)
    pendientes = len(manual.get("pendientes", []))
    conclusion_cobertura = normalize_text(ws.get("cobertura", {}).get("conclusion", "sin_mapeo"))
    calidad = ws.get("calidad_metodologia", {}) if isinstance(ws.get("calidad_metodologia", {}), dict) else {}
    alertas_criticas = int(calidad.get("resumen", {}).get("alertas_criticas", 0) or 0)

    lista_para_cerrar = True
    razones = []
    if hallazgos_abiertos > 0:
        lista_para_cerrar = False
        razones.append("Existen hallazgos abiertos.")
    if pendientes > 0:
        lista_para_cerrar = False
        razones.append("Existen pendientes operativos.")
    if conclusion_cobertura == "incompleta":
        lista_para_cerrar = False
        razones.append("La cobertura de aseveraciones está incompleta.")
    if alertas_criticas > 0:
        lista_para_cerrar = False
        razones.append("Existen alertas metodológicas críticas de calidad.")

    return lista_para_cerrar, razones


def _build_export_payload(
    ws: dict[str, Any],
    cliente: str,
    datos_clave: dict[str, Any] | None,
    perfil: dict[str, Any] | None,
) -> dict[str, Any]:
    datos_clave = datos_clave or {}
    perfil = perfil or {}
    manual = _manual_state_from_ws(ws)
    lista_para_cerrar, razones = _closure_readiness(ws)

    objetivo_area = ws["focos"][0] if ws.get("focos") else "No disponible"
    period = get_first(datos_clave, ["periodo"], perfil.get("encargo", {}).get("anio_activo", "No disponible"))
    recommendation = (
        "Lista para cerrar. Documentar conclusión final y referencias de evidencia."
        if lista_para_cerrar
        else "No lista para cerrar. " + " ".join(razones)
    )

    return {
        "cliente": cliente,
        "periodo": period,
        "area_nombre": ws.get("area_name", "No disponible"),
        "codigo_ls": ws.get("codigo_ls", "No disponible"),
        "etapa": ws.get("etapa", "No disponible"),
        "estado_area": manual.get("estado_area", "no_iniciada"),
        "riesgo": ws.get("riesgo", "No disponible"),
        "score_riesgo": ws.get("area_score", "No disponible"),
        "prioridad": ws.get("prioridad", "media"),
        "materialidad_relativa": float(ws.get("materialidad_relativa", 0) or 0),
        "senales_expertas": ws.get("expert_flags", []) or [],
        "objetivo_area": objetivo_area,
        "riesgos_area": ws.get("riesgos", []) or [],
        "procedimientos_pendientes": manual.get("pendientes", []) + _pending_procedures_details(ws),
        "cobertura": ws.get("cobertura", {}) or {},
        "hallazgos_abiertos": ws.get("hallazgos", []) or [],
        "conclusion_preliminar": manual.get("conclusion_preliminar", "No definida"),
        "decision_cierre": manual.get("decision_cierre", "requiere_revision"),
        "recomendacion_final": recommendation,
        "texto_cierre": ws.get("cierre_texto", "No disponible"),
    }


def render_export_block(
    ws: dict[str, Any],
    cliente: str,
    datos_clave: dict[str, Any] | None,
    perfil: dict[str, Any] | None,
) -> None:
    st.markdown("### Exportación del área")
    payload = _build_export_payload(ws, cliente, datos_clave, perfil)

    resumen_md = safe_call(build_area_resumen_markdown, payload, default="")
    cierre_md = safe_call(build_area_cierre_markdown, payload, default="")

    if not resumen_md:
        resumen_md = f"# Resumen de área\n\nCliente: {cliente}\nÁrea: {ws.get('codigo_ls', 'N/A')}\n"
    if not cierre_md:
        cierre_md = resumen_md

    code = str(ws.get("codigo_ls", "area")).replace("/", "_")
    resumen_filename = f"area_{code}_resumen.md"
    cierre_filename = f"area_{code}_cierre.md"

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Exportar resumen del área (Markdown)", key=f"save_resumen_{cliente}_{code}", use_container_width=True):
            out = safe_call(save_area_markdown, cliente, resumen_filename, resumen_md, default=None)
            if out is None:
                st.error("No se pudo guardar el resumen del área.")
            else:
                st.success(f"Resumen guardado en: {out}")
        st.download_button(
            "Descargar resumen (.md)",
            data=resumen_md,
            file_name=resumen_filename,
            mime="text/markdown",
            key=f"dl_resumen_{cliente}_{code}",
            use_container_width=True,
        )

    with c2:
        if st.button("Exportar cierre del área (Markdown)", key=f"save_cierre_{cliente}_{code}", use_container_width=True):
            out = safe_call(save_area_markdown, cliente, cierre_filename, cierre_md, default=None)
            if out is None:
                st.error("No se pudo guardar el cierre del área.")
            else:
                st.success(f"Cierre guardado en: {out}")
        st.download_button(
            "Descargar cierre (.md)",
            data=cierre_md,
            file_name=cierre_filename,
            mime="text/markdown",
            key=f"dl_cierre_{cliente}_{code}",
            use_container_width=True,
        )


def render_seguimiento_tab(ws: dict[str, Any], cliente: str) -> None:
    st.markdown("**Seguimiento operativo del área**")
    manual = _manual_state_from_ws(ws)

    key_base = f"seg_{cliente}_{ws['codigo_ls']}"
    with st.form(f"{key_base}_form", clear_on_submit=False):
        estado_area = st.selectbox(
            "Estado del área",
            options=["no_iniciada", "en_revision", "pendiente_cliente", "lista_para_cierre", "cerrada"],
            index=["no_iniciada", "en_revision", "pendiente_cliente", "lista_para_cierre", "cerrada"].index(
                manual["estado_area"] if manual["estado_area"] in {"no_iniciada", "en_revision", "pendiente_cliente", "lista_para_cierre", "cerrada"} else "no_iniciada"
            ),
        )
        decision_cierre = st.selectbox(
            "Decisión de cierre",
            options=["requiere_revision", "cerrar", "no_cerrar"],
            index=["requiere_revision", "cerrar", "no_cerrar"].index(
                manual["decision_cierre"] if manual["decision_cierre"] in {"requiere_revision", "cerrar", "no_cerrar"} else "requiere_revision"
            ),
        )
        notas_txt = st.text_area(
            "Notas",
            value="\n".join(manual["notas"]),
            height=140,
            help="Una nota por línea.",
        )
        pendientes_txt = st.text_area(
            "Pendientes",
            value="\n".join(manual["pendientes"]),
            height=120,
            help="Un pendiente por línea.",
        )
        conclusion_preliminar = st.text_area(
            "Conclusión preliminar",
            value=manual["conclusion_preliminar"],
            height=120,
        )

        submit = st.form_submit_button("Guardar estado del área", use_container_width=True)

    if manual.get("fecha_actualizacion"):
        st.caption(f"Última actualización: {manual['fecha_actualizacion']}")

    if submit:
        payload = {
            "codigo": str(ws["codigo_ls"]),
            "nombre": ws.get("area_name", ""),
            "estado_area": estado_area,
            "riesgo": ws.get("riesgo", ""),
            "notas": _lines_to_list(notas_txt),
            "pendientes": _lines_to_list(pendientes_txt),
            "hallazgos_abiertos": ws.get("estado_area", {}).get("hallazgos_abiertos", []) or [],
            "conclusion_preliminar": normalize_text(conclusion_preliminar),
            "decision_cierre": decision_cierre,
        }
        _ = safe_call(guardar_estado_area, cliente, str(ws["codigo_ls"]), payload, default=None)
        if _ is None:
            st.error("No se pudo guardar el estado del área.")
        else:
            hist_event = safe_call(
                agregar_evento_historial_area,
                cliente,
                str(ws["codigo_ls"]),
                payload,
                origen="manual",
                default=None,
            )
            st.success("Estado del área guardado correctamente.")
            if hist_event is None:
                st.caption("Sin cambios significativos: no se agregó nuevo evento al historial.")


def render_decision_cierre_helper(ws: dict[str, Any]) -> None:
    st.markdown("### Asistente de decisión de cierre")
    manual = _manual_state_from_ws(ws)
    hallazgos_abiertos = int(ws.get("hallazgos_count", 0) or 0)
    pendientes = len(manual.get("pendientes", []))
    conclusion_cobertura = normalize_text(ws.get("cobertura", {}).get("conclusion", "sin_mapeo"))
    cobertura_actual = float(ws.get("coverage", 0) or 0)
    calidad = ws.get("calidad_metodologia", {}) if isinstance(ws.get("calidad_metodologia", {}), dict) else {}
    alertas_criticas = int(calidad.get("resumen", {}).get("alertas_criticas", 0) or 0)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cobertura actual", f"{fmt_num(cobertura_actual, 1)}%")
    c2.metric("Hallazgos abiertos", hallazgos_abiertos)
    c3.metric("Pendientes", pendientes)
    c4.metric("Conclusión cobertura", conclusion_cobertura or "sin_mapeo")
    c5.metric("Alertas calidad criticas", alertas_criticas)

    lista_para_cerrar, razones = _closure_readiness(ws)

    if lista_para_cerrar:
        st.success("Estado sugerido: lista para cerrar")
    else:
        st.warning("Estado sugerido: no lista para cerrar")
        for r in razones:
            st.markdown(f"- {r}")


def render_historial_tab(ws: dict[str, Any], cliente: str) -> None:
    st.markdown("**Historial del área**")
    historial = safe_call(cargar_historial_area, cliente, str(ws["codigo_ls"]), default=[]) or []

    if not historial:
        st.info("Sin historial registrado todavía")
        return

    resumen = safe_call(resumir_historial_area, historial, default={}) or {}
    if resumen:
        c1, c2, c3 = st.columns(3)
        c1.metric("Eventos", int(resumen.get("total_eventos", 0) or 0))
        c2.metric("Último estado", normalize_text(resumen.get("ultimo_estado", "N/A")) or "N/A")
        c3.metric("Última decisión", normalize_text(resumen.get("ultima_decision", "N/A")) or "N/A")

    latest = historial[0]
    highlight = normalize_text(latest.get("decision_cierre", ""))
    if highlight in {"cerrar", "requiere_revision", "no_cerrar"}:
        st.caption(f"Última decisión destacada: {highlight}")
    elif normalize_text(latest.get("estado_area", "")) in {"cerrada", "lista_para_cierre"}:
        st.caption(f"Último estado destacado: {normalize_text(latest.get('estado_area', ''))}")

    st.divider()
    st.markdown("**Timeline (más reciente primero)**")
    for ev in historial:
        ts = normalize_text(ev.get("timestamp", "N/A")) or "N/A"
        estado = normalize_text(ev.get("estado_area", "N/A")) or "N/A"
        decision = normalize_text(ev.get("decision_cierre", "N/A")) or "N/A"
        concl = normalize_text(ev.get("conclusion_preliminar", ""))
        notas_res = normalize_text(ev.get("notas_resumen", ""))
        pendientes_res = normalize_text(ev.get("pendientes_resumen", ""))
        notas_count = int(ev.get("notas_count", 0) or 0)
        pendientes_count = int(ev.get("pendientes_count", 0) or 0)

        with st.container(border=True):
            st.markdown(f"**{ts}**")
            st.markdown(f"- Estado: `{estado}`")
            st.markdown(f"- Decisión: `{decision}`")
            st.markdown(f"- Conclusión: {concl[:180] + ('...' if len(concl) > 180 else '') if concl else 'No disponible'}")
            st.markdown(f"- Notas ({notas_count}): {notas_res if notas_res else 'Sin notas'}")
            st.markdown(f"- Pendientes ({pendientes_count}): {pendientes_res if pendientes_res else 'Sin pendientes'}")


def render_contexto_tab(ws: dict[str, Any]) -> None:
    area_df = ws["area_df"]

    st.markdown("**Top cuentas principales del area**")
    top_df = safe_call(top_cuentas_significativas, area_df, 8, default=pd.DataFrame())
    if top_df is None or top_df.empty:
        top_df = area_df.head(8) if isinstance(area_df, pd.DataFrame) else pd.DataFrame()

    if top_df is not None and not top_df.empty:
        cols = [c for c in ["numero_cuenta", "nombre_cuenta", "saldo_actual", "variacion_absoluta"] if c in top_df.columns]
        if cols:
            show = top_df[cols].copy()
            if "saldo_actual" in show.columns:
                show["saldo_actual"] = show["saldo_actual"].apply(fmt_money)
            if "variacion_absoluta" in show.columns:
                show["variacion_absoluta"] = show["variacion_absoluta"].apply(fmt_money)
            st.dataframe(show, use_container_width=True, hide_index=True)
        else:
            st.dataframe(top_df.head(8), use_container_width=True, hide_index=True)
    else:
        st.info("No hay cuentas principales disponibles para esta area.")

    st.markdown("**Objetivo del area**")
    if ws["focos"]:
        st.write(ws["focos"][0])
    else:
        st.write("Objetivo no disponible. Revisar mapeo de area y reglas de negocio.")

    st.markdown("**Riesgos del area**")
    if ws["riesgos"]:
        for r in ws["riesgos"]:
            st.markdown(f"- [{normalize_text(r.get('nivel', 'N/A'))}] {normalize_text(r.get('titulo', ''))}: {normalize_text(r.get('descripcion', ''))}")
    else:
        st.info("No se detectaron riesgos del motor base para esta area.")

    riesgos = ws.get("riesgos_automaticos", []) if isinstance(ws.get("riesgos_automaticos", []), list) else []
    st.subheader("Riesgos automaticos")
    if riesgos:
        for r in riesgos:
            nivel = normalize_text(r.get("nivel", ""))
            color = {"ALTO": "RED", "MEDIO": "ORANGE", "BAJO": "GREEN"}.get(nivel.upper(), "GRAY")
            st.markdown(
                f"- `{color}` **{normalize_text(r.get('tipo', 'RIESGO'))} ({nivel.upper() or 'N/A'})**  \n"
                f"  - {normalize_text(r.get('descripcion', 'Sin descripcion'))}  \n"
                f"  - Accion: {normalize_text(r.get('accion_sugerida', 'Sin accion sugerida'))}"
            )
    else:
        st.success("No se detectaron riesgos automáticos para esta área.")

    st.markdown("**Aseveraciones esperadas**")
    esperadas = ws["cobertura"].get("esperadas", [])
    if esperadas:
        st.write(", ".join(esperadas))
    else:
        st.info("No existe mapeo de aseveraciones esperadas para esta area.")

    st.markdown("**Alertas contextuales**")
    alertas = []
    if ws["hallazgos_count"] > 0:
        alertas.append(f"Hay {ws['hallazgos_count']} hallazgo(s) abierto(s).")
    if ws["pending_count"] > 0:
        alertas.append(f"Hay {ws['pending_count']} procedimiento(s) pendiente(s).")
    if ws["coverage"] < 60:
        alertas.append("Cobertura menor al 60%.")

    if alertas:
        for a in alertas:
            st.warning(a)
    else:
        st.success("Sin alertas contextuales relevantes.")


def render_briefing_tab(ws: dict[str, Any]) -> None:
    st.markdown("**Briefing ejecutivo del area**")
    st.write(ws["lectura"])

    st.markdown("**Resumen practico**")
    s = ws["area_summary"]
    st.write(
        f"Cuentas: {int(s.get('cuentas', 0) or 0)} | "
        f"Saldo actual: {fmt_money(s.get('saldo_actual', 0))} | "
        f"Variacion acumulada: {fmt_money(s.get('variacion_acumulada', 0))}"
    )

    st.markdown("**Foco de auditoria**")
    if ws["focos"]:
        for foco in ws["focos"]:
            st.markdown(f"- {foco}")
    else:
        st.info("No hay foco de auditoria definido para esta area.")

    if ws.get("es_holding"):
        st.markdown("**Foco holding**")
        foco_holding = ws.get("foco_holding", []) if isinstance(ws.get("foco_holding", []), list) else []
        if foco_holding:
            for foco in foco_holding:
                st.markdown(f"- {foco}")
        else:
            st.info("Sin foco holding específico para esta area.")

    st.markdown("**Why this area matters**")
    if ws["coverage"] < 80 or ws["hallazgos_count"] > 0:
        st.write("Esta area importa porque puede concentrar riesgo residual por cobertura parcial y/o hallazgos abiertos.")
    else:
        st.write("Esta area importa por su relevancia en el cierre, aun con cobertura favorable.")


def render_procedimientos_tab(ws: dict[str, Any]) -> None:
    st.markdown("**Procedimientos del area**")
    proc_df = ws["proc_df"].copy()

    if proc_df.empty:
        st.info("No existen procedimientos cargados para esta area.")
        return

    if "id" not in proc_df.columns:
        proc_df["id"] = ""
    if "descripcion" not in proc_df.columns:
        proc_df["descripcion"] = ""
    if "estado" not in proc_df.columns:
        proc_df["estado"] = "planificado"

    proc_df["estado"] = proc_df["estado"].astype(str).str.lower()

    estado_labels = {
        "ejecutado": "Ejecutado",
        "completado": "Completado",
        "cerrado": "Cerrado",
        "en_proceso": "En proceso",
        "planificado": "Planificado",
        "pendiente": "Pendiente",
        "no_aplicable": "No aplicable",
        "no_aplica": "No aplica",
    }
    proc_df["estado_legible"] = proc_df["estado"].map(estado_labels).fillna(proc_df["estado"])

    resumen = proc_df["estado_legible"].value_counts().to_dict()
    resumen_txt = " | ".join([f"{k}: {v}" for k, v in resumen.items()])
    st.caption(f"Resumen estados: {resumen_txt}")
    st.caption(f"Pendientes: {ws['pending_count']}")

    view_df = proc_df[["id", "descripcion", "estado_legible"]].rename(
        columns={"id": "ID", "descripcion": "Procedimiento", "estado_legible": "Estado"}
    )

    st.dataframe(
        view_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Estado": st.column_config.TextColumn(
                "Estado",
                help="Estado actual del procedimiento",
            )
        },
    )


def render_cobertura_tab(ws: dict[str, Any]) -> None:
    cobertura = ws["cobertura"]
    codigo_ls = normalize_text(ws.get("codigo_ls", ""))
    area_oficial = safe_call(obtener_area_por_codigo, codigo_ls, default=None)
    titulo_ls = normalize_text(area_oficial.get("titulo", "")) if isinstance(area_oficial, dict) else ""
    calidad = ws.get("calidad_metodologia", {}) if isinstance(ws.get("calidad_metodologia", {}), dict) else {}
    guia_det = calidad.get("aseveraciones_guia_detalle", {}) if isinstance(calidad.get("aseveraciones_guia_detalle", {}), dict) else {}
    guia_ls = guia_det.get("aseveraciones_sugeridas", []) if isinstance(guia_det.get("aseveraciones_sugeridas", []), list) else []
    guia_nota = normalize_text(guia_det.get("nota", "")) or "Guia referencial, no exhaustiva."

    st.markdown("**Resumen de cobertura**")
    c1, c2, c3 = st.columns(3)
    c1.metric("Cobertura", f"{fmt_num(cobertura.get('cobertura_porcentaje', 0), 1)}%")
    c2.metric("Aseveraciones cubiertas", len(cobertura.get("cubiertas", [])))
    c3.metric("Aseveraciones no cubiertas", len(cobertura.get("no_cubiertas", [])))

    if codigo_ls:
        st.caption(f"LS {codigo_ls} - {titulo_ls or ws.get('area_name', 'Sin título oficial')}")

    st.markdown("**Aseveraciones esperadas**")
    st.write(", ".join(cobertura.get("esperadas", [])) or "Sin datos")

    st.markdown("**Aseveraciones guía sugeridas (referencial)**")
    if guia_ls:
        st.write(", ".join([str(x) for x in guia_ls]))
    else:
        st.info("Sin guía específica disponible")
    st.caption(
        "Esta guía es referencial y puede complementarse según el juicio profesional y la naturaleza del saldo."
    )
    if guia_nota and guia_nota.lower() != "guia referencial, no exhaustiva.":
        st.caption(guia_nota)

    st.markdown("**Aseveraciones cubiertas**")
    st.write(", ".join(cobertura.get("cubiertas", [])) or "Sin cobertura fuerte")

    st.markdown("**Aseveraciones debiles**")
    st.write(", ".join(cobertura.get("debiles", [])) or "Sin aseveraciones debiles")

    st.markdown("**Aseveraciones no cubiertas**")
    st.write(", ".join(cobertura.get("no_cubiertas", [])) or "Sin aseveraciones no cubiertas")

    st.markdown("**Conclusion**")
    conclusion = normalize_text(cobertura.get("conclusion", "sin_mapeo")) or "sin_mapeo"
    if conclusion == "completa":
        st.success("Cobertura completa")
    elif conclusion == "con_reservas":
        st.warning("Cobertura con reservas")
    elif conclusion == "incompleta":
        st.error("Cobertura incompleta")
    else:
        st.info("Cobertura sin mapeo")


def render_hallazgos_tab(ws: dict[str, Any]) -> None:
    st.markdown("**Hallazgos abiertos**")
    hallazgos = ws["hallazgos"]

    if not hallazgos:
        st.info("No existen hallazgos abiertos para esta area.")
        return

    for idx, h in enumerate(hallazgos, start=1):
        st.markdown(f"{idx}. {h}")


def render_calidad_tab(ws: dict[str, Any]) -> None:
    st.markdown("**Revision de calidad metodologica**")
    calidad = ws.get("calidad_metodologia", {}) if isinstance(ws.get("calidad_metodologia", {}), dict) else {}
    if not calidad:
        st.info("No evaluado: servicio de metodologia no disponible.")
        return

    codigo_ls = normalize_text(ws.get("codigo_ls", ""))
    area_oficial = safe_call(obtener_area_por_codigo, codigo_ls, default=None)
    titulo_oficial = normalize_text(area_oficial.get("titulo", "")) if isinstance(area_oficial, dict) else ""
    st.caption(f"LS {codigo_ls} - {titulo_oficial or ws.get('area_name', 'Sin título oficial')}")

    resumen = calidad.get("resumen", {}) if isinstance(calidad.get("resumen", {}), dict) else {}
    total_alertas = int(resumen.get("total_alertas", 0) or 0)
    alertas_criticas = int(resumen.get("alertas_criticas", 0) or 0)
    estado_general = normalize_text(resumen.get("estado_general", "no_evaluado")) or "no_evaluado"

    c1, c2, c3 = st.columns(3)
    c1.metric("Alertas totales", total_alertas)
    c2.metric("Alertas criticas", alertas_criticas)
    c3.metric("Estado", estado_general.upper())

    rim = calidad.get("rim_fraude", {}) if isinstance(calidad.get("rim_fraude", {}), dict) else {}
    st.markdown("**RIM / fraude presunto**")
    st.markdown(f"- Riesgo fraude en ingresos presente: {'Si' if rim.get('ingresos_presente') else 'No'}")
    st.markdown(f"- Riesgo override gerencia presente: {'Si' if rim.get('gerencia_presente') else 'No'}")
    st.markdown(
        f"- Rebuttal documentado: ingresos={'Si' if rim.get('rebuttal_ingresos') else 'No'} | gerencia={'Si' if rim.get('rebuttal_gerencia') else 'No'}"
    )

    req = calidad.get("procedimientos_materialidad", {}) if isinstance(calidad.get("procedimientos_materialidad", {}), dict) else {}
    st.markdown("**Requerimiento de procedimientos por materialidad/fraude**")
    st.markdown(f"- Area material: {'Si' if req.get('es_material') else 'No'}")
    st.markdown(f"- Procedimientos registrados: {int(req.get('procedimientos_count', 0) or 0)}")
    st.markdown(f"- Relacionada a fraude en ingresos: {'Si' if req.get('riesgo_fraude_relacionado') else 'No'}")

    ctrl = calidad.get("pruebas_control_walkthrough", {}) if isinstance(calidad.get("pruebas_control_walkthrough", {}), dict) else {}
    st.markdown("**Pruebas de control / walkthrough**")
    st.markdown(f"- Hay pruebas control/recorrido: {'Si' if ctrl.get('hay_control_o_walkthrough') else 'No'}")
    st.markdown(f"- Soporte de base de muestra/transaccion: {'Si' if ctrl.get('tiene_soporte_base') else 'No'}")

    ing = calidad.get("ingresos_metodologia", {}) if isinstance(calidad.get("ingresos_metodologia", {}), dict) else {}
    st.markdown("**Metodologia de ingresos**")
    if ing.get("aplica"):
        st.markdown(f"- Marco aplicado: {normalize_text(ing.get('marco', 'no_disponible')) or 'no_disponible'}")
        checklist = ing.get("checklist", []) if isinstance(ing.get("checklist", []), list) else []
        faltantes = ing.get("faltantes", []) if isinstance(ing.get("faltantes", []), list) else []
        st.markdown(f"- Checklist: {', '.join([str(x) for x in checklist]) if checklist else 'No disponible'}")
        st.markdown(f"- Faltantes: {', '.join([str(x) for x in faltantes]) if faltantes else 'Ninguno'}")
    else:
        st.info("No aplica para esta area.")

    gas = calidad.get("gastos_metodologia", {}) if isinstance(calidad.get("gastos_metodologia", {}), dict) else {}
    st.markdown("**Metodologia de gastos**")
    if gas.get("aplica"):
        st.markdown(f"- Existe resumen/cruce: {'Si' if gas.get('tiene_resumen_cruce') else 'No'}")
    else:
        st.info("No aplica para esta area.")

    est = calidad.get("estimaciones_nia540", {}) if isinstance(calidad.get("estimaciones_nia540", {}), dict) else {}
    st.markdown("**NIA 540 - estimaciones contables**")
    if est.get("aplica"):
        enfoques = est.get("enfoques_detectados", []) if isinstance(est.get("enfoques_detectados", []), list) else []
        st.markdown(f"- Enfoques detectados: {', '.join([str(x) for x in enfoques]) if enfoques else 'Ninguno'}")
        sugerencias = est.get("sugerencias", []) if isinstance(est.get("sugerencias", []), list) else []
        for s in sugerencias:
            st.markdown(f"- {s}")
    else:
        st.info("No aplica para esta area.")

    hold = calidad.get("holding_sensibilidad", {}) if isinstance(calidad.get("holding_sensibilidad", {}), dict) else {}
    if hold.get("aplica"):
        st.markdown("**Sensibilidad de calidad para holding**")
        obs = hold.get("observaciones", []) if isinstance(hold.get("observaciones", []), list) else []
        if obs:
            for o in obs:
                st.markdown(f"- {o}")
        else:
            st.info("Sin observaciones holding adicionales para esta area.")

    st.markdown("**Aseveraciones guia para conclusion de papeles**")
    guia_det = calidad.get("aseveraciones_guia_detalle", {}) if isinstance(calidad.get("aseveraciones_guia_detalle", {}), dict) else {}
    asev = guia_det.get("aseveraciones_sugeridas", []) if isinstance(guia_det.get("aseveraciones_sugeridas", []), list) else []
    nota = normalize_text(guia_det.get("nota", "")) or "Guia referencial, no exhaustiva."
    st.write(", ".join([str(x) for x in asev]) if asev else "Sin guía específica disponible")
    st.caption(
        "Esta guía es referencial y puede complementarse según el juicio profesional y la naturaleza del saldo."
    )
    if nota and nota.lower() != "guia referencial, no exhaustiva.":
        st.caption(nota)

    st.markdown("**Alertas de calidad**")
    alertas = calidad.get("alertas", []) if isinstance(calidad.get("alertas", []), list) else []
    if not alertas:
        st.success("Sin alertas de calidad metodologica.")
    else:
        for a in alertas:
            nivel = normalize_text(a.get("nivel", "medio")) or "medio"
            msg = normalize_text(a.get("mensaje", "Alerta metodologica")) or "Alerta metodologica"
            det = normalize_text(a.get("detalle", ""))
            critica = bool(a.get("critica", False))
            prefix = "[CRITICA]" if critica else f"[{nivel.upper()}]"
            if critica:
                st.error(f"{prefix} {msg}")
            elif nivel == "alto":
                st.warning(f"{prefix} {msg}")
            else:
                st.info(f"{prefix} {msg}")
            if det:
                st.caption(det)


def render_cierre_tab(ws: dict[str, Any]) -> None:
    render_decision_cierre_helper(ws)
    st.divider()
    st.markdown("**Revision de cierre**")
    st.text_area("Texto de revision", value=ws["cierre_texto"], height=240)

    st.markdown("**Pendientes clave antes del cierre**")
    if ws["pendientes"]:
        for p in ws["pendientes"]:
            st.markdown(f"- {p}")
    elif ws["pending_count"] > 0:
        st.markdown(f"- Existen {ws['pending_count']} procedimientos pendientes.")
    else:
        st.markdown("- No se registran pendientes criticos.")

    st.markdown("**Conclusion sugerida**")
    lista_para_cerrar, razones = _closure_readiness(ws)
    if lista_para_cerrar:
        st.success("Se puede avanzar al cierre del area.")
    else:
        st.warning("No se recomienda cerrar el area aun.")
        for r in razones:
            st.markdown(f"- {r}")

    st.markdown("**Proximas acciones recomendadas**")
    actions = []
    if ws["pending_count"] > 0:
        actions.append("Completar procedimientos pendientes con evidencia.")
    if ws["hallazgos_count"] > 0:
        actions.append("Resolver hallazgos abiertos o documentar plan de remediacion.")
    if ws["coverage"] < 80:
        actions.append("Fortalecer cobertura en aseveraciones debiles/no cubiertas.")
    calidad = ws.get("calidad_metodologia", {}) if isinstance(ws.get("calidad_metodologia", {}), dict) else {}
    if int(calidad.get("resumen", {}).get("alertas_criticas", 0) or 0) > 0:
        actions.append("Resolver alertas metodologicas criticas de la pestana Revision de calidad.")
    if not actions:
        actions.append("Documentar conclusion final del area y referencias de soporte.")

    for a in actions:
        st.markdown(f"- {a}")


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

if st.sidebar.button("Cargar cliente", use_container_width=True):
    st.session_state.cliente_cargado = cliente_seleccionado

if "cliente_cargado" not in st.session_state:
    st.session_state.cliente_cargado = cliente_seleccionado

cliente = st.session_state.cliente_cargado


# ============================================================
# Carga de datos base
# ============================================================
perfil = safe_call(leer_perfil, cliente, default={}) or {}
datos_clave = safe_call(obtener_datos_clave, cliente, default={}) or {}
tb = safe_call(leer_tb, cliente, default=pd.DataFrame())
resumen_tb = safe_call(obtener_resumen_tb, cliente, default={}) or {}
diag_tb = safe_call(obtener_diagnostico_tb, cliente, default={}) or {}
ranking_areas = safe_call(calcular_ranking_areas, cliente, default=pd.DataFrame())
indicadores = safe_call(obtener_indicadores_clave, cliente, default={}) or {}
variaciones = safe_call(calcular_variaciones, cliente, default=pd.DataFrame())

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

render_sidebar_summary(cliente, perfil, datos_clave, ranking_areas)


# ============================================================
# Header principal
# ============================================================
st.markdown("<div class='header-title'>SocioAI - Analisis de Auditoria</div>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cliente", normalize_text(get_first(datos_clave, ["nombre"], perfil.get("cliente", {}).get("nombre_legal", "N/A"))) or "N/A")
c2.metric("RUC", normalize_text(get_first(datos_clave, ["ruc"], perfil.get("cliente", {}).get("ruc", "N/A"))) or "N/A")
c3.metric("Sector", normalize_text(get_first(datos_clave, ["sector"], perfil.get("cliente", {}).get("sector", "N/A"))) or "N/A")
c4.metric("Moneda", normalize_text(get_first(datos_clave, ["moneda"], perfil.get("cliente", {}).get("moneda_funcional", "N/A"))) or "N/A")

st.divider()


# ============================================================
# Tabs principales
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Resumen",
    "Ranking de áreas",
    "Vista por área",
    "Variaciones",
    "Trial Balance",
    "Hallazgos",
    "Briefing IA",
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
    st.write(f"Concentracion principal area: {fmt_num(concentracion, 1)}%")
    st.progress(max(0.0, min(concentracion / 100.0, 1.0)))


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

        st.dataframe(rank_view, use_container_width=True, hide_index=True)
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
        st.dataframe(show, use_container_width=True, hide_index=True)
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

        st.dataframe(tb_filtrado, use_container_width=True, hide_index=True)

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
    st.subheader("Briefing de Área con IA (DeepSeek)")

    from llm.llm_client import llamar_llm_seguro

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        area_briefing_input = st.text_input(
            "Código área L/S para briefing", value=selected_area_code or "14"
        )
    with col_b2:
        etapa_input = st.selectbox(
            "Etapa de auditoría", ["planificacion", "ejecucion", "cierre"]
        )

    if st.button("Generar Briefing con IA"):
        with st.spinner("Consultando al modelo..."):
            try:
                from llm.briefing_llm import generar_briefing_area_llm
                resultado = generar_briefing_area_llm(
                    nombre_cliente=cliente,
                    codigo_ls=area_briefing_input,
                    etapa=etapa_input,
                )
                st.text_area("Criterio del socio (IA)", value=resultado, height=400)
            except ValueError as ve:
                msg = str(ve)
                if "DEEPSEEK_API_KEY" in msg or "OPENAI_API_KEY" in msg:
                    st.error(
                        f"Falta API key: {ve}. "
                        "Agrega DEEPSEEK_API_KEY a tu archivo .env y reinicia la app."
                    )
                else:
                    st.error(f"Error de configuración interna: {ve}")
            except Exception as ex:
                st.error(f"Error al generar briefing: {ex}")

    st.info(
        "Requiere DEEPSEEK_API_KEY en el archivo .env del proyecto. "
        "Si no tienes clave, el resto de la app funciona sin IA."
    )


st.divider()
f1, f2, f3 = st.columns(3)
f1.caption("SocioAI - Auditoria Inteligente con IA")
f2.caption("Ultima actualizacion: 2026-03-17")
f3.caption("Modo: analisis + workspace por area")
