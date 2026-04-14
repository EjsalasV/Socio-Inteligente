from __future__ import annotations

"""
Servicio de memoria persistente para el chat de auditoría.

Ciclo de vida:
  - Mensajes recientes (últimos 8)  → se inyectan verbatim al LLM como historial real
  - Mensajes viejos (>20 acumulados) → se comprimen en resumen con el LLM
  - Resúmenes                        → se guardan en chat_memory.json por cliente
                                       y se inyectan como bloque de contexto de sistema

El resumen captura: quién preguntó (rol), qué se discutió, conclusiones alcanzadas.
Así el modelo siempre "recuerda" aunque la conversación supere el límite de contexto.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any

LOGGER = logging.getLogger("socio_ai.memory")

RECENT_WINDOW = 8        # Mensajes recientes inyectados verbatim al LLM
COMPRESS_THRESHOLD = 20  # A partir de cuántos mensajes se activa la compresión
COMPRESS_BATCH = 12      # Cuántos comprimir a la vez (los más viejos)
MAX_SUMMARIES = 20       # Máximo de resúmenes históricos por cliente


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _get_llm_client() -> tuple[Any, str]:
    """Reutiliza el proveedor LLM configurado en el sistema."""
    from backend.services.rag_chat_service import _resolved_provider  # type: ignore[import]
    from openai import OpenAI

    provider, api_key = _resolved_provider()
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "12"))

    if provider == "deepseek":
        base_url = (os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").strip()
        model = os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat").strip() or "deepseek-chat"
        return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout), model

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    return OpenAI(api_key=api_key, timeout=timeout), model


def _label(msg: dict[str, Any]) -> str:
    """Genera etiqueta de autoría: 'Juan (junior)' o 'IA'."""
    if msg.get("role") == "assistant":
        return "IA"
    display = str(msg.get("user_display_name") or msg.get("user_id") or "Auditor")
    role = str(msg.get("user_role") or "").strip()
    return f"{display} ({role})" if role else display


def _format_for_summary(messages: list[dict[str, Any]]) -> str:
    """Formatea mensajes para enviar al LLM de compresión."""
    lines: list[str] = []
    for msg in messages:
        text = str(msg.get("text", "")).strip()
        if msg.get("role") == "assistant":
            lines.append(f"IA: {text[:400]}")
        else:
            lines.append(f"{_label(msg)}: {text}")
    return "\n".join(lines)


def _compress_to_summary(messages: list[dict[str, Any]]) -> str:
    """
    Comprime una lista de mensajes en un resumen estructurado usando el LLM.
    Si el LLM no está disponible cae a resumen determinístico.
    """
    conversation_text = _format_for_summary(messages)

    try:
        client, model = _get_llm_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente de auditoría. Resume esta conversación en 3-5 oraciones "
                        "capturando: quién preguntó (y su rol de auditoría), qué temas de auditoría "
                        "se discutieron, y qué conclusiones o hallazgos importantes se mencionaron. "
                        "Si hay nombres o roles de auditores, inclúyelos. "
                        "Sé concreto, usa terminología de auditoría. Responde en español."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Conversación a resumir:\n\n{conversation_text}",
                },
            ],
            temperature=0.2,
            max_tokens=300,
        )
        if response.choices and response.choices[0].message:
            result = str(response.choices[0].message.content or "").strip()
            if result:
                return result
    except Exception as exc:
        LOGGER.warning("LLM compression failed, using fallback: %s", exc)

    # Fallback determinístico: lista de temas de los mensajes de usuario
    topics = [
        str(m.get("text", ""))[:80]
        for m in messages
        if m.get("role") == "user"
    ]
    return "Conversación anterior sobre: " + "; ".join(topics[:5])


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def build_memory_context(cliente_id: str) -> tuple[str, list[dict[str, str]]]:
    """
    Construye el contexto de memoria para inyectar en el LLM.

    Returns
    -------
    summary_block : str
        Bloque de texto con resúmenes históricos para el system prompt.
        Vacío si no hay historial comprimido previo.
    recent_messages : list[{role, content}]
        Últimos RECENT_WINDOW mensajes formateados para la API de completions.
    """
    from backend.repositories.file_repository import read_chat_history, read_chat_memory

    history = read_chat_history(cliente_id)
    summaries = read_chat_memory(cliente_id)

    # ---- Mensajes recientes (verbatim) ------------------------------------
    recent_raw = history[-RECENT_WINDOW:] if history else []
    recent_messages: list[dict[str, str]] = []

    for msg in recent_raw:
        role = msg.get("role", "")
        text = str(msg.get("text", "")).strip()
        if not text:
            continue
        if role == "user":
            label = _label(msg)
            recent_messages.append({"role": "user", "content": f"[{label}]: {text}"})
        elif role == "assistant":
            recent_messages.append({"role": "assistant", "content": text})

    # ---- Bloque de resúmenes históricos -----------------------------------
    summary_block = ""
    if summaries:
        lines = ["[MEMORIA DEL ENCARGO — conversaciones anteriores resumidas]"]
        for s in summaries[-5:]:
            period = s.get("period", "")
            text = s.get("summary", "")
            if text:
                lines.append(f"• {period}: {text}")
        if len(lines) > 1:
            summary_block = "\n".join(lines)

    return summary_block, recent_messages


def compress_old_messages_if_needed(cliente_id: str) -> None:
    """
    Si el historial supera COMPRESS_THRESHOLD, comprime el batch más viejo
    en un resumen y lo guarda en chat_memory.json.

    Debe llamarse DESPUÉS de guardar la respuesta del asistente en el historial.
    Es seguro llamar siempre — si no supera el umbral no hace nada.
    """
    from backend.repositories.file_repository import (
        read_chat_history,
        read_chat_memory,
        write_chat_history,
        write_chat_memory,
    )

    history = read_chat_history(cliente_id)

    if len(history) <= COMPRESS_THRESHOLD:
        return

    to_compress = history[:COMPRESS_BATCH]
    remaining = history[COMPRESS_BATCH:]

    LOGGER.info(
        "Comprimiendo %d mensajes del encargo %s (%d restantes)",
        len(to_compress),
        cliente_id,
        len(remaining),
    )

    summary_text = _compress_to_summary(to_compress)

    summaries = read_chat_memory(cliente_id)
    summaries.append(
        {
            "period": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "summary": summary_text,
            "message_count": len(to_compress),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    write_chat_memory(cliente_id, summaries[-MAX_SUMMARIES:])
    write_chat_history(cliente_id, remaining)
