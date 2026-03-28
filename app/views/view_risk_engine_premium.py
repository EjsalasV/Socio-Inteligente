from __future__ import annotations

from html import escape
from pathlib import Path
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def _txt(v: Any, default: str = "") -> str:
    t = str(v if v is not None else default).strip()
    if not t:
        t = default
    return escape(t)


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _html_block(raw: str) -> str:
    # Streamlit Markdown can treat indented HTML as code blocks.
    # Normalize by stripping leading indentation per line.
    return "\n".join(line.lstrip() for line in raw.strip().splitlines())


def _inject_assets_once() -> None:
    if st.session_state.get("_risk_premium_assets_loaded"):
        return

    st.markdown(
        _html_block(
            dedent(
            """
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2-family=Inter:wght@400;500;600;700;800&family=Newsreader:ital,wght@0,400;0,600;0,700;1,700&family=Material+Symbols+Outlined:wght@400;700&display=swap" rel="stylesheet">
            
            """
        )),
        unsafe_allow_html=True,
    )

    st.session_state["_risk_premium_assets_loaded"] = True


def _build_risks(ranking_areas: pd.DataFrame | None) -> list[dict[str, Any]]:
    if isinstance(ranking_areas, pd.DataFrame) and not ranking_areas.empty:
        out: list[dict[str, Any]] = []
        for _, row in ranking_areas.head(8).iterrows():
            score = _safe_float(row.get("score_riesgo", 0.0))
            nombre = _txt(row.get("nombre", row.get("area", "Area")), "Area")
            codigo = _txt(row.get("area", ""), "")

            if score >= 85:
                nivel, cls, row_cls = "CRITICO", "crit", ""
            elif score >= 65:
                nivel, cls, row_cls = "ALTO", "alto", "mid"
            else:
                nivel, cls, row_cls = "MEDIO", "med", "low"

            out.append(
                {
                    "nombre": f"{codigo} - {nombre}" if codigo else nombre,
                    "score": score,
                    "nivel": nivel,
                    "chip_cls": cls,
                    "row_cls": row_cls,
                }
            )
        if out:
            return out[:3]

    return [
        {"nombre": "14 - Ingresos (corte)", "score": 94.0, "nivel": "CRITICO", "chip_cls": "crit", "row_cls": ""},
        {"nombre": "31 - Inventarios", "score": 82.0, "nivel": "ALTO", "chip_cls": "alto", "row_cls": "mid"},
        {"nombre": "47 - Estimaciones", "score": 68.0, "nivel": "MEDIO", "chip_cls": "med", "row_cls": "low"},
    ]


