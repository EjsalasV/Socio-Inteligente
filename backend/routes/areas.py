from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import append_hallazgo, repo
from backend.schemas import (
    ApiResponse,
    AreaCheckRequest,
    AreaConclusionRequest,
    AreaWorkspaceResponse,
    UserContext,
)

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("/{cliente_id}/{area_code}", response_model=ApiResponse)
def get_area(cliente_id: str, area_code: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    detail = repo.get_area_detail(cliente_id, area_code)
    return ApiResponse(data=AreaWorkspaceResponse(**detail).model_dump())


@router.patch("/{cliente_id}/{area_code}/cuentas/{cuenta_codigo}/check", response_model=ApiResponse)
def patch_check(
    cliente_id: str,
    area_code: str,
    cuenta_codigo: str,
    payload: AreaCheckRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    result = repo.set_area_account_check(cliente_id, area_code, cuenta_codigo, payload.checked)
    return ApiResponse(data={"saved": True, **result})


@router.put("/{cliente_id}/{area_code}/conclusion", response_model=ApiResponse)
def put_conclusion(
    cliente_id: str,
    area_code: str,
    payload: AreaConclusionRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    if not payload.conclusion.strip():
        raise HTTPException(status_code=422, detail="conclusion cannot be empty")
    append_hallazgo(cliente_id, f"## Área {area_code}\n\n{payload.conclusion.strip()}")
    return ApiResponse(data={"saved": True, "cliente_id": cliente_id, "area_code": area_code})
