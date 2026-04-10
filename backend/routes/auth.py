from __future__ import annotations

import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from backend.auth import AUTH_COOKIE_NAME, AUTH_COOKIE_SAMESITE, AUTH_COOKIE_SECURE, create_access_token, decode_token, get_current_user
from backend.middleware.rate_limit import limiter, LIMITS
from backend.repositories.identity_repository import store as identity_store
from backend.schemas import ApiResponse, AuthMeResponse, LoginRequest, TokenResponse, UserContext

router = APIRouter(prefix="/auth", tags=["auth"])

_ADMIN_USER = (os.getenv("ADMIN_USERNAME") or os.getenv("SOCIO_ADMIN_USER") or "").strip()
_ADMIN_PASS = (os.getenv("ADMIN_PASSWORD") or os.getenv("SOCIO_ADMIN_PASSWORD") or "").strip()


def _allowed_clientes() -> list[str]:
    raw = os.getenv("ALLOWED_CLIENTES", "").strip()
    if not raw:
        # Modo seguro por defecto: sin acceso a clientes hasta configurar variable.
        return []
    if raw == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


def _build_login_response(token: str, ttl: int) -> JSONResponse:
    payload = decode_token(token)
    csrf_token = str(payload.get("csrf") or "").strip()
    body = ApiResponse(
        data=TokenResponse(
            access_token=token,
            expires_in=ttl,
            csrf_token=csrf_token,
        ).model_dump()
    ).model_dump(mode="json")
    response = JSONResponse(content=body, status_code=status.HTTP_200_OK)
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE,
        max_age=ttl,
        path="/",
    )
    return response


@router.post("/login", response_model=ApiResponse)
@limiter.limit(LIMITS["login"])  # 5 intentos por minuto por IP
def login(request: Request, payload: LoginRequest) -> JSONResponse:
    identity_store.ensure_legacy_admin()
    user = identity_store.authenticate(payload.username, payload.password)

    if isinstance(user, dict):
        user_id = str(user.get("user_id") or "").strip()
        role = str(user.get("role") or "auditor").strip().lower()
        allowed = identity_store.get_user_clientes(user_id)
        if not allowed and role in {"admin", "socio"}:
            allowed = _allowed_clientes()
        token, ttl = create_access_token(
            sub=str(user.get("username") or payload.username),
            org_id=os.getenv("SOCIO_ORG_ID", "socio-default-org"),
            allowed_clientes=allowed,
            role=role,
            user_id=user_id,
            display_name=str(user.get("display_name") or user.get("username") or ""),
        )
        return _build_login_response(token, ttl)

    # Legacy fallback: solo si credenciales admin están explícitamente configuradas.
    if _ADMIN_USER and _ADMIN_PASS:
        user_ok = secrets.compare_digest(payload.username, _ADMIN_USER)
        pass_ok = secrets.compare_digest(payload.password, _ADMIN_PASS)
        if user_ok and pass_ok:
            token, ttl = create_access_token(
                sub=payload.username,
                org_id=os.getenv("SOCIO_ORG_ID", "socio-default-org"),
                allowed_clientes=_allowed_clientes(),
                role="admin",
            )
            return _build_login_response(token, ttl)
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales incorrectas",
    )


@router.post("/logout", response_model=ApiResponse)
def logout() -> JSONResponse:
    response = JSONResponse(
        content=ApiResponse(data={"logged_out": True}).model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )
    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/")
    return response


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