def _build_procedures(risks: list[dict[str, Any]]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for r in risks:
        n = r["nombre"].lower()
        if "ingres" in n or "cxc" in n:
            items.append(
                {
                    "nia": "NIA 505",
                    "title": "Confirmacion Externa de Saldos",
                    "desc": "Confirmar clientes que concentran mayor exposicion de cartera y reforzar pruebas de corte al cierre.",
                    "tag": "Ingresos",
                }
            )
        elif "invent" in n:
            items.append(
                {
                    "nia": "NIA 315",
                    "title": "Walkthrough de Inventarios",
                    "desc": "Validar controles de entradas/salidas y movimientos de ajuste de fin de periodo.",
                    "tag": "Existencias",
                }
            )
        else:
            items.append(
                {
                    "nia": "NIA 540",
                    "title": "Revision de Estimaciones",
                    "desc": "Recalcular supuestos clave y contrastar sensibilidad de escenarios en juicios contables.",
                    "tag": "Estimaciones",
                }
            )
    return (items or [{"nia": "NIA 330", "title": "Respuesta a Riesgos Valorados", "desc": "Alinear pruebas con riesgo valorado.", "tag": "General"}])[:3]


def _load_holding_guidance() -> str:
    try:
        p = Path(__file__).resolve().parents[2] / "data" / "criterio_experto" / "por_sector" / "holding.md"
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def _pick_focus_account(
    variaciones: pd.DataFrame | None,
    risks: list[dict[str, Any]],
) -> tuple[str, str]:
    if isinstance(variaciones, pd.DataFrame) and not variaciones.empty:
        name_col = next(
            (c for c in ["nombre_cuenta", "cuenta", "descripcion", "area_nombre"] if c in variaciones.columns),
            None,
        )
        rel_col = next(
            (c for c in ["variacion_relativa", "variacion_pct", "delta_pct"] if c in variaciones.columns),
            None,
        )
        if name_col:
            if rel_col:
                v = variaciones.copy()
                v["_rel"] = pd.to_numeric(v[rel_col], errors="coerce").abs().fillna(0)
                row = v.sort_values("_rel", ascending=False).iloc[0]
                account = _txt(row.get(name_col, "Cuenta relevante"), "Cuenta relevante")
                rel = _safe_float(row.get("_rel", 0.0))
                return account, f"Variaci-n relativa estimada: {rel:.1f}%"
            row = variaciones.iloc[0]
            account = _txt(row.get(name_col, "Cuenta relevante"), "Cuenta relevante")
            return account, "Movimiento relevante detectado en este rubro."

    if risks:
        return risks[0]["nombre"], "Riesgo priorizado por el motor de áreas."
    return "Ingresos / Cuentas por cobrar", "Rubro sensible por exposici-n de corte y recuperabilidad."


def render_risk_engine_premium(
    cliente: str,
    ranking_areas: pd.DataFrame | None,
    indicadores: dict[str, Any] | None,
    variaciones: pd.DataFrame | None,
    perfil: dict[str, Any] | None,
) -> None:
    indicadores = indicadores or {}
    perfil = perfil or {}

    risks = _build_risks(ranking_areas)
    procedures = _build_procedures(risks)
    _cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente", {}), dict) else {}
    sector = str(_cliente.get("sector", "")).lower()
    is_holding = bool(perfil.get("es_holding")) or ("holding" in sector) or ("sociedad_cartera" in sector)
    holding_guidance = _load_holding_guidance() if is_holding else ""

    alto = int(indicadores.get("areas_alto_riesgo", 0) or 0)
    medio = int(indicadores.get("areas_medio_riesgo", 0) or 0)
    bajo = int(indicadores.get("areas_bajo_riesgo", 0) or 0)
    total = max(1, alto + medio + bajo)
    pct_ctrl = min(70, max(25, int((bajo / total) * 100 + 20)))
    pct_subs = 100 - pct_ctrl

    heat_colors = [
        "#b91c1c", "#dc2626", "#ef4444", "#f97316", "#fb923c",
        "#dc2626", "#ef4444", "#f97316", "#fb923c", "#facc15",
        "#ef4444", "#f97316", "#facc15", "#34d399", "#22c55e",
        "#f97316", "#fb923c", "#34d399", "#22c55e", "#16a34a",
        "#fb923c", "#facc15", "#34d399", "#16a34a", "#15803d",
    ]
    hot_idxs = {0, 2, 10}
    cell_parts: list[str] = []
    for idx, color in enumerate(heat_colors):
        inner = '<span class="rk-dot"></span>' if idx in hot_idxs else ""
        if idx in hot_idxs:
            cell_parts.append(
                f"<div class=\"rk-cell hot\" style=\"background:{color};cursor:pointer;\" "
                f"onclick=\"var el=document.getElementById('riesgos-criticos'); if(el){{el.scrollIntoView({{behavior:'smooth'}});}}\" "
                f"title=\"Ver riesgos criticos\">{inner}</div>"
            )
        else:
            cell_parts.append(f'<div class="rk-cell" style="background:{color};">{inner}</div>')
    cells = "".join(cell_parts)

    risk_cards = "".join(
        [
            f"""
            <div class="rk-risk-card {r['row_cls']}">
                <div>
                    <div style="font-weight:700;font-size:.88rem;">{r['nombre']}</div>
                    <div style="margin-top:.2rem;"><span class="rk-chip {r['chip_cls']}">{r['nivel']}</span></div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.4rem;font-weight:900;color:{'#BA1A1A' if r['nivel']=='CRITICO' else '#B45309' if r['nivel']=='ALTO' else '#64748B'};">{r['score']:.1f}</div>
                    <div style="font-size:.58rem;letter-spacing:.1em;text-transform:uppercase;color:#94A3B8;">Score</div>
                </div>
            </div>
            """
            for r in risks
        ]
    )

    proc_cards = "".join(
        [
            f"""
            <div class="rk-proc-item">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:.5rem;">
                    <span class="rk-nia">{p['nia']}</span>
                    <span class="material-symbols-outlined" style="color:#64748B;">add_circle</span>
                </div>
                <div style="font-weight:700;margin-top:.35rem;">{p['title']}</div>
                <div style="font-size:.82rem;color:#475569;margin-top:.22rem;line-height:1.45;">{p['desc']}</div>
                <div style="margin-top:.35rem;font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;color:#0f766e;font-weight:800;">Vinculado a: {p['tag']}</div>
            </div>
            """
            for p in procedures
        ]
    )

    global_level = str(perfil.get("riesgo_global", {}).get("nivel", "medio")).upper() if isinstance(perfil.get("riesgo_global", {}), dict) else "MEDIO"
    ai_insight = "Se detecta correlacion atipica entre devoluciones y reconocimiento de ingresos de cierre."
    if isinstance(variaciones, pd.DataFrame) and not variaciones.empty and "variacion_relativa" in variaciones.columns:
        max_rel = _safe_float(pd.to_numeric(variaciones["variacion_relativa"], errors="coerce").abs().max(), 0.0)
        ai_insight = f"La variacion relativa maxima observada es {max_rel:.1f}%, lo que sugiere reforzar pruebas de corte y estimaciones clave."
    if is_holding:
        holding_note = (
            " La guía sectorial para holding indica reforzar L/S 14 con revisi-n de VPP/equity method, "
            "conciliaci-n de movimientos del período y consistencia con informaci-n de participadas."
            if "L/S 14 - Inversiones no corrientes" in holding_guidance
            else ""
        )
        ai_insight = (
            "Al ser una Holding, el riesgo no debe explicarse solo por el saldo de la cuenta 14. "
            "El riesgo principal es el reconocimiento del método de participaci-n segon la secci-n correspondiente "
            "de la NIIF para las PYMES (especialmente secci-n 14 cuando aplica a asociadas)."
            + holding_note
        )

    ui_html = dedent(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2-family=Inter:wght@400;500;600;700;800&family=Newsreader:ital,wght@0,400;0,600;0,700;1,700&family=Material+Symbols+Outlined:wght@400;700&display=swap" rel="stylesheet">
        
        <div class="rk-root" style="margin-bottom:.8rem;">
            <span class="rk-kicker">Risk Intelligence Dashboard</span>
            <h1 class="rk-serif rk-title">Matriz de Riesgo Inherente vs. Control</h1>
            <div style="color:#64748B;font-size:.82rem;">Cliente: {_txt(cliente, 'N/D')} | Alto: {alto} - Medio: {medio} - Bajo: {bajo}</div>
        </div>
        <div class="rk-root rk-grid">
            <div class="rk-col-7 rk-card rk-heat-wrap">
                <div style="display:flex;justify-content:space-between;gap:.7rem;align-items:end;flex-wrap:wrap;">
                    <div><h2 class="rk-serif" style="margin:0;font-size:1.65rem;">Matriz de Riesgo</h2></div>
                    <div style="display:flex;gap:.35rem;"><span class="rk-chip crit">ALTO</span><span class="rk-chip med">BAJO</span></div>
                </div>
                <div style="display:flex;gap:.7rem;margin-top:.7rem;align-items:stretch;">
                    <div style="writing-mode:vertical-lr;transform:rotate(180deg);font-size:.58rem;letter-spacing:.12em;text-transform:uppercase;color:#94A3B8;font-weight:800;">Riesgo Inherente</div>
                    <div style="flex:1;"><div class="rk-heat-grid">{cells}</div><div style="display:flex;justify-content:space-between;margin-top:.4rem;font-size:.58rem;color:#94A3B8;letter-spacing:.12em;text-transform:uppercase;font-weight:800;"><span>Remoto</span><span>Riesgo de Control</span><span>Probable</span></div></div>
                </div>
            </div>
            <div class="rk-col-5" style="display:flex;flex-direction:column;gap:.8rem;">
                <div class="rk-strategy"><div class="lbl">Estrategia Recomendada</div><h3 class="rk-serif">Enfoque de Auditoria: <span style="color:#89d3d4;font-style:italic;">Mixto</span></h3><div style="display:flex;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,.14);padding-bottom:.35rem;margin-bottom:.35rem;"><span style="color:#cbd5e1;">Pruebas de Control</span><b style="color:#89d3d4;">{pct_ctrl}%</b></div><div style="display:flex;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,.14);padding-bottom:.35rem;"><span style="color:#cbd5e1;">Procedimientos Sustantivos</span><b style="color:#89d3d4;">{pct_subs}%</b></div><p style="margin:.55rem 0 0 0;color:#cbd5e1;font-size:.8rem;line-height:1.45;">Riesgo global {global_level} con concentracion en cuentas sensibles. Se sugiere reforzar confirmaciones externas y pruebas de integridad al cierre.</p></div>
                <div class="rk-insight"><div style="display:flex;gap:.5rem;align-items:flex-start;"><span class="material-symbols-outlined" style="font-size:1.8rem;">psychology</span><div><div style="font-weight:700;">AI Insight</div><div style="font-size:.8rem;line-height:1.45;margin-top:.2rem;">{ai_insight}</div></div></div></div>
            </div>
            <div class="rk-col-5" id="riesgos-criticos"><h2 class="rk-serif" style="font-size:1.6rem;margin:.15rem 0 .6rem .1rem;">Riesgos Criticos Detectados</h2>{risk_cards}</div>
            <div class="rk-col-7 rk-proc"><div style="display:flex;gap:.5rem;align-items:center;margin-bottom:.65rem;"><span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1; color:#0f766e;">bolt</span><h2 class="rk-serif" style="font-size:1.55rem;margin:0;">Socio AI - Sugerencia de Procedimientos</h2></div>{proc_cards}</div>
        </div>
        <div class="rk-root rk-footer"><span>Socio AI Risk Engine v2.4.0</span><span>Documentation - Methodology - Audit Standards</span></div>
        """
    )
    components.html(ui_html, height=1120, scrolling=False)

    legend_cols = st.columns(4)
    legend_cols[0].markdown("🟥 Critico")
    legend_cols[1].markdown("🟧 Alto")
    legend_cols[2].markdown("  Medio")
    legend_cols[3].markdown("🟩 Bajo")

    def _emoji_for_cell(inh: int, ctl: int) -> str:
        score = inh * ctl
        if score >= 16:
            return "🟥"
        if score >= 10:
            return "🟧"
        if score >= 6:
            return " "
        return "🟩"

    selected_key = f"rk_selected_cell_{cliente}"
    if selected_key not in st.session_state:
        st.session_state[selected_key] = (4, 4)

    # 5x5 clickable matrix: filas = riesgo inherente (5 a 1), columnas = control (1 a 5)
    for inh in range(5, 0, -1):
        cols = st.columns(5)
        for ctl in range(1, 6):
            label = _emoji_for_cell(inh, ctl)
            if cols[ctl - 1].button(label, key=f"rk_cell_{cliente}_{inh}_{ctl}", help=f"Inherente {inh} / Control {ctl}"):
                st.session_state[selected_key] = (inh, ctl)

    inherente, control = st.session_state[selected_key]
    score_mapa = inherente * control
    zona = "Critica" if score_mapa >= 16 else "Alta" if score_mapa >= 10 else "Moderada" if score_mapa >= 6 else "Baja"
    color = "#BA1A1A" if zona == "Critica" else "#B45309" if zona == "Alta" else "#047857"
    accion = (
        "Escalar a socio, ampliar muestra y ejecutar pruebas sustantivas extendidas."
        if zona == "Critica"
        else "Incrementar pruebas de detalle y validar controles compensatorios."
        if zona == "Alta"
        else "Mantener enfoque mixto con seguimiento semanal."
        if zona == "Moderada"
        else "Monitoreo estándar y pruebas de confirmaci-n selectivas."
    )

    st.markdown(
        f"""
        <div style="margin-top:.6rem;padding:.8rem 1rem;border:1px solid #E2E8F0;border-radius:12px;background:#fff;">
            <div style="font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:#64748B;font-weight:800;">Celda Seleccionada</div>
            <div style="margin-top:.2rem;font-weight:700;color:#041627;">Riesgo Inherente {inherente} - Riesgo de Control {control}</div>
            <div style="margin-top:.2rem;font-weight:900;color:{color};">Zona: {zona} ({score_mapa}/25)</div>
            <div style="margin-top:.25rem;color:#475569;font-size:.84rem;">{accion}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    focus_account, focus_detail = _pick_focus_account(variaciones, risks)
    if is_holding:
        focus_account = "L/S 14 - Inversiones no corrientes"
        focus_detail = (
            "Al ser Holding, la evaluaci-n crítica es el método de participaci-n (VPP/equity method) "
            "y su alineaci-n con la secci-n NIIF PYMES aplicable."
        )
    historia = (
        f"En esta zona crítica, la cuenta '{focus_account}' puede concentrar errores materiales. "
        f"{focus_detail} Si el patr-n se confirma, es probable que exista sesgo de corte o debilidad de control."
        if zona == "Critica"
        else f"La cuenta '{focus_account}' merece pruebas adicionales. {focus_detail} "
        "La narrativa sugiere riesgo alto y necesidad de procedimientos de detalle."
        if zona == "Alta"
        else f"La cuenta '{focus_account}' permanece bajo observaci-n. {focus_detail} "
        "La evidencia actual permite un enfoque mixto con monitoreo."
        if zona == "Moderada"
        else f"En zona baja, '{focus_account}' no muestra señales fuertes. {focus_detail} "
        "Se recomienda seguimiento estándar."
    )

    siguiente_paso = (
        "Enviar confirmaciones externas y ampliar muestra de transacciones cercanas al cierre."
        if zona in {"Critica", "Alta"}
        else "Ejecutar walkthrough y pruebas selectivas con recalculo de soportes clave."
    )

    st.markdown(
        f"""
        <div style="margin-top:.7rem;padding:.9rem 1rem;border:1px solid #E2E8F0;border-radius:12px;background:#F8FAFC;">
            <div style="font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:#64748B;font-weight:800;">Historia IA de la Celda</div>
            <div style="margin-top:.35rem;font-weight:800;color:#041627;">Cuenta / Foco: {focus_account}</div>
            <div style="margin-top:.25rem;color:#334155;font-size:.86rem;line-height:1.5;">{historia}</div>
            <div style="margin-top:.35rem;color:#0F766E;font-size:.8rem;font-weight:700;">Siguiente paso recomendado: {siguiente_paso}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    i_col, c_col, go_col = st.columns([2, 2, 2])
    with i_col:
        inherente = st.select_slider(
            "Riesgo Inherente",
            options=[1, 2, 3, 4, 5],
            value=4,
            key=f"rk_inh_{cliente}",
            help="1 bajo - 5 critico",
        )
    with c_col:
        control = st.select_slider(
            "Riesgo de Control",
            options=[1, 2, 3, 4, 5],
            value=4,
            key=f"rk_ctrl_{cliente}",
            help="1 fuerte - 5 debil",
        )

    score_mapa = inherente * control
    zona = "Critica" if score_mapa >= 16 else "Alta" if score_mapa >= 10 else "Moderada" if score_mapa >= 6 else "Baja"
    color = "#BA1A1A" if zona == "Critica" else "#B45309" if zona == "Alta" else "#047857"

    with go_col:
        st.markdown(
            f"<div style='margin-top:1.8rem;font-weight:800;color:{color};'>Zona: {zona} ({score_mapa}/25)</div>",
            unsafe_allow_html=True,
        )

    risk_nav_options: list[tuple[str, str]] = []
    for r in risks:
        label = r["nombre"]
        code = label.split(" - ", 1)[0].strip() if " - " in label else ""
        if code and code.replace(".", "").replace("-", "").isalnum():
            risk_nav_options.append((label, code))

    if risk_nav_options:
        selected_label = st.selectbox(
            "Abrir area relacionada",
            options=[x[0] for x in risk_nav_options],
            index=0,
            key=f"rk_area_sel_{cliente}",
        )
        code = next((c for l, c in risk_nav_options if l == selected_label), "")
        if st.button("Ir a Areas con esta seleccion", key=f"rk_go_area_{cliente}"):
            st.session_state[f"selected_area_{cliente}"] = code
            st.success(f"Area {code} preseleccionada. Abre la pestana '  Areas'.")
