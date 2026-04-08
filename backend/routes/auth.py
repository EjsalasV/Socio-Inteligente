from __future__ import annotations

import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import create_access_token, get_current_user
from backend.repositories.identity_repository import store as identity_store
from backend.schemas import ApiResponse, AuthMeResponse, LoginRequest, TokenResponse, UserContext

router = APIRouter(prefix="/auth", tags=["auth"])

_ADMIN_USER = (
    os.getenv("ADMIN_USERNAME")
    or os.getenv("SOCIO_ADMIN_USER")
    or "joaosalas123@gmail.com"
).strip()
_ADMIN_PASS = (
    os.getenv("ADMIN_PASSWORD")
    or os.getenv("SOCIO_ADMIN_PASSWORD")
    or "1234"
).strip()


def _allowed_clientes() -> list[str]:
    raw = os.getenv("ALLOWED_CLIENTES", "").strip()
    if not raw:
        # Modo seguro por defecto: sin acceso a clientes hasta configurar variable.
        return []
    if raw == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


@router.post("/login", response_model=ApiResponse)
def login(payload: LoginRequest) -> ApiResponse:
    identity_store.ensure_legacy_admin()
    user = identity_store.authenticate(payload.username, payload.password)

    if isinstance(user, dict):
        user_id = str(user.get("user_id") or "").strip()
        allowed = identity_store.get_user_clientes(user_id)
        if not allowed:
            allowed = _allowed_clientes()
        token, ttl = create_access_token(
            sub=str(user.get("username") or payload.username),
            org_id=os.getenv("SOCIO_ORG_ID", "socio-default-org"),
            allowed_clientes=allowed,
            role=str(user.get("role") or "auditor"),
            user_id=user_id,
            display_name=str(user.get("display_name") or user.get("username") or ""),
        )
        return ApiResponse(data=TokenResponse(access_token=token, expires_in=ttl).model_dump())

    # Legacy fallback keeps old installations working even if identity store is empty.
    user_ok = secrets.compare_digest(payload.username, _ADMIN_USER)
    pass_ok = secrets.compare_digest(payload.password, _ADMIN_PASS)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    token, ttl = create_access_token(
        sub=payload.username,
        org_id=os.getenv("SOCIO_ORG_ID", "socio-default-org"),
        allowed_clientes=_allowed_clientes(),
        role="admin",
    )
    return ApiResponse(data=TokenResponse(access_token=token, expires_in=ttl).model_dump())


@router.get("/me", response_model=ApiResponse)
def me(user: UserContext = Depends(get_current_user)) -> ApiResponse:
    return ApiResponse(
        data=AuthMeResponse(
            sub=user.sub,
            user_id=user.user_id,
            display_name=user.display_name or user.sub,
            role=user.role,
            org_id=user.org_id,
            allowed_clientes=user.allowed_clientes,
        ).model_dump()
    )
