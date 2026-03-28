from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import read_perfil, write_perfil
from backend.schemas import ApiResponse, ClienteProfile, UserContext

router = APIRouter(prefix="/perfil", tags=["perfil"])


@router.get("/{cliente_id}", response_model=ApiResponse)
def get_perfil(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    perfil = read_perfil(cliente_id)
    return ApiResponse(data=ClienteProfile(cliente_id=cliente_id, perfil=perfil).model_dump())


@router.put("/{cliente_id}", response_model=ApiResponse)
def put_perfil(cliente_id: str, payload: dict, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    write_perfil(cliente_id, payload)
    return ApiResponse(data=ClienteProfile(cliente_id=cliente_id, perfil=payload).model_dump())
