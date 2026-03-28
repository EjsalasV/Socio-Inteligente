from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def render_profile_editorial_intro() -> None:
    st.markdown(
        """
        <div class="sovereign-card" style="margin:.3rem 0 .9rem 0;">
          <div style="font-size:.66rem;letter-spacing:.16em;text-transform:uppercase;font-weight:800;color:#64748B;">
            The Sovereign Intelligence
          </div>
          <div class="sv-serif" style="font-size:2rem;font-weight:700;color:#041627;line-height:1.1;margin-top:.2rem;">
            Configuracion de Perfil
          </div>
          <div style="font-size:.9rem;color:#64748B;margin-top:.35rem;">
            Define el contexto del cliente para que Socio AI priorice riesgos y evidencia con criterio editorial premium.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_profile_card_title(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="profile-block-marker"></div>
        <div style="font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;font-weight:800;color:#64748B;">
          {title}
        </div>
        {f'<div style="font-size:.82rem;color:#64748B;margin:.28rem 0 .25rem 0;">{subtitle}</div>' if subtitle else ''}
        """,
        unsafe_allow_html=True,
    )


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
