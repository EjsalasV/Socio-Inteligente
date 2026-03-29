from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import append_audit_log
from backend.schemas import ApiResponse, ChatRequest, ChatResponse, MetodoRequest, MetodoResponse, UserContext
from backend.services.rag_chat_service import generate_chat_response, generate_metodologia_response

router = APIRouter(prefix="/chat", tags=["chat"])


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
    )
    return ApiResponse(data=data.model_dump())


@router.post("/metodologia/{cliente_id}", response_model=ApiResponse)
def post_metodologia_alias(
    cliente_id: str,
    payload: MetodoRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    return post_metodologia(cliente_id=cliente_id, payload=payload, user=user)
