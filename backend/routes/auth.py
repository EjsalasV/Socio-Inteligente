from __future__ import annotations

import os
import secrets

from fastapi import APIRouter, HTTPException, status

from backend.auth import create_access_token
from backend.schemas import ApiResponse, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_ADMIN_USER = (
    os.getenv("ADMIN_USERNAME") or os.getenv("SOCIO_ADMIN_USER") or "joaosalas123@gmail.com"
).strip()
_ADMIN_PASS = (os.getenv("ADMIN_PASSWORD") or os.getenv("SOCIO_ADMIN_PASSWORD") or "1234").strip()


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
