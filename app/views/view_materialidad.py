from __future__ import annotations

from typing import Any

import streamlit as st

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


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


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
