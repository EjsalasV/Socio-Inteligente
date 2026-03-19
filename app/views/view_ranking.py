from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

try:
    from domain.services.area_briefing import top_cuentas_significativas
except Exception:
    top_cuentas_significativas = None

try:
    from infra.repositories.catalogo_repository import obtener_area_por_codigo
except Exception:
    obtener_area_por_codigo = None


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
            st.dataframe(show, width="stretch", hide_index=True)
        else:
            st.dataframe(top_df.head(8), width="stretch", hide_index=True)
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
        width="stretch",
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
