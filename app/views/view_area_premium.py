from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st


def _fmt_money(value: Any) -> str:
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "$0.00"


def _fmt_pct(value: Any, decimals: int = 1) -> str:
    try:
        return f"{float(value):.{decimals}f}%"
    except Exception:
        return "0.0%"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _txt(value: Any, default: str = "") -> str:
    raw = value if value is not None else default
    text = str(raw).strip()
    if not text:
        text = default
    return escape(text)


def _to_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _badge_html(text: str, kind: str = "default") -> str:
    css = {
        "error": "badge-error",
        "warning": "badge-warning",
        "success": "badge-success",
        "state": "badge-state",
        "default": "badge-default",
    }.get(kind, "badge-default")
    return f'<span class="soc-badge {css}">{escape(text)}</span>'


def _priority_from_text(text: str) -> str:
    t = text.lower()
    high_words = ["crit", "urg", "bloq", "inmediat", "alto", "venc", "hallazgo"]
    medium_words = ["media", "revis", "valid", "pend", "niif", "nia"]
    if any(w in t for w in high_words):
        return "alta"
    if any(w in t for w in medium_words):
        return "media"
    return "baja"


def _task_item_html(task: str, priority: str, bloqueante: bool = False) -> str:
    p = priority.lower()
    if bloqueante:
        return (
            '<div class="task-meta">'
            '<span class="task-chip chip-block">BLOQUEANTE</span>'
            '<span class="task-chip chip-high">ALTA</span>'
            "</div>"
        )
    if p == "alta":
        return (
            '<div class="task-meta">'
            '<span class="task-chip chip-high">ALTA</span>'
            "</div>"
        )
    if p == "media":
        return (
            '<div class="task-meta">'
            '<span class="task-chip chip-mid">MEDIA</span>'
            "</div>"
        )
    return (
        '<div class="task-meta">'
        '<span class="task-chip chip-low">BAJA</span>'
        "</div>"
    )


def _alert_card_html(titulo: str, mensaje: str, nivel: str = "medio") -> str:
    lvl = (nivel or "medio").strip().lower()
    if lvl == "alto":
        klass = "alert-card alert-high"
        label = "ALERTA CRITICA"
    elif lvl == "medio":
        klass = "alert-card alert-mid"
        label = "ALERTA MEDIA"
    else:
        klass = "alert-card alert-low"
        label = "ALERTA"

    return f"""
    <div class=\"{klass}\">
        <div class=\"alert-label\">{escape(label)}</div>
        <div class=\"alert-title\">{escape(titulo or 'Alerta de auditoria')}</div>
        <div class=\"alert-msg\">{escape(mensaje or 'Sin detalle')}</div>
    </div>
    """


