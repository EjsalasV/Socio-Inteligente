from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

try:
    from domain.services.estado_area_yaml import guardar_estado_area
except Exception:
    guardar_estado_area = None

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
    from domain.services.export_area_service import (
        build_area_resumen_markdown,
        build_area_cierre_markdown,
        save_area_markdown,
    )
except Exception:
    build_area_resumen_markdown = None
    build_area_cierre_markdown = None
    save_area_markdown = None


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
        if st.button("Exportar resumen del área (Markdown)", key=f"save_resumen_{cliente}_{code}", width="stretch"):
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
            width="stretch",
        )

    with c2:
        if st.button("Exportar cierre del área (Markdown)", key=f"save_cierre_{cliente}_{code}", width="stretch"):
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
            width="stretch",
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

        submit = st.form_submit_button("Guardar estado del área", width="stretch")

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
