from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import (
    append_audit_log,
    read_catalog_file,
    read_hallazgos,
    read_perfil,
)
from backend.schemas import ApiResponse, ChatRequest, ChatResponse, MetodoRequest, MetodoResponse, UserContext

router = APIRouter(prefix="/chat", tags=["chat"])
ROOT = Path(__file__).resolve().parents[2]


@router.post("/{cliente_id}", response_model=ApiResponse)
def post_chat(
    cliente_id: str,
    payload: ChatRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)

    perfil = read_perfil(cliente_id)
    hallazgos = read_hallazgos(cliente_id)
    sector = str(perfil.get("cliente", {}).get("sector", "N/D"))

    answer = (
        f"[Socio AI] Cliente {cliente_id} ({sector}). "
        f"Consulta recibida: '{payload.message}'. "
        "Respuesta preliminar basada en perfil y hallazgos del encargo actual."
    )
    if hallazgos.strip():
        answer += " Se incorporó contexto histórico de hallazgos documentados."

    append_audit_log(
        user_id=user.sub,
        cliente_id=cliente_id,
        endpoint="POST /chat/{cliente_id}",
        extra={"message_len": len(payload.message)},
    )

    data = ChatResponse(
        cliente_id=cliente_id,
        answer=answer,
        context_sources=["perfil.yaml", "hallazgos.md"],
    )
    return ApiResponse(data=data.model_dump())


@router.post("/{cliente_id}/metodologia", response_model=ApiResponse)
def post_metodologia(
    cliente_id: str,
    payload: MetodoRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)

    asev = read_catalog_file(ROOT / "data" / "conocimiento_normativo" / "metodologia" / "aseveraciones.md")
    nia315 = read_catalog_file(ROOT / "data" / "conocimiento_normativo" / "nias" / "nia_315.md")

    explanation = (
        f"Para el área {payload.area}, la aseveración clave se determina desde aseveraciones.md "
        "y su relevancia para cierre se sustenta con nia_315.md sobre valoración de riesgos."
    )
    if asev.strip() and nia315.strip():
        explanation += " Ambos documentos fueron cargados en contexto para esta respuesta."

    append_audit_log(
        user_id=user.sub,
        cliente_id=cliente_id,
        endpoint="POST /chat/{cliente_id}/metodologia",
        extra={"area": payload.area},
    )

    data = MetodoResponse(
        cliente_id=cliente_id,
        area=payload.area,
        explanation=explanation,
        context_sources=["aseveraciones.md", "nia_315.md"],
    )
    return ApiResponse(data=data.model_dump())


@router.post("/metodologia/{cliente_id}", response_model=ApiResponse)
def post_metodologia_alias(
    cliente_id: str,
    payload: MetodoRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    return post_metodologia(cliente_id=cliente_id, payload=payload, user=user)