def _inject_assets_once() -> None:
    if st.session_state.get("_premium_assets_loaded"):
        return

    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Newsreader:ital,wght@0,400;0,600;0,700;1,400&family=Material+Symbols+Outlined:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --soc-primary: #041627;
                --soc-error: #BA1A1A;
                --soc-medium: #B45309;
                --soc-success: #047857;
                --soc-surface: #F7FAFC;
                --soc-border: #E2E8F0;
                --soc-muted: #64748B;
                --soc-white: #FFFFFF;
            }
            .soc-root { font-family: 'Inter', sans-serif; color: var(--soc-primary); }
            .soc-title { font-family: 'Newsreader', serif; letter-spacing: -0.02em; }
            .soc-card { background: var(--soc-white); border: 1px solid var(--soc-border); border-radius: 18px; }
            .soc-hero { padding: 1.25rem; }
            .soc-badge { display:inline-block; padding:.35rem .65rem; border-radius:.5rem; font-size:.66rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
            .badge-error { background: var(--soc-error); color:#fff; }
            .badge-warning { background: #FEF3C7; color:#78350F; border:1px solid #FDE68A; }
            .badge-success { background: #DCFCE7; color:#065F46; border:1px solid #A7F3D0; }
            .badge-state { background: #E2E8F0; color: #334155; }
            .badge-default { background: #EEF2FF; color: #334155; }

            .decision-wrap { border-radius: 28px; padding: 6px; box-shadow: 0 16px 35px rgba(15, 23, 42, .18); }
            .decision-danger { background: linear-gradient(140deg, #BA1A1A 0%, #7F1010 90%); }
            .decision-ok { background: linear-gradient(140deg, #047857 0%, #065F46 90%); }
            .decision-inner { border-radius: 24px; padding: 1.3rem; color:#fff; }
            .decision-title { font-family: 'Newsreader', serif; font-size: 2.1rem; font-weight: 700; line-height: 1.05; }
            .decision-sub { color: rgba(255,255,255,.88); }
            .counter-pill { background: rgba(0,0,0,.22); border:1px solid rgba(255,255,255,.18); border-radius: 12px; padding:.5rem .7rem; margin-top:.45rem; }
            .counter-k { font-size:.65rem; letter-spacing:.12em; text-transform:uppercase; color:rgba(255,255,255,.75); font-weight:800; }
            .counter-v { font-size:1.25rem; font-weight:800; }

            .metric-card { border-radius: 16px; padding: .95rem 1rem; background: #fff; border:1px solid var(--soc-border); }
            .metric-label { font-size:.65rem; text-transform:uppercase; letter-spacing:.12em; color:#94A3B8; font-weight:800; }
            .metric-value { font-size:2.05rem; line-height:1; margin-top:.6rem; font-family:'Newsreader', serif; font-weight:700; }
            .metric-sub { color: var(--soc-muted); font-size:.74rem; margin-top:.5rem; }
            .progress-track { height:6px; background:#E5E7EB; border-radius:999px; overflow:hidden; margin-top:.6rem; }
            .progress-fill { height:100%; border-radius:999px; }

            .opinion-wrap { border: 3px solid var(--soc-primary); border-radius: 22px; overflow: hidden; background: #fff; }
            .opinion-head { background: var(--soc-primary); color: #fff; padding: .8rem 1rem; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; font-weight:800; display:flex; gap:.45rem; align-items:center; }
            .opinion-body { padding: 1rem 1.1rem; }
            .opinion-list { margin:.25rem 0 0 1rem; padding:0; }
            .opinion-list li { margin:.35rem 0; }
            .quote-block { border-left: 4px solid var(--soc-border); padding-left: .9rem; color:#334155; }

            .table-wrap { background: #fff; border: 1px solid var(--soc-border); border-radius: 18px; overflow: hidden; }
            .table-head { padding: .9rem 1rem; border-bottom:1px solid #EEF2F7; background:#F8FAFC; display:flex; justify-content:space-between; align-items:center; gap:.6rem; }
            .table-title { font-family: 'Newsreader', serif; font-size:1.3rem; font-weight:700; }
            .soc-btn { display:inline-block; font-size:.64rem; letter-spacing:.1em; text-transform:uppercase; padding:.45rem .6rem; border-radius:.55rem; font-weight:800; border:1px solid var(--soc-border); background:#fff; color:#334155; }
            .soc-btn.primary { background: var(--soc-primary); border-color: var(--soc-primary); color:#fff; }
            .soc-table { width:100%; border-collapse:collapse; }
            .soc-table th { text-align:left; font-size:.64rem; color:#94A3B8; text-transform:uppercase; letter-spacing:.11em; padding:.7rem .9rem; border-bottom:1px solid #EEF2F7; }
            .soc-table td { padding:.75rem .9rem; border-bottom:1px solid #F1F5F9; font-size:.86rem; color:#1E293B; }
            .state-chip { padding:.2rem .45rem; border-radius:.45rem; font-size:.62rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; display:inline-block; }
            .state-ok { background:#DCFCE7; color:#065F46; border:1px solid #A7F3D0; }
            .state-pending { background:#FEE2E2; color:#991B1B; border:1px solid #FECACA; }
            .state-plan { background:#F1F5F9; color:#475569; border:1px solid #CBD5E1; }
            .state-progress { background:#FEF3C7; color:#92400E; border:1px solid #FDE68A; }

            .side-card { background:#fff; border:1px solid var(--soc-border); border-radius:20px; padding:1rem; }
            .side-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:.8rem; }
            .task-row { border:1px solid var(--soc-border); border-radius:12px; padding:.6rem .7rem; margin-bottom:.5rem; }
            .task-row.block { border: 2px solid var(--soc-error); background: #FEF2F2; }
            .task-meta { margin-top:.35rem; display:flex; gap:.35rem; }
            .task-chip { font-size:.58rem; font-weight:800; letter-spacing:.1em; border-radius:.4rem; padding:.15rem .3rem; text-transform:uppercase; }
            .chip-block { background: var(--soc-error); color:#fff; }
            .chip-high { background:#FEE2E2; color:#991B1B; border:1px solid #FECACA; }
            .chip-mid { background:#FEF3C7; color:#92400E; border:1px solid #FDE68A; }
            .chip-low { background:#F1F5F9; color:#475569; border:1px solid #CBD5E1; }

            .alert-card { border-radius: 16px; padding: .8rem .9rem; border:1px solid var(--soc-border); }
            .alert-high { background: #0F172A; border-left: 6px solid var(--soc-error); color:#fff; }
            .alert-mid { background: #fff; border-left: 6px solid #F59E0B; }
            .alert-low { background: #fff; border-left: 6px solid #10B981; }
            .alert-label { font-size:.6rem; text-transform:uppercase; letter-spacing:.12em; font-weight:800; opacity:.8; }
            .alert-title { margin-top:.3rem; font-weight:700; font-size:.86rem; }
            .alert-msg { margin-top:.3rem; font-size:.8rem; line-height:1.4; }

            .flow-card { background:#F8FAFC; border:1px solid var(--soc-border); border-radius:20px; padding:1rem; }
            .flow-line { position:relative; margin-left:.45rem; border-left:2px solid #CBD5E1; padding-left:1.05rem; }
            .flow-step { position:relative; margin-bottom:.95rem; }
            .flow-dot { position:absolute; left:-1.48rem; top:.2rem; width:.78rem; height:.78rem; border-radius:999px; border:2px solid #CBD5E1; background:#fff; }
            .flow-step.done .flow-dot { background: var(--soc-success); border-color: var(--soc-success); box-shadow: 0 0 0 3px rgba(4, 120, 87, .16); }
            .flow-step.active .flow-dot { background: var(--soc-primary); border-color: var(--soc-primary); animation: socPulse 1.2s infinite; }
            .flow-step.future { opacity:.55; }
            .flow-name { font-size:.72rem; font-weight:800; text-transform:uppercase; letter-spacing:.1em; }
            .flow-sub { font-size:.72rem; color: var(--soc-muted); }

            @keyframes socPulse {
                0% { box-shadow: 0 0 0 0 rgba(4, 22, 39, .32); }
                70% { box-shadow: 0 0 0 10px rgba(4, 22, 39, 0); }
                100% { box-shadow: 0 0 0 0 rgba(4, 22, 39, 0); }
            }

            div[data-testid="stCheckbox"] label p {
                font-size: .84rem !important;
                color: #0F172A !important;
                font-weight: 600 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.session_state["_premium_assets_loaded"] = True


def _stage_status(current_stage: str, step: str) -> str:
    order = ["planificacion", "ejecucion", "cierre"]
    current = (current_stage or "").strip().lower()
    if current not in order:
        current = "planificacion"
    cur_idx = order.index(current)
    step_idx = order.index(step)
    if step_idx < cur_idx:
        return "done"
    if step_idx == cur_idx:
        return "active"
    return "future"


def _render_header(ws: dict[str, Any], cliente: str) -> None:
    area_name = _txt(ws.get("area_name", "Área sin nombre"), "Área sin nombre")
    codigo_ls = _txt(ws.get("codigo_ls", "-"), "-")
    score = _safe_float(ws.get("area_score", 0.0))
    riesgo = _txt(ws.get("riesgo", "MEDIO"), "MEDIO").upper()

    if score >= 70 or riesgo == "ALTO":
        risk_badge = _badge_html(f"RIESGO {riesgo}", "error")
        score_color = "#BA1A1A"
    elif score >= 40 or riesgo == "MEDIO":
        risk_badge = _badge_html(f"RIESGO {riesgo}", "warning")
        score_color = "#B45309"
    else:
        risk_badge = _badge_html(f"RIESGO {riesgo}", "success")
        score_color = "#047857"

    etapa = _txt(ws.get("etapa", "en revisión").replace("_", " "), "en revisión").upper()
    estado_badge = _badge_html(etapa, "state")

    mat_rel = _safe_float(ws.get("materialidad_relativa", 0.0))
    mat_exec = _safe_float(ws.get("materialidad_ejecucion", 0.0))

    st.markdown(
        f"""
        <div class="soc-root soc-card soc-hero">
            <div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;align-items:flex-start;">
                <div>
                    <div style="display:flex;gap:.45rem;flex-wrap:wrap;">{risk_badge}{estado_badge}</div>
                    <h2 class="soc-title" style="font-size:3rem;line-height:1.02;margin:.55rem 0 .25rem 0;">{area_name} - LS {codigo_ls}</h2>
                    <div style="color:#64748B;font-size:.85rem;">Cliente: {escape(cliente or 'N/D')}</div>
                </div>
                <div class="soc-card" style="padding:.85rem 1rem;display:flex;gap:1rem;align-items:center;">
                    <div>
                        <div class="metric-label">Risk Score</div>
                        <div class="soc-title" style="font-size:2.1rem;color:{score_color};">{score:.1f}</div>
                    </div>
                    <div style="width:1px;height:48px;background:#E2E8F0;"></div>
                    <div>
                        <div class="metric-label">Materialidad Relativa / Ejecución</div>
                        <div class="soc-title" style="font-size:1.42rem;color:#041627;">{_fmt_pct(mat_rel)} / {_fmt_money(mat_exec)}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_decision_critica(ws: dict[str, Any]) -> None:
    hallazgos_count = _safe_int(ws.get("hallazgos_count", 0))
    pending_count = _safe_int(ws.get("pending_count", 0))
    coverage = _safe_float(ws.get("coverage", 0.0))

    no_lista = hallazgos_count > 0 or pending_count > 0 or coverage < 80
    wrap_cls = "decision-danger" if no_lista else "decision-ok"
    title = "NO LISTA PARA CIERRE" if no_lista else "LISTA PARA CIERRE"
    subtitle = (
        "El área presenta condiciones críticas que requieren remediación antes del cierre."
        if no_lista
        else "El área cumple condiciones para avanzar al cierre sin bloqueos críticos."
    )

    focos = [_txt(x) for x in _to_list(ws.get("focos")) if str(x).strip()][:4]
    if not focos:
        focos = ["Sin acciones requeridas registradas."]

    focos_html = "".join(
        [
            f'<div style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);padding:.55rem .65rem;border-radius:10px;font-size:.82rem;">{f}</div>'
            for f in focos
        ]
    )

    st.markdown(
        f"""
        <div class="soc-root decision-wrap {wrap_cls}">
            <div class="decision-inner">
                <div style="display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;flex-wrap:wrap;">
                    <div style="max-width:72%;min-width:300px;">
                        <div class="decision-title">ESTADO: {title}</div>
                        <p class="decision-sub" style="margin:.45rem 0 0 0;">{escape(subtitle)}</p>
                    </div>
                    <div style="min-width:200px;">
                        <div class="counter-pill"><div class="counter-k">Hallazgos Abiertos</div><div class="counter-v">{hallazgos_count:02d}</div></div>
                        <div class="counter-pill"><div class="counter-k">Pendientes Críticos</div><div class="counter-v">{pending_count:02d}</div></div>
                    </div>
                </div>
                <div style="margin-top:.9rem;border-top:1px solid rgba(255,255,255,.2);padding-top:.8rem;">
                    <div style="font-size:.66rem;letter-spacing:.12em;text-transform:uppercase;font-weight:800;color:rgba(255,255,255,.85);margin-bottom:.45rem;">Acciones Requeridas</div>
                    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.45rem;">{focos_html}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_metric_card(label: str, value: str, sub: str, value_color: str, progress: float | None = None) -> str:
    progress_html = ""
    if progress is not None:
        p = max(0.0, min(100.0, progress))
        bar_color = "#047857" if p >= 80 else "#B45309" if p >= 60 else "#BA1A1A"
        progress_html = (
            f'<div class="progress-track"><div class="progress-fill" style="width:{p:.1f}%;background:{bar_color};"></div></div>'
        )
    return f"""
    <div class="metric-card soc-root">
        <div class="metric-label">{escape(label)}</div>
        <div class="metric-value" style="color:{value_color};">{escape(value)}</div>
        <div class="metric-sub">{escape(sub)}</div>
        {progress_html}
    </div>
    """


def _render_metrics(ws: dict[str, Any]) -> None:
    coverage = _safe_float(ws.get("coverage", 0.0))
    hallazgos_count = _safe_int(ws.get("hallazgos_count", 0))
    pending_count = _safe_int(ws.get("pending_count", 0))

    calidad = ws.get("calidad_metodologia") if isinstance(ws.get("calidad_metodologia"), dict) else {}
    resumen = calidad.get("resumen") if isinstance(calidad.get("resumen"), dict) else {}
    alertas_criticas = _safe_int(resumen.get("alertas_criticas", 0))

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            _render_metric_card("Cobertura de Auditoría", _fmt_pct(coverage, 0), "Cobertura sobre procedimientos esperados", "#041627", coverage),
            unsafe_allow_html=True,
        )
    with c2:
        color = "#BA1A1A" if hallazgos_count > 0 else "#047857"
        st.markdown(
            _render_metric_card("Hallazgos de Auditoría", str(hallazgos_count), "Abiertos en el área", color),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            _render_metric_card("Tareas Pendientes", str(pending_count), "Procedimientos no cerrados", "#041627"),
            unsafe_allow_html=True,
        )
    with c4:
        color = "#BA1A1A" if alertas_criticas > 0 else "#047857"
        st.markdown(
            _render_metric_card("Alertas Críticas de Calidad", str(alertas_criticas), "Control metodológico", color),
            unsafe_allow_html=True,
        )


def _render_opinion(ws: dict[str, Any]) -> None:
    riesgos = ws.get("riesgos") if isinstance(ws.get("riesgos"), list) else []
    focos = [_txt(x) for x in _to_list(ws.get("focos")) if str(x).strip()][:3]
    lectura = _txt(ws.get("lectura", "Sin lectura inicial disponible."), "Sin lectura inicial disponible.")

    risk_items: list[str] = []
    for r in riesgos[:3]:
        if isinstance(r, dict):
            titulo = _txt(r.get("titulo", "Riesgo relevante"), "Riesgo relevante")
            descripcion = _txt(r.get("descripcion", ""), "")
            risk_items.append(f"<li><b>{titulo}</b>{(': ' + descripcion) if descripcion else ''}</li>")

    if not risk_items:
        risk_items = ["<li>Sin riesgos priorizados para este corte.</li>"]

    focos_items = "".join([f"<li>{f}</li>" for f in focos]) if focos else "<li>Sin recomendaciones estratégicas registradas.</li>"
    risks_html = "".join(risk_items)

    st.markdown(
        f"""
        <div class="soc-root opinion-wrap">
            <div class="opinion-head">
                <span class="material-symbols-outlined" style="font-size:18px;">verified_user</span>
                OPINIÓN OFICIAL DE SOCIO IA
            </div>
            <div class="opinion-body">
                <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:.12em;color:#64748B;font-weight:800;">Resumen de Riesgos Principales</div>
                <ul class="opinion-list">{risks_html}</ul>
                <div class="quote-block" style="margin-top:.75rem;">
                    <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:.12em;color:#64748B;font-weight:800;">Lectura Inicial</div>
                    <p style="margin:.35rem 0 0 0;">{lectura}</p>
                </div>
                <div style="margin-top:.75rem;">
                    <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:.12em;color:#64748B;font-weight:800;">Recomendaciones Estratégicas</div>
                    <ul class="opinion-list">{focos_items}</ul>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _estado_chip(estado: str) -> str:
    norm = (estado or "").strip().lower()
    if norm == "ejecutado":
        return '<span class="state-chip state-ok">EJECUTADO</span>'
    if norm == "pendiente":
        return '<span class="state-chip state-pending">PENDIENTE</span>'
    if norm in {"en_proceso", "en proceso"}:
        return '<span class="state-chip state-progress">EN PROCESO</span>'
    if norm == "planificado":
        return '<span class="state-chip state-plan">PLANIFICADO</span>'
    return f'<span class="state-chip state-plan">{escape((estado or "N/D").upper())}</span>'


def _render_table(ws: dict[str, Any]) -> None:
    proc_df = ws.get("proc_df")
    rows_html = ""

    if isinstance(proc_df, pd.DataFrame) and not proc_df.empty:
        for _, row in proc_df.iterrows():
            rid = _txt(row.get("id", "-"), "-")
            desc = _txt(row.get("descripcion", "Sin descripción"), "Sin descripción")
            estado = _txt(row.get("estado", "planificado"), "planificado")
            rows_html += (
                "<tr>"
                f"<td>{rid}</td>"
                f"<td>{desc}</td>"
                f"<td>{_estado_chip(estado)}</td>"
                "</tr>"
            )

    if not rows_html:
        rows_html = "<tr><td>-</td><td>Sin procedimientos cargados.</td><td><span class='state-chip state-plan'>N/D</span></td></tr>"

    st.markdown(
        f"""
        <div class="soc-root table-wrap">
            <div class="table-head">
                <div>
                    <div class="table-title">Procedimientos del Área</div>
                    <div style="font-size:.74rem;color:#64748B;">Muestra de ejecución y estado operativo</div>
                </div>
                <div>
                    <span class="soc-btn">Exportar</span>
                    <span class="soc-btn primary">Ver Detalle</span>
                </div>
            </div>
            <div style="overflow-x:auto;">
                <table class="soc-table">
                    <thead>
                        <tr><th>ID</th><th>Descripción</th><th>Estado</th></tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_pendientes(ws: dict[str, Any]) -> None:
    pendientes = [_txt(x) for x in _to_list(ws.get("pendientes")) if str(x).strip()]
    hallazgos_open = _safe_int(ws.get("hallazgos_count", 0)) > 0

    st.markdown(
        f"""
        <div class="soc-root side-card">
            <div class="side-head">
                <h4 class="soc-title" style="margin:0;font-size:1.5rem;">Pendientes</h4>
                <span class="soc-badge badge-default">{len(pendientes)} TOTAL</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not pendientes:
        st.markdown(
            '<div class="soc-root task-row"><b>Sin pendientes activos.</b></div>',
            unsafe_allow_html=True,
        )
        return

    for idx, p in enumerate(pendientes):
        bloqueante = idx == 0 and hallazgos_open
        priority = _priority_from_text(p)
        row_cls = "task-row block" if bloqueante else "task-row"
        label_html = _task_item_html(p, priority, bloqueante=bloqueante)

        st.markdown(f'<div class="soc-root {row_cls}">', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 16])
        with c1:
            st.checkbox("", key=f"premium_task_{idx}_{abs(hash(p)) % 10_000}")
        with c2:
            st.markdown(f"<div style='font-size:.85rem;font-weight:700;'>{p}</div>{label_html}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def _render_alertas(ws: dict[str, Any]) -> None:
    hallazgos = [_txt(h) for h in _to_list(ws.get("hallazgos")) if str(h).strip()]
    expert_flags = ws.get("expert_flags") if isinstance(ws.get("expert_flags"), list) else []

    st.markdown('<div class="soc-root" style="display:flex;flex-direction:column;gap:.55rem;">', unsafe_allow_html=True)

    if not hallazgos and not expert_flags:
        st.markdown(_alert_card_html("Sin alertas", "No se detectan alertas activas para este corte.", "bajo"), unsafe_allow_html=True)

    for h in hallazgos:
        st.markdown(_alert_card_html("Hallazgo abierto", h, "medio"), unsafe_allow_html=True)

    for flag in expert_flags:
        if not isinstance(flag, dict):
            continue
        nivel = _txt(flag.get("nivel", "medio"), "medio").lower()
        titulo = _txt(flag.get("titulo", "Señal experta"), "Señal experta")
        mensaje = _txt(flag.get("mensaje", "Sin detalle"), "Sin detalle")
        if nivel == "alto":
            st.markdown(_alert_card_html(titulo, mensaje, "alto"), unsafe_allow_html=True)
        elif nivel == "medio":
            st.markdown(_alert_card_html(titulo, mensaje, "medio"), unsafe_allow_html=True)
        else:
            st.markdown(_alert_card_html(titulo, mensaje, "bajo"), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _render_stepper(ws: dict[str, Any]) -> None:
    etapa = _txt(ws.get("etapa", "planificacion"), "planificacion").lower()
    steps = [
        ("planificacion", "Planificación"),
        ("ejecucion", "Ejecución"),
        ("cierre", "Cierre"),
    ]

    steps_html = ""
    for code, label in steps:
        status = _stage_status(etapa, code)
        sub = "Completado" if status == "done" else "Activo" if status == "active" else "Pendiente"
        steps_html += (
            f'<div class="flow-step {status}">'
            '<div class="flow-dot"></div>'
            f'<div class="flow-name">{escape(label)}</div>'
            f'<div class="flow-sub">{escape(sub)}</div>'
            "</div>"
        )

    st.markdown(
        f"""
        <div class="soc-root flow-card">
            <div style="font-size:.66rem;text-transform:uppercase;letter-spacing:.12em;color:#64748B;font-weight:800;margin-bottom:.65rem;">Historial / Flujo</div>
            <div class="flow-line">{steps_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_area_premium(ws: dict, cliente: str, datos_clave: dict, perfil: dict) -> None:
    if not ws:
        return

    _inject_assets_once()

    _render_header(ws, cliente)
    _render_decision_critica(ws)
    _render_metrics(ws)

    main_col, side_col = st.columns([8, 4])

    with main_col:
        _render_opinion(ws)
        _render_table(ws)

    with side_col:
        _render_pendientes(ws)
        _render_alertas(ws)
        _render_stepper(ws)


# Compatibilidad temporal con el flujo previo del app_streamlit.
def render_area_hero_premium(ws: dict[str, Any]) -> None:
    _inject_assets_once()
    _render_header(ws or {}, cliente="")


def render_decision_block_premium(ws: dict[str, Any]) -> None:
    _inject_assets_once()
    _render_decision_critica(ws or {})


def render_metric_cards_premium(ws: dict[str, Any]) -> None:
    _inject_assets_once()
    _render_metrics(ws or {})


def render_executive_summary_premium(ws: dict[str, Any]) -> None:
    _inject_assets_once()
    _render_opinion(ws or {})


def render_ai_opinion_premium(ws: dict[str, Any]) -> None:
    _inject_assets_once()
    _render_opinion(ws or {})


def render_pending_system_premium(ws: dict[str, Any]) -> None:
    _inject_assets_once()
    _render_pendientes(ws or {})


def render_alerts_premium(ws: dict[str, Any]) -> None:
    _inject_assets_once()
    _render_alertas(ws or {})
