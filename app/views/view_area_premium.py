from __future__ import annotations

from html import escape
from typing import Any
from pathlib import Path
from datetime import datetime
import re

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yaml


def _fmt_money(value: Any) -> str:
    try:
        v = float(value)
        if v < 0:
            return f"(${abs(v):,.2f})"
        return f"${v:,.2f}"
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

    etapa = _txt(ws.get("etapa", "en revisi - n").replace("_", " "), "en revisi - n").upper()
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
                        <div class="metric-label">Materialidad Relativa / Ejecuci-n</div>
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
        "El área presenta condiciones críticas que requieren remediaci-n antes del cierre."
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
        <div class="soc-root soc-decision decision-wrap {wrap_cls}">
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
            _render_metric_card("Alertas Críticas de Calidad", str(alertas_criticas), "Control metodol-gico", color),
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
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
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
                    <div style="font-size:.74rem;color:#64748B;">Muestra de ejecuci-n y estado operativo</div>
                </div>
                <div>
                    <span class="soc-btn">Exportar</span>
                    <span class="soc-btn primary">Ver Detalle</span>
                </div>
            </div>
            <div style="overflow-x:auto;">
                <table class="soc-table">
                    <thead>
                        <tr><th>ID</th><th>Descripci-n</th><th>Estado</th></tr>
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
        ("planificacion", "Planificaci-n"),
        ("ejecucion", "Ejecuci-n"),
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


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(data, dict):
                return data
    except Exception:
        return {}
    return {}


def _nia_reference_for_proc(proc: dict[str, Any], nia_available: set[str]) -> str:
    p_tipo = _txt(proc.get("tipo", "")).lower()
    p_desc = _txt(proc.get("descripcion", "")).lower()
    if "confirm" in p_tipo or "circular" in p_desc:
        return "NIA 505" if "505" in nia_available else "NIA 500"
    if "analit" in p_tipo:
        return "NIA 520" if "520" in nia_available else "NIA 500"
    if "muestra" in p_desc or "muest" in p_desc:
        return "NIA 530" if "530" in nia_available else "NIA 500"
    return "NIA 500" if "500" in nia_available else "NIA 330"


def _suggest_procedures(
    ws: dict[str, Any],
    perfil: dict[str, Any],
    proc_catalog: dict[str, Any],
    nia_available: set[str],
) -> list[dict[str, Any]]:
    codigo_ls = _txt(ws.get("codigo_ls", ""))
    area_data = proc_catalog.get(codigo_ls, {}) if isinstance(proc_catalog.get(codigo_ls, {}), dict) else {}
    procs = area_data.get("procedimientos", []) if isinstance(area_data.get("procedimientos", []), list) else []
    if not procs:
        return []

    riesgo = _txt(ws.get("riesgo", "MEDIO"), "MEDIO").upper()
    area_score = _safe_float(ws.get("area_score", 0.0))
    risk_high = riesgo == "ALTO" or area_score >= 70 or _safe_int(ws.get("hallazgos_count", 0)) > 0
    sector = _txt(
        perfil.get("cliente", {}).get("sector", perfil.get("sector", ""))
        if isinstance(perfil, dict)
        else ""
    ).lower()
    is_holding_14 = ("holding" in sector) and (codigo_ls == "14")

    ranked: list[tuple[float, dict[str, Any]]] = []
    for p in procs:
        if not isinstance(p, dict):
            continue
        score = 0.0
        descripcion = _txt(p.get("descripcion", "")).lower()
        afirmacion = _txt(p.get("afirmacion", "")).lower()
        tipo = _txt(p.get("tipo", "")).lower()
        if bool(p.get("obligatorio", False)):
            score += 3.0
        if risk_high and "valuacion" in afirmacion:
            score += 2.5
        if risk_high and "confirm" in tipo:
            score += 1.8
        if is_holding_14 and (
            "vpp" in descripcion
            or "particip" in descripcion
            or "inversion" in descripcion
        ):
            score += 4.2
        if "corte" in afirmacion:
            score += 0.8
        p2 = dict(p)
        p2["nia_ref"] = _nia_reference_for_proc(p2, nia_available)
        ranked.append((score, p2))

    ranked.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in ranked[:3]]


def _render_copy_block(md_text: str, key: str) -> None:
    safe_text = md_text.replace("`", "'")
    html = f"""
    <div style="margin-top:.5rem;">
      <textarea id="{key}_txt" style="width:100%;height:220px;border:1px solid #E2E8F0;border-radius:12px;padding:10px;background:#fff;color:#0F172A;">{escape(safe_text)}</textarea>
      <button id="{key}_btn" style="margin-top:.5rem;border:0;background:#041627;color:#fff;border-radius:10px;padding:.5rem .85rem;font-weight:700;cursor:pointer;">
        Copiar al portapapeles
      </button>
      <span id="{key}_msg" style="margin-left:.55rem;color:#047857;font-size:.83rem;"></span>
    </div>
    <script>
      const btn = document.getElementById("{key}_btn");
      const txt = document.getElementById("{key}_txt");
      const msg = document.getElementById("{key}_msg");
      btn.addEventListener("click", async () => {{
        try {{
          await navigator.clipboard.writeText(txt.value);
          msg.textContent = "Copiado";
        }} catch(e) {{
          msg.textContent = "No se pudo copiar";
        }}
      }});
    </script>
    """
    components.html(html, height=300)


