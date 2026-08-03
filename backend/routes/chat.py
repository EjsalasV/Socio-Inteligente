from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from backend.auditor_pipeline import execute_pipeline
from backend.auth import authorize_cliente_access, get_current_user
from backend.middleware.rate_limit import limiter, LIMITS
from backend.repositories.file_repository import (
    append_audit_log,
    append_chat_message,
    append_hallazgo,
    list_area_codes,
    read_chat_history,
)
from backend.repositories.identity_repository import store as identity_store
from backend.services.memory_service import compress_old_messages_if_needed
from backend.services.chat_conversation_service import (
    create_conversation, delete_conversation, ensure_conversation,
    list_conversations, rename_conversation,
)
from backend.schemas import ApiResponse, ChatRequest, ChatResponse, MetodoRequest, MetodoResponse, UserContext
from backend.services.rag_chat_service import generate_chat_response, generate_metodologia_response

router = APIRouter(prefix="/chat", tags=["chat"])
LOGGER = logging.getLogger("socio_ai.chat")


class ChatExportRequest(BaseModel):
    content: str
    title: str | None = None


class ConversationCreateRequest(BaseModel):
    title: str = "Nueva conversación"


class ConversationRenameRequest(BaseModel):
    title: str


def _is_true(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _select_area_code(cliente_id: str) -> str:
    codes = list_area_codes(cliente_id)
    if not codes:
        return "140"
    # Prefer active balance areas when available.
    for preferred in ["140", "130", "200", "14"]:
        if preferred in codes:
            return preferred
    return str(codes[0])


def _run_chat_engine(
    cliente_id: str,
    message: str,
    *,
    user_sub: str = "",
    user_display_name: str = "",
    user_role: str = "",
    learning_role: str = "semi",
    conversation_id: str = "",
) -> dict:
    # El chat principal debe sentirse conversacional.
    # El pipeline estructurado se puede activar de forma explicita para chat si se requiere.
    use_pipeline = _is_true(os.getenv("USE_AUDITOR_PIPELINE_CHAT"))
    if not use_pipeline:
        return generate_chat_response(
            cliente_id,
            message,
            user_sub=user_sub,
            user_display_name=user_display_name,
            user_role=user_role,
            learning_role=learning_role,
            conversation_id=conversation_id,
        )

    try:
        return execute_pipeline(
            cliente_id=cliente_id,
            codigo_area=_select_area_code(cliente_id),
            modo="consulta_rapida",
            senales_python={},
            consulta_adicional=message,
        )
    except Exception as exc:
        LOGGER.exception(
            f"Pipeline failed for cliente={cliente_id}, message={message[:100]}",
            exc_info=True,
        )
        return generate_chat_response(
            cliente_id,
            message,
            user_sub=user_sub,
            user_display_name=user_display_name,
            user_role=user_role,
        )


@router.post("/{cliente_id}", response_model=ApiResponse)
@limiter.limit(LIMITS["chat"])  # 20 mensajes por minuto por IP
def post_chat(
    request: Request,
    cliente_id: str,
    payload: ChatRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    conversation = ensure_conversation(
        cliente_id,
        payload.conversation_id or create_conversation(cliente_id)["id"],
        payload.message,
    )

    # Obtener learning_role del usuario
    try:
        prefs = identity_store.get_preferences(user.sub)
        learning_role = str(prefs.get("learning_role") or "semi").strip().lower()
    except Exception:
        learning_role = "semi"

    rag = _run_chat_engine(
        cliente_id,
        payload.message,
        user_sub=user.sub,
        user_display_name=user.display_name or user.sub,
        user_role=user.role or "",
        learning_role=learning_role,
        conversation_id=str(conversation["id"]),
    )
    append_chat_message(
        cliente_id,
        {
            "role": "user",
            "text": payload.message,
            "user_id": user.sub,
            "user_display_name": user.display_name or user.sub,
            "user_role": user.role or "",
            "conversation_id": conversation["id"],
        },
    )

    append_audit_log(
        user_id=user.sub,
        cliente_id=cliente_id,
        endpoint="POST /chat/{cliente_id}",
        extra={"message_len": len(payload.message)},
    )

    data = ChatResponse(
        cliente_id=cliente_id,
        answer=str(rag.get("answer", "")),
        context_sources=[str(x) for x in rag.get("context_sources", []) if str(x).strip()],
        citations=[c for c in rag.get("citations", []) if isinstance(c, dict)],
        confidence=float(rag.get("confidence", 0.0) or 0.0),
        prompt_id=str((rag.get("prompt_meta") or {}).get("prompt_id") or ""),
        prompt_version=str((rag.get("prompt_meta") or {}).get("prompt_version") or ""),
        mode_used=str(rag.get("mode_used") or "chat"),
        expert_criteria_used=bool(rag.get("expert_criteria_used", False)),
    )
    append_chat_message(
        cliente_id,
        {
            "role": "assistant",
            "text": data.answer,
            "citations": data.citations,
            "confidence": data.confidence,
            "prompt_id": data.prompt_id,
            "prompt_version": data.prompt_version,
            "user_id": user.sub,
            "conversation_id": conversation["id"],
        },
    )
    # Comprimir historial si supera el umbral (no bloquea la respuesta)
    try:
        compress_old_messages_if_needed(cliente_id)
    except Exception:
        pass
    response_data = data.model_dump()
    response_data["conversation_id"] = conversation["id"]
    return ApiResponse(data=response_data)


@router.get("/{cliente_id}/history", response_model=ApiResponse)
def get_chat_history(cliente_id: str, conversation_id: str = "", user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    rows = read_chat_history(cliente_id)
    safe_rows: list[dict] = []
    selected = [row for row in rows if not conversation_id or row.get("conversation_id") == conversation_id]
    for row in selected[-120:]:
        if not isinstance(row, dict):
            continue
        safe_rows.append(
            {
                "role": str(row.get("role") or ""),
                "text": str(row.get("text") or ""),
                "timestamp": str(row.get("timestamp") or ""),
                "citations": row.get("citations") if isinstance(row.get("citations"), list) else [],
                "confidence": float(row.get("confidence") or 0.0) if row.get("confidence") is not None else 0.0,
            }
        )
    return ApiResponse(data={"messages": safe_rows})


@router.get("/{cliente_id}/conversations", response_model=ApiResponse)
def get_conversations(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    return ApiResponse(data={"conversations": list_conversations(cliente_id)})


@router.post("/{cliente_id}/conversations", response_model=ApiResponse)
def post_conversation(cliente_id: str, payload: ConversationCreateRequest, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    return ApiResponse(data={"conversation": create_conversation(cliente_id, payload.title)})


@router.patch("/{cliente_id}/conversations/{conversation_id}", response_model=ApiResponse)
def patch_conversation(cliente_id: str, conversation_id: str, payload: ConversationRenameRequest, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    row = rename_conversation(cliente_id, conversation_id, payload.title)
    if row is None:
        raise_api_error(status_code=404, code="CONVERSATION_NOT_FOUND", message="Conversación no encontrada.")
    return ApiResponse(data={"conversation": row})


@router.delete("/{cliente_id}/conversations/{conversation_id}", response_model=ApiResponse)
def remove_conversation(cliente_id: str, conversation_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    if not delete_conversation(cliente_id, conversation_id):
        raise_api_error(status_code=404, code="CONVERSATION_NOT_FOUND", message="Conversación no encontrada.")
    return ApiResponse(data={"deleted": True})


@router.post("/{cliente_id}/metodologia", response_model=ApiResponse)
def post_metodologia(
    cliente_id: str,
    payload: MetodoRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    use_pipeline = _is_true(os.getenv("USE_AUDITOR_PIPELINE"))
    if use_pipeline:
        try:
            rag = execute_pipeline(
                cliente_id=cliente_id,
                codigo_area=str(payload.area or _select_area_code(cliente_id)),
                modo="briefing",
                senales_python={},
                consulta_adicional=f"Metodologia y procedimientos para area {payload.area}",
            )
        except Exception:
            rag = generate_metodologia_response(cliente_id, payload.area)
    else:
        rag = generate_metodologia_response(cliente_id, payload.area)

    append_audit_log(
        user_id=user.sub,
        cliente_id=cliente_id,
        endpoint="POST /chat/{cliente_id}/metodologia",
        extra={"area": payload.area},
    )

    data = MetodoResponse(
        cliente_id=cliente_id,
        area=payload.area,
        explanation=str(rag.get("answer", "")),
        context_sources=[str(x) for x in rag.get("context_sources", []) if str(x).strip()],
        citations=[c for c in rag.get("citations", []) if isinstance(c, dict)],
        confidence=float(rag.get("confidence", 0.0) or 0.0),
        prompt_id=str((rag.get("prompt_meta") or {}).get("prompt_id") or ""),
        prompt_version=str((rag.get("prompt_meta") or {}).get("prompt_version") or ""),
    )
    return ApiResponse(data=data.model_dump())


@router.post("/metodologia/{cliente_id}", response_model=ApiResponse)
def post_metodologia_alias(
    cliente_id: str,
    payload: MetodoRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    return post_metodologia(cliente_id=cliente_id, payload=payload, user=user)


@router.post("/{cliente_id}/export", response_model=ApiResponse)
def post_chat_export(
    cliente_id: str,
    payload: ChatExportRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    text = payload.content.strip()
    if not text:
        return ApiResponse(data={"saved": False, "reason": "empty_content"})

    title = (payload.title or "Criterio exportado desde Socio Chat").strip()
    append_hallazgo(cliente_id, f"## {title}\n\n{text}")

    append_audit_log(
        user_id=user.sub,
        cliente_id=cliente_id,
        endpoint="POST /chat/{cliente_id}/export",
        extra={"title": title, "content_len": len(text)},
    )
    return ApiResponse(data={"saved": True, "title": title})
