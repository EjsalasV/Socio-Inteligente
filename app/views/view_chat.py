from __future__ import annotations

from typing import Any

import streamlit as st


def render_briefing_ia_tab(
    cliente: str,
    selected_area_code: str,
) -> None:
    """Renders tab7 — Briefing IA content."""
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
                    st.error(f"Error de configuración interna: {ve}")
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
) -> None:
    """Renders tab8 — Chat libre con IA."""
    st.subheader("Chat libre con IA sobre el cliente")
    st.caption(
        f"Contexto activo: {cliente} | "
        "La IA conoce el perfil y datos del cliente."
    )

    # ── Build client context for system prompt ───────────────────
    _perfil_chat = cached_leer_perfil(cliente) or {}
    _nombre_chat = _perfil_chat.get("cliente", {}).get("nombre_legal", cliente)
    _sector_chat = _perfil_chat.get("cliente", {}).get("sector", "N/A")
    _periodo_chat = _perfil_chat.get("encargo", {}).get("anio_activo", "N/A")
    _riesgo_chat = _perfil_chat.get("riesgo_global", {}).get("nivel", "N/A")
    _mat_chat = _perfil_chat.get("materialidad", {}).get("preliminar", {}).get("materialidad_global", "N/A")

    system_chat = (
        f"Eres un socio senior de auditoría financiera especializado en NIAs y NIIF. "
        f"Estás trabajando en el encargo de auditoría del cliente: {_nombre_chat}, "
        f"sector {_sector_chat}, periodo {_periodo_chat}. "
        f"Riesgo global del cliente: {_riesgo_chat}. "
        f"Materialidad global: {_mat_chat}. "
        f"Responde siempre en español con criterio técnico, concreto y accionable. "
        f"Usa formato Markdown para estructurar tus respuestas."
    )

    # ── Chat history in session state ────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input(
        "Pregunta algo sobre el cliente, áreas, riesgos, NIAs..."
    )

    if user_input:
        st.session_state.chat_history.append(
            {"role": "user", "content": user_input}
        )
        with st.chat_message("user"):
            st.markdown(user_input)

        history_text = "\n".join(
            [f"{m['role'].upper()}: {m['content']}"
             for m in st.session_state.chat_history[-6:]]
        )

        # RAG: recuperar contexto normativo relevante
        contexto_normativo = ""
        try:
            from infra.rag.retriever import recuperar_contexto_normativo
            from infra.rag.vector_store import esta_indexado
            if esta_indexado():
                contexto_normativo = recuperar_contexto_normativo(
                    user_input, n_resultados=3
                )
        except Exception:
            pass

        full_prompt = (
            f"Historial de conversación:\n{history_text}"
            f"{chr(10) + contexto_normativo if contexto_normativo else ''}"
            f"\n\nPregunta actual: {user_input}"
        )

        with st.chat_message("assistant"):
            with st.spinner("Consultando a DeepSeek..."):
                response = llamar_llm_seguro(
                    full_prompt,
                    system=system_chat,
                    fallback="No se pudo obtener respuesta. Verifica tu DEEPSEEK_API_KEY.",
                )
            st.markdown(response)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": response}
        )

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("Limpiar conversación", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()
