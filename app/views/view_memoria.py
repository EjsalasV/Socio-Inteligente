from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import re

import streamlit as st

from domain.services.leer_perfil import leer_perfil
from domain.services.hallazgos_service import cargar_hallazgos_gestion


def _txt(v: Any, default: str = "N/A") -> str:
    t = str(v or "").strip()
    return t if t else default


def _cliente_dir(cliente: str) -> Path:
    return Path("data") / "clientes" / str(cliente)


def _read_hallazgos_md(cliente: str) -> str:
    p = _cliente_dir(cliente) / "hallazgos.md"
    try:
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    return ""


def _extract_timeline_events(cliente: str) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    raw = _read_hallazgos_md(cliente)
    if raw:
        for ln in raw.splitlines():
            s = ln.strip()
            if not s:
                continue
            if not (s.startswith("-") or s.startswith("*") or s.startswith("##")):
                continue
            years = re.findall(r"(20\d{2})", s)
            year = years[0] if years else "Sin año"
            low = s.lower()
            if "material" in low:
                sev = "material"
                icon = "--"
            elif "signific" in low:
                sev = "significativo"
                icon = "--"
            else:
                sev = "observación"
                icon = "--"
            events.append(
                {
                    "year": year,
                    "icon": icon,
                    "sev": sev,
                    "text": s.lstrip("-*# ").strip(),
                }
            )

    # complemento desde hallazgos_gestion.yaml/remoto
    try:
        h = cargar_hallazgos_gestion(cliente)
        for it in h[:12]:
            if not isinstance(it, dict):
                continue
            d = _txt(it.get("descripcion", "Hallazgo"))
            f = _txt(it.get("fecha_creacion", ""))
            year = f[:4] if len(f) >= 4 and f[:4].isdigit() else "Sin año"
            nivel = _txt(it.get("nivel", "")).lower()
            if nivel == "alto":
                icon = "--"
                sev = "material"
            else:
                icon = "--"
                sev = "significativo"
            events.append({"year": year, "icon": icon, "sev": sev, "text": d})
    except Exception:
        pass

    # dedup simple + orden desc por año
    seen = set()
    uniq: list[dict[str, str]] = []
    for e in events:
        k = (e["year"], e["text"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)
    uniq.sort(key=lambda x: x["year"], reverse=True)
    return uniq[:14]


def _build_alertas_recientes(cliente: str, ranking_areas: Any) -> list[str]:
    out: list[str] = []
    try:
        hs = cargar_hallazgos_gestion(cliente)
        abiertos = [
            x for x in hs if isinstance(x, dict) and _txt(x.get("estado", "")).lower() == "abierto"
        ]
        for h in abiertos[:3]:
            out.append(
                f"Hallazgo {_txt(h.get('id', 'N/A'))}: {_txt(h.get('descripcion', 'Sin descripci-n'))[:88]}"
            )
    except Exception:
        pass
    try:
        if (
            ranking_areas is not None
            and hasattr(ranking_areas, "empty")
            and not ranking_areas.empty
        ):
            cols = ranking_areas.columns.tolist()
            if "score_riesgo" in cols:
                top = ranking_areas.sort_values("score_riesgo", ascending=False).head(2)
                for _, r in top.iterrows():
                    out.append(
                        f"Riesgo alto L/S {_txt(r.get('area', 'N/D'))}: {_txt(r.get('nombre', 'Área'))} ({_txt(r.get('score_riesgo', '0'))})"
                    )
    except Exception:
        pass
    return out[:6] if out else ["Sin alertas críticas recientes."]


def _memo_estrategico(perfil: dict[str, Any], cliente: str) -> str:
    sector = _txt(
        perfil.get("cliente", {}).get("sector", "") if isinstance(perfil, dict) else ""
    ).lower()
    hall = _read_hallazgos_md(cliente).lower()
    if hall:
        if "debil" in hall or "sin soporte" in hall or "no concili" in hall:
            return (
                "La cultura de control muestra brechas recurrentes en documentación y conciliación. "
                "La estrategia debe priorizar disciplina de cierre mensual, trazabilidad de evidencia "
                "y escalamiento temprano de diferencias materiales."
            )
        return (
            "Se observa una cultura de control funcional pero reactiva. "
            "Recomendamos fortalecer controles preventivos, revisión de estimaciones críticas "
            "y monitoreo continuo de desviaciones contra materialidad."
        )
    if "holding" in sector:
        return (
            "Borrador inicial: En un Holding, la cultura de control debe centrarse en gobierno corporativo, "
            "consistencia de método de participación y calidad de revelaciones entre relacionadas."
        )
    if "funer" in sector:
        return (
            "Borrador inicial: En el sector funerario, la cultura de control debe enfocarse en corte de ingresos, "
            "provisiones por servicios futuros y segregaci-n de funciones en caja/contrataci-n."
        )
    return (
        "Borrador inicial: La cultura de control requiere un marco preventivo de riesgos, "
        "matriz de controles clave y disciplina de cierre basada en evidencia verificable."
    )


def render_memoria_tab(
    cliente: str,
    perfil: dict[str, Any] | None = None,
    ranking_areas: Any = None,
) -> None:
    perfil = perfil if isinstance(perfil, dict) and perfil else (leer_perfil(cliente) or {})
    c = perfil.get("cliente", {}) if isinstance(perfil, dict) else {}
    enc = perfil.get("encargo", {}) if isinstance(perfil, dict) else {}
    rg = perfil.get("riesgo_global", {}) if isinstance(perfil, dict) else {}
    mat = perfil.get("materialidad", {}).get("preliminar", {}) if isinstance(perfil, dict) else {}
    industria = perfil.get("industria_inteligente", {}) if isinstance(perfil, dict) else {}

    industria_txt = _txt(c.get("sector", industria.get("sector_base", "N/A")))
    marco_txt = _txt(enc.get("marco_referencial", "N/A"))
    riesgo_txt = _txt(rg.get("nivel", "N/A")).upper()
    mat_plan = _txt(mat.get("materialidad_global", "N/A"))
    alertas = _build_alertas_recientes(cliente, ranking_areas)

    st.markdown(
        "<div class='section-header'>Memoria del Cliente - Archivo Permanente</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([7, 5], gap="large")

    with left:
        st.markdown("<div class='sovereign-card'>", unsafe_allow_html=True)
        st.markdown("#### Perfil del Cliente")
        g1, g2 = st.columns(2)
        with g1:
            st.markdown(f"**Industria:** {_txt(industria_txt)}")
            st.markdown(f"**Marco Contable:** {_txt(marco_txt)}")
        with g2:
            st.markdown(f"**Riesgo Global:** {_txt(riesgo_txt)}")
            st.markdown(f"**Materialidad de Planeaci-n:** {_txt(mat_plan)}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:.55rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='sovereign-card'>", unsafe_allow_html=True)
        st.markdown("#### Repositorio de Documentos")

        cdir = _cliente_dir(cliente)
        files = []
        if cdir.exists():
            for p in cdir.rglob("*"):
                if p.is_file():
                    files.append(p)
        files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
        rows = []
        for p in files[:80]:
            mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            rows.append(
                f"<tr class='tb-row'><td class='tb-detail-name'>{p.name}</td><td>{mtime}</td></tr>"
            )
        table_html = (
            "<div class='tb-shell'><div class='tb-card'><table class='tb-table'>"
            "<thead><tr><th>Documento</th><th>Última modificación</th></tr></thead>"
            f"<tbody>{''.join(rows) if rows else '<tr><td colspan=\"2\">Sin documentos.</td></tr>'}</tbody>"
            "</table></div></div>"
        )
        st.markdown(table_html, unsafe_allow_html=True)

        up = st.file_uploader(
            "Selecciona archivo para incorporar al repositorio",
            key=f"mem_upload_{cliente}",
        )
        if st.button(
            "Cargar Documento", key=f"btn_mem_upload_{cliente}", type="secondary", width="content"
        ):
            if up is None:
                st.warning("Selecciona un archivo antes de cargar.")
            else:
                try:
                    cdir.mkdir(parents=True, exist_ok=True)
                    dest = cdir / up.name
                    dest.write_bytes(up.getvalue())
                    st.success(f"Documento cargado: {up.name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo cargar el documento: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown(
            f"""
            <div class="ai-memo">
              <div style="font-size:.65rem;letter-spacing:.14em;text-transform:uppercase;font-weight:800;opacity:.92;">Memorándum Estratégico AI</div>
              <div class="sv-serif" style="font-style:italic;font-size:1.07rem;line-height:1.56;margin-top:.45rem;">
                {_memo_estrategico(perfil, cliente)}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:.55rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='sovereign-card'>", unsafe_allow_html=True)
        st.markdown("#### Historial de Hallazgos Críticos")
        events = _extract_timeline_events(cliente)
        if not events:
            st.info("Sin historial de hallazgos disponible.")
        else:
            items = []
            for e in events:
                color = "#BA1A1A" if e["icon"] == "--" else "#0B5394"
                items.append(
                    "<div style='position:relative;padding-left:1.1rem;margin:.55rem 0;'>"
                    f"<div style='position:absolute;left:0;top:.18rem;width:.55rem;height:.55rem;border-radius:999px;background:{color};'></div>"
                    f"<div style='font-size:.72rem;color:#64748B;font-weight:700;'>{e['year']} - {e['icon']} {_txt(e['sev'])}</div>"
                    f"<div style='font-size:.83rem;color:#1F2937;'>{_txt(e['text'])}</div>"
                    "</div>"
                )
            st.markdown(
                "<div style='border-left:2px solid #E2E8F0;padding-left:.5rem;'>"
                + "".join(items)
                + "</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:.55rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='sovereign-card'>", unsafe_allow_html=True)
        st.markdown("#### Alertas Recientes")
        for a in alertas:
            st.markdown(f"- {a}")
        st.markdown("</div>", unsafe_allow_html=True)
