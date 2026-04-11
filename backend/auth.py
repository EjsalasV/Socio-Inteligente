from __future__ import annotations

import os
import secrets
import sys
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.repositories.identity_repository import store as identity_store
from backend.schemas import UserContext


_SECRET = (os.getenv("JWT_SECRET_KEY") or os.getenv("SOCIO_JWT_SECRET") or "").strip()
if not _SECRET:
    if os.getenv("CI") or os.getenv("EXPORT_OPENAPI"):
        # En CI/export de OpenAPI usamos secreto efimero por proceso, nunca hardcodeado.
        _SECRET = secrets.token_urlsafe(48)
    else:
        raise RuntimeError(
            "JWT_SECRET_KEY no esta configurado. Define la variable de entorno antes de iniciar el backend."
        )

# Log para diagnosticar cual clave se está usando
_key_preview = _SECRET[:20] + "..." + _SECRET[-10:] if len(_SECRET) > 30 else _SECRET[:20] + "..."
print(f"[JWT] JWT_SECRET_KEY loaded: {_key_preview} (len={len(_SECRET)})", file=sys.stderr)
logging.getLogger().warning(f"[JWT] JWT_SECRET_KEY loaded: {_key_preview} (len={len(_SECRET)})")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES")
    or os.getenv("SOCIO_JWT_EXPIRES_MINUTES")
    or "60"
)

bearer_scheme = HTTPBearer(auto_error=False)

AUTH_COOKIE_NAME = (os.getenv("AUTH_COOKIE_NAME") or "socio-auth").strip() or "socio-auth"
AUTH_COOKIE_SAMESITE = (
    os.getenv("AUTH_COOKIE_SAMESITE")
    or ("none" if os.getenv("ENV", "development").lower() == "production" else "lax")
).strip().lower()
AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "").strip().lower() in {"1", "true", "yes"}
if not AUTH_COOKIE_SECURE:
    AUTH_COOKIE_SECURE = os.getenv("ENV", "development").lower() == "production"
CSRF_HEADER_NAME = "X-CSRF-Token"


def _allowed_clientes_from_env() -> list[str] | None:
    raw = os.getenv("ALLOWED_CLIENTES", "").strip()
    if not raw or raw == "*":
        return None
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return values or None


def create_access_token(
    *,
    sub: str,
    org_id: str,
    allowed_clientes: list[str],
    role: str,
    user_id: str = "",
    display_name: str = "",
    csrf_token: str = "",
    expires_minutes: int | None = None,
) -> tuple[str, int]:
    minutes = expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    csrf_value = csrf_token.strip() if csrf_token else secrets.token_urlsafe(24)
    payload = {
        "sub": sub,
        "org_id": org_id,
        "allowed_clientes": allowed_clientes,
        "role": role,
        "exp": exp,
        "csrf": csrf_value,
    }
    if user_id:
        payload["uid"] = user_id
    if display_name:
        payload["display_name"] = display_name
    token = jwt.encode(payload, _SECRET, algorithm=ALGORITHM)
    return token, minutes * 60


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _SECRET, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
        ) from exc


def user_context_from_payload(payload: dict[str, Any]) -> UserContext:
    allowed_clientes = payload.get("allowed_clientes")
    if not isinstance(allowed_clientes, list):
        allowed_clientes = _allowed_clientes_from_env() or ["*"]

    sub = str(payload.get("sub") or "").strip()
    live_user = identity_store.get_user_by_username(sub) if sub else None
    live_uid = str(payload.get("uid") or "").strip()
    live_role = str(payload.get("role") or "auditor").strip()
    live_display_name = str(payload.get("display_name") or sub).strip()

    # Dynamic authorization: if identity repository has user/assignments, prefer live values.
    if isinstance(live_user, dict):
        if not bool(live_user.get("active", True)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario desactivado",
            )
        live_uid = str(live_user.get("user_id") or live_uid or "").strip()
        live_role = str(live_user.get("role") or live_role or "auditor").strip()
        live_display_name = str(live_user.get("display_name") or live_display_name or sub).strip()
        dynamic_allowed = identity_store.get_user_clientes(live_uid) if live_uid else []
        # For real users in identity store, assignments are the source of truth (even if empty).
        allowed_clientes = dynamic_allowed

    try:
        return UserContext(
            sub=sub,
            org_id=str(payload.get("org_id") or "socio-default-org"),
            allowed_clientes=[str(c) for c in allowed_clientes],
            role=live_role,
            user_id=live_uid,
            display_name=live_display_name,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Payload de token invalido",
        ) from exc


def get_user_from_token(token: str) -> UserContext:
    payload = decode_token(token)
    return user_context_from_payload(payload)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserContext:
    token = ""
    if credentials is not None and credentials.scheme.lower() == "bearer":
        token = str(credentials.credentials or "").strip()
    if not token:
        token = str(request.cookies.get(AUTH_COOKIE_NAME) or "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta token bearer o cookie de sesion",
        )
    return get_user_from_token(token)


def authorize_cliente_access(cliente_id: str, user: UserContext | None = None) -> None:
    allowed_env = _allowed_clientes_from_env()

    if user is not None:
        allowed = set(user.allowed_clientes)
        if "*" in allowed:
            return
        if cliente_id in allowed:
            return
        # Identity users use strict assignment checks (no env wildcard fallback).
        if user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado al cliente: {cliente_id}",
            )
        # Legacy tokens keep previous environment fallback behavior.
        if allowed_env is None:
            return
        if cliente_id in set(allowed_env):
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Acceso denegado al cliente: {cliente_id}",
        )

    if allowed_env is None:
        return
    if cliente_id not in set(allowed_env):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Acceso denegado al cliente: {cliente_id}",
        )