def _render_workspace_execution(ws: dict[str, Any], cliente: str, perfil: dict[str, Any]) -> None:
    root = _project_root()
    asev_path = root / "data" / "catalogos" / "aseveraciones_guia_ls.yaml"
    proc_path = root / "data" / "catalogos" / "procedimientos_por_area.yaml"
    nia_dir = root / "data" / "conocimiento_normativo" / "nias"

    asev_catalog = _load_yaml(asev_path)
    proc_catalog = _load_yaml(proc_path)
    nia_available = set()
    if nia_dir.exists():
        for f in nia_dir.glob("nia_*.md"):
            m = re.search(r"nia_(\d+)", f.stem.lower())
            if m:
                nia_available.add(m.group(1))

    codigo_ls = _txt(ws.get("codigo_ls", ""))
    asev_data = asev_catalog.get(codigo_ls, {}) if isinstance(asev_catalog.get(codigo_ls, {}), dict) else {}
    aseveraciones = asev_data.get("aseveraciones_sugeridas", []) if isinstance(asev_data.get("aseveraciones_sugeridas", []), list) else []
    if not aseveraciones:
        aseveraciones = _to_list(ws.get("cobertura", {}).get("esperadas", [])) if isinstance(ws.get("cobertura", {}), dict) else []

    riesgo = _txt(ws.get("riesgo", "MEDIO"), "MEDIO").upper()
    area_score = _safe_float(ws.get("area_score", 0.0))
    risk_high = riesgo == "ALTO" or area_score >= 70 or _safe_int(ws.get("hallazgos_count", 0)) > 0

    suggested = _suggest_procedures(ws, perfil, proc_catalog, nia_available)

    st.markdown("<div class='section-header'>Workspace de Ejecuci-n</div>", unsafe_allow_html=True)
    col_asev, col_proc = st.columns([1, 2], gap="large")

    with col_asev:
        st.markdown("<div class='sovereign-card'>", unsafe_allow_html=True)
        st.markdown("**Aseveraciones Clave**")
        if aseveraciones:
            for a in aseveraciones:
                a_txt = _txt(a)
                priority = (
                    '<span class="soc-badge badge-error" style="margin-left:.35rem;">Prioridad Alta</span>'
                    if risk_high and a_txt.lower() == "valuacion"
                    else ""
                )
                st.markdown(
                    f"""
                    <div style="border:1px solid #E2E8F0;background:#F8FAFC;border-radius:12px;padding:.55rem .65rem;margin-bottom:.4rem;">
                      <span style="font-weight:700;color:#041627;">{a_txt}</span>{priority}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No se encontraron aseveraciones guía para esta área.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_proc:
        st.markdown("<div class='sovereign-card'>", unsafe_allow_html=True)
        st.markdown("**Procedimientos sugeridos por riesgo**")
        if suggested:
            for i, p in enumerate(suggested, start=1):
                pid = _txt(p.get("id", f"PROC-{i}"))
                pdesc = _txt(p.get("descripcion", "Sin descripción"))
                paf = _txt(p.get("afirmacion", "N/D"))
                nia = _txt(p.get("nia_ref", "NIA 500"))
                st.checkbox(
                    f"{pid} - {pdesc}",
                    key=f"ws_proc_{codigo_ls}_{i}_{pid}",
                    value=False,
                )
                st.markdown(
                    f"<div style='margin:-.2rem 0 .5rem 1.9rem;font-size:.78rem;color:#64748B;'>"
                    f"Aseveración: <b>{paf}</b> - Referencia: <b>{nia}</b></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No hay procedimientos catalogados para esta área.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:.4rem;'></div>", unsafe_allow_html=True)
    if st.button("-- -- Generar Ficha de Ejecuci-n", key=f"btn_ficha_exec_{codigo_ls}", type="primary"):
        me = _safe_float(ws.get("materialidad_ejecucion", 0.0))
        cuentas_rel = _safe_int(ws.get("area_summary", {}).get("cuentas_relevantes", 0)) if isinstance(ws.get("area_summary", {}), dict) else 0
        muestra = max(5, min(35, cuentas_rel if cuentas_rel > 0 else int((me / 10000.0) if me else 8)))
        proc_lineas = []
        for idx, p in enumerate(suggested[:3], start=1):
            proc_lineas.append(f"{idx}. {p.get('descripcion', 'Procedimiento')}")
        proc_txt = "<br>".join([escape(x) for x in proc_lineas]) if proc_lineas else "1. Sin procedimiento sugerido"
        asev_target = ", ".join([_txt(a) for a in aseveraciones[:2]]) if aseveraciones else "Valuaci-n"
        riesgo_txt = _txt(ws.get("riesgo", "MEDIO"), "MEDIO").upper()

        ficha = (
            "| Riesgo Identificado | Aseveración atacada | Procedimiento paso a paso | Muestra sugerida |\n"
            "|---|---|---|---|\n"
            f"| Riesgo {riesgo_txt} en área LS {codigo_ls} | {asev_target} | {proc_txt} | {muestra} elementos |\n"
        )
        st.markdown("<div class='sovereign-card'>", unsafe_allow_html=True)
        st.markdown("**Ficha de Ejecuci-n (copiable a Excel)**")
        st.markdown(ficha)
        _render_copy_block(ficha, key=f"copy_ficha_{codigo_ls}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:.35rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sovereign-card'>", unsafe_allow_html=True)
    st.markdown("**Documentar Conclusi-n**")
    hall_path = root / "data" / "clientes" / str(cliente) / "hallazgos.md"
    if f"conclusion_ws_{codigo_ls}_{cliente}" not in st.session_state:
        existing = ""
        try:
            if hall_path.exists():
                existing = hall_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            existing = ""
        st.session_state[f"conclusion_ws_{codigo_ls}_{cliente}"] = existing

    concl = st.text_area(
        "Conclusi-n del área",
        key=f"conclusion_ws_{codigo_ls}_{cliente}",
        height=150,
        placeholder="Documenta evidencia, conclusi-n y pendientes finales...",
    )
    if st.button("Guardar conclusi-n local", key=f"save_concl_{codigo_ls}_{cliente}"):
        try:
            hall_path.parent.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            current = ""
            if hall_path.exists():
                current = hall_path.read_text(encoding="utf-8", errors="replace")
            block = (
                f"\n\n## {ws.get('area_name', 'Área')} (LS {codigo_ls})\n"
                f"- Fecha: {stamp}\n"
                f"- Riesgo: {ws.get('riesgo', 'N/D')}\n\n"
                f"{concl.strip()}\n"
            )
            hall_path.write_text((current + block).strip() + "\n", encoding="utf-8")
            st.success("Conclusi-n guardada en hallazgos.md")
        except Exception as e:
            st.error(f"No se pudo guardar la conclusi-n: {e}")
    st.markdown("</div>", unsafe_allow_html=True)


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
        _render_workspace_execution(ws, cliente, perfil if isinstance(perfil, dict) else {})
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


def _render_cierre_cards(ws: dict[str, Any]) -> None:
    """Render editorial closure cards used by legacy intelligence/memory tabs."""
    _inject_assets_once()
    ws = ws or {}

    hallazgos_count = _safe_int(ws.get("hallazgos_count", 0))
    pendientes_count = _safe_int(ws.get("pending_count", 0))
    focos = [str(x).strip() for x in _to_list(ws.get("focos")) if str(x).strip()]
    hallazgos = [str(x).strip() for x in _to_list(ws.get("hallazgos")) if str(x).strip()]
    pendientes = [str(x).strip() for x in _to_list(ws.get("pendientes")) if str(x).strip()]

    st.markdown(
        """
        <div class="section-header">Cierre del Area</div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="sovereign-card">
              <div class="metric-label">Hallazgos Abiertos</div>
              <div class="metric-value" style="color:{'#BA1A1A' if hallazgos_count > 0 else '#047857'};">{hallazgos_count}</div>
              <div class="metric-sub">{escape(hallazgos[0]) if hallazgos else 'Sin hallazgos materiales abiertos.'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="sovereign-card">
              <div class="metric-label">Pendientes Criticos</div>
              <div class="metric-value" style="color:{'#B45309' if pendientes_count > 0 else '#047857'};">{pendientes_count}</div>
              <div class="metric-sub">{escape(pendientes[0]) if pendientes else 'No hay pendientes bloqueantes.'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="sovereign-card">
              <div class="metric-label">Acciones Requeridas</div>
              <div class="metric-value" style="font-size:1.65rem;color:#041627;">{len(focos)}</div>
              <div class="metric-sub">{escape(focos[0]) if focos else 'Sin acciones nuevas definidas.'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if focos:
        items = "".join(
            [f"<li style='margin:.3rem 0;'>{escape(x)}</li>" for x in focos[:5]]
        )
        st.markdown(
            f"""
            <div class="sovereign-card" style="margin-top:.6rem;">
              <div class="metric-label">Plan de Cierre Prioritario</div>
              <ul style="margin:.45rem 0 0 1rem; color:#334155;">{items}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
