from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.auth import get_current_user
from backend.repositories.file_repository import list_clientes, read_perfil
from backend.schemas import ApiResponse, ClienteSummary, UserContext

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("", response_model=ApiResponse)
def get_clientes(user: UserContext = Depends(get_current_user)) -> ApiResponse:
    out: list[dict] = []
    for cid in list_clientes():
        if "*" not in user.allowed_clientes and cid not in user.allowed_clientes:
            continue
        perfil = read_perfil(cid)
        nombre = str(perfil.get("cliente", {}).get("nombre_legal") or cid)
        sector = perfil.get("cliente", {}).get("sector")
        out.append(ClienteSummary(cliente_id=cid, nombre=nombre, sector=sector).model_dump())
    return ApiResponse(data=out)
