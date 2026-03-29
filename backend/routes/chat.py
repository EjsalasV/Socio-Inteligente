from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import append_audit_log, append_hallazgo
from backend.schemas import ApiResponse, ChatRequest, ChatResponse, MetodoRequest, MetodoResponse, UserContext
from backend.services.rag_chat_service import generate_chat_response, generate_metodologia_response

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatExportRequest(BaseModel):
    content: str
    title: str | None = None


@router.post("/{cliente_id}", response_model=ApiResponse)
def post_chat(
    cliente_id: str,
    payload: ChatRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    rag = generate_chat_response(cliente_id, payload.message)

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
    )
    return ApiResponse(data=data.model_dump())


@router.post("/{cliente_id}/metodologia", response_model=ApiResponse)
def post_metodologia(
    cliente_id: str,
    payload: MetodoRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
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
