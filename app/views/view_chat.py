from __future__ import annotations

from pathlib import Path
from typing import Any
import re

import streamlit as st


def _txt(value: Any, default: str = "") -> str:
    t = str(value or "").strip()
    return t if t else default


def _cliente_dir(cliente: str) -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "clientes" / str(cliente)


def _hallazgos_path(cliente: str) -> Path:
    return _cliente_dir(cliente) / "hallazgos.md"


def _read_hallazgos(cliente: str) -> str:
    p = _hallazgos_path(cliente)
    try:
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    return ""


def _summarize_hallazgos(md_text: str, max_lines: int = 8) -> str:
    if not md_text.strip():
        return "Sin hallazgos documentados."
    lines = []
    for ln in md_text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        if ln.startswith("#") or ln.startswith("-") or ln.startswith("*"):
            lines.append(ln)
        if len(lines) >= max_lines:
            break
    return "\n".join(lines) if lines else md_text[:1200]


def _append_consulta_tecnica(cliente: str, content: str) -> tuple[bool, str]:
    p = _hallazgos_path(cliente)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        old = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        section_title = "## Consultas Técnicas"
        block = f"\n- {content.strip()}\n"
        if section_title in old:
            new = old.rstrip() + block
        else:
            new = (old.rstrip() + f"\n\n{section_title}\n" + block).strip() + "\n"
        p.write_text(new, encoding="utf-8")
        return True, str(p)
    except Exception as e:
        return False, str(e)


def _infer_alertas_recientes(
    ranking_areas: Any = None,
    variaciones: Any = None,
) -> list[str]:
    out: list[str] = []
    try:
        if ranking_areas is not None and hasattr(ranking_areas, "empty") and not ranking_areas.empty:
            cols = ranking_areas.columns.tolist()
            if "score_riesgo" in cols:
                top = ranking_areas.sort_values("score_riesgo", ascending=False).head(3)
                for _, r in top.iterrows():
                    out.append(
                        f"{_txt(r.get('area', 'L/S'))} {_txt(r.get('nombre', 'Área'))}: score {_txt(r.get('score_riesgo', '0'))}"
                    )
    except Exception:
        pass
    try:
        if variaciones is not None and hasattr(variaciones, "empty") and not variaciones.empty:
            col_n = "nombre" if "nombre" in variaciones.columns else "nombre_cuenta" if "nombre_cuenta" in variaciones.columns else None
            col_i = "impacto" if "impacto" in variaciones.columns else "variacion_absoluta" if "variacion_absoluta" in variaciones.columns else None
            if col_n and col_i:
                topv = variaciones.copy().head(2)
                for _, r in topv.iterrows():
                    out.append(f"Variaci-n relevante: {_txt(r.get(col_n, 'Cuenta'))} ({_txt(r.get(col_i, '0'))})")
    except Exception:
        pass
    return out[:5]


