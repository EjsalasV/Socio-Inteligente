from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import append_audit_log, deep_merge_dict, read_perfil, write_perfil
from backend.schemas import ApiResponse, ClienteProfile, UserContext
from backend.services.view_cache_service import invalidate_view_cache_for_cliente
from backend.validation import validate_perfil_doc_v1

router = APIRouter(prefix="/perfil", tags=["perfil"])


@router.get("/{cliente_id}", response_model=ApiResponse)
def get_perfil(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    perfil = read_perfil(cliente_id)
    return ApiResponse(data=ClienteProfile(cliente_id=cliente_id, perfil=perfil).model_dump())


@router.put("/{cliente_id}", response_model=ApiResponse)
def put_perfil(cliente_id: str, payload: dict, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    current = read_perfil(cliente_id)
    patch = payload if isinstance(payload, dict) else {}
    merged = deep_merge_dict(current, patch)
    is_valid, errors = validate_perfil_doc_v1(merged)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Perfil invalido para schema v1.",
                "errors": errors,
                "schema_version": "v1",
            },
        )
    write_perfil(cliente_id, merged)
    invalidate_view_cache_for_cliente(cliente_id)

    changed_keys: list[str] = []
    for key in patch.keys():
        if current.get(key) != merged.get(key):
            changed_keys.append(str(key))

    append_audit_log(
        user_id=user.sub,
        cliente_id=cliente_id,
        endpoint="PUT /perfil/{cliente_id}",
        extra={"changed_top_level_keys": changed_keys},
    )

    return ApiResponse(data=ClienteProfile(cliente_id=cliente_id, perfil=merged).model_dump())