def render_briefing_ia_tab(
    cliente: str,
    selected_area_code: str,
) -> None:
    """Renders tab7 " Briefing IA content."""
    st.subheader("Briefing de Área con IA (DeepSeek)")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        area_briefing_input = st.text_input(
            "C-digo área L/S para briefing", value=selected_area_code or "14"
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
                st.markdown("**Criterio del socio (IA)**")
                st.markdown(resultado)
            except ValueError as ve:
                msg = str(ve)
                if "DEEPSEEK_API_KEY" in msg or "OPENAI_API_KEY" in msg:
                    st.error(
                        f"Falta API key: {ve}. "
                        "Agrega DEEPSEEK_API_KEY a tu archivo .env y reinicia la app."
                    )
                else:
                    st.error(f"Error de configuraci-n interna: {ve}")
            except Exception as ex:
                st.error(f"Error al generar briefing: {ex}")

    st.info(
        "Requiere DEEPSEEK_API_KEY en el archivo .env del proyecto. "
        "Si no tienes clave, el resto de la app funciona sin IA."
    )


def render_chat_tab(
    cliente: str,
    cached_leer_perfil: Any,
    llamar_llm_seguro: Any,
    ranking_areas: Any = None,
    variaciones: Any = None,
    alertas_recientes: list[str] | None = None,
) -> None:
    """Renders Socio Chat with editorial premium memo layout."""
    perfil = cached_leer_perfil(cliente) or {}
    cliente_info = perfil.get("cliente", {}) if isinstance(perfil, dict) else {}
    riesgo_info = perfil.get("riesgo_global", {}) if isinstance(perfil, dict) else {}
    mat_info = perfil.get("materialidad", {}).get("preliminar", {}) if isinstance(perfil, dict) else {}

    nombre = _txt(cliente_info.get("nombre_legal"), cliente)
    sector = _txt(cliente_info.get("sector"), "N/A")
    riesgo = _txt(riesgo_info.get("nivel"), "N/A").upper()
    mat_planeacion = _txt(mat_info.get("materialidad_global"), "N/A")

    hallazgos_raw = _read_hallazgos(cliente)
    hallazgos_resumen = _summarize_hallazgos(hallazgos_raw)

    if alertas_recientes is None:
        alertas = _infer_alertas_recientes(ranking_areas=ranking_areas, variaciones=variaciones)
    else:
        alertas = alertas_recientes
    if not alertas:
        alertas = ["Sin alertas recientes del motor de riesgos."]

    system_chat = (
        "Eres un socio senior de auditoría financiera especializado en NIAs y NIIF. "
        f"Cliente: {nombre} | Sector: {sector} | Riesgo global: {riesgo} | Materialidad planeaci-n: {mat_planeacion}. "
        "Responde siempre en español con criterio técnico, concreto y accionable.\n\n"
        "Memoria de hallazgos del encargo (resumen):\n"
        f"{hallazgos_resumen}\n\n"
        "Cuando aplique, conecta tu respuesta con hallazgos previos documentados."
    )

    state_key = f"socio_chat_history_{cliente}"
    if state_key not in st.session_state:
        st.session_state[state_key] = []

    col_main, col_ctx = st.columns([3, 1], gap="large")

    with col_ctx:
        st.markdown(
            f"""
            <div class="sovereign-card" style="position:sticky;top:80px;">
              <div style="font-size:.62rem;letter-spacing:.14em;text-transform:uppercase;font-weight:800;color:#64748B;">Contexto del Encargo</div>
              <div style="margin-top:.4rem;font-size:.85rem;color:#334155;"><b>Sector:</b> {sector}</div>
              <div style="margin-top:.2rem;font-size:.85rem;color:#334155;"><b>Riesgo Global:</b> {riesgo}</div>
              <div style="margin-top:.2rem;font-size:.85rem;color:#334155;"><b>Materialidad de Planeaci-n:</b> {mat_planeacion}</div>
              <div style="margin-top:.7rem;font-size:.67rem;letter-spacing:.11em;text-transform:uppercase;font-weight:800;color:#64748B;">Alertas Recientes</div>
              <ul style="margin:.45rem 0 0 .95rem;padding:0;font-size:.8rem;color:#475569;line-height:1.45;">
                {''.join([f'<li>{a}</li>' for a in alertas])}
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_main:
        st.markdown("### Socio Chat")
        st.caption(f"Cliente activo: {nombre}")

        for idx, msg in enumerate(st.session_state[state_key]):
            role = msg.get("role", "assistant")
            content = _txt(msg.get("content"), "")

            if role == "user":
                st.markdown(
                    f"""
                    <div class="sovereign-card" style="margin-bottom:.6rem;border-left:4px solid #1a2b3c;">
                      <div style="font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;font-weight:800;color:#64748B;">Consulta del Equipo</div>
                      <div style="margin-top:.3rem;color:#0F172A;">{content}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                continue

            st.markdown(
                f"""
                <div class="ai-memo" style="margin-bottom:.45rem;">
                  <div style="font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;font-weight:800;opacity:.95;">Opinión Técnica de Auditoría</div>
                  <div style="font-size:.78rem;opacity:.9;margin-top:.2rem;">Ref: NIA-315 / NIIF-15</div>
                  <div class="sv-serif" style="font-style:italic;font-size:1.05rem;line-height:1.58;margin-top:.45rem;">{content}</div>
                  <div style="margin-top:.7rem;font-size:.72rem;opacity:.85;">Firma Digital de IA - Socio AI</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("📌 Vincular a Papel de Trabajo", key=f"link_pt_{cliente}_{idx}", width="content"):
                ok, detail = _append_consulta_tecnica(cliente, content)
                if ok:
                    st.success("Respuesta vinculada a Consultas Técnicas en hallazgos.md")
                else:
                    st.error(f"No se pudo vincular: {detail}")

        user_input = st.text_area(
            "Consulta técnica",
            key=f"socio_chat_input_{cliente}",
            placeholder="Ejemplo: ¿C-mo debo sustentar el riesgo en CxC considerando el hallazgo de diferencia de $45k-",
            height=90,
        )
        send = st.button("Enviar consulta", key=f"socio_chat_send_{cliente}", type="primary")

        if send and _txt(user_input):
            st.session_state[state_key].append({"role": "user", "content": user_input})
            history_text = "\n".join(
                [f"{m.get('role', '').upper()}: {m.get('content', '')}" for m in st.session_state[state_key][-8:]]
            )

            contexto_normativo = ""
            try:
                from infra.rag.retriever import recuperar_contexto_normativo
                from infra.rag.vector_store import esta_indexado
                if esta_indexado():
                    contexto_normativo = recuperar_contexto_normativo(user_input, n_resultados=3)
            except Exception:
                pass

            prompt = (
                "Historial de conversaci-n:\n"
                f"{history_text}\n\n"
                "Hallazgos documentados del cliente:\n"
                f"{hallazgos_resumen}\n"
                f"{chr(10) + contexto_normativo if contexto_normativo else ''}\n"
                f"Pregunta actual: {user_input}"
            )

            with st.spinner("Analizando criterio técnico..."):
                response = llamar_llm_seguro(
                    prompt,
                    system=system_chat,
                    fallback="No se pudo obtener respuesta. Verifica tu configuraci-n de IA.",
                )
            st.session_state[state_key].append({"role": "assistant", "content": response})
            st.rerun()

        if st.session_state[state_key]:
            if st.button("Limpiar conversaci-n", key=f"clear_chat_{cliente}"):
                st.session_state[state_key] = []
                st.rerun()
