from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.repositories.identity_repository import store as identity_store
from backend.schemas import UserContext


_SECRET = (os.getenv("JWT_SECRET_KEY") or os.getenv("SOCIO_JWT_SECRET") or "").strip()
if not _SECRET:
    if os.getenv("CI") or os.getenv("EXPORT_OPENAPI"):
        _SECRET = "DUMMY_SECRET_FOR_CI"
    else:
        raise RuntimeError(
            "JWT_SECRET_KEY no esta configurado. Define la variable de entorno antes de iniciar el backend."
        )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES")
    or os.getenv("SOCIO_JWT_EXPIRES_MINUTES")
    or "60"
)

bearer_scheme = HTTPBearer(auto_error=False)


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
    expires_minutes: int | None = None,
) -> tuple[str, int]:
    minutes = expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {
        "sub": sub,
        "org_id": org_id,
        "allowed_clientes": allowed_clientes,
        "role": role,
        "exp": exp,
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


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta token bearer",
        )

    payload = decode_token(credentials.credentials)
    allowed_clientes = payload.get("allowed_clientes")
    if not isinstance(allowed_clientes, list):
        allowed_clientes = _allowed_clientes_from_env() or ["*"]

    sub = str(payload.get("sub") or "").strip()
    live_user = identity_store.get_user_by_username(sub) if sub else None

    # Dynamic authorization: if identity repository has user/assignments, prefer live values.
    if isinstance(live_user, dict):
        if not bool(live_user.get("active", True)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario desactivado",
            )
        live_uid = str(live_user.get("user_id") or payload.get("uid") or "").strip()
        live_role = str(live_user.get("role") or payload.get("role") or "auditor").strip()
        live_display_name = str(live_user.get("display_name") or payload.get("display_name") or sub).strip()
        dynamic_allowed = identity_store.get_user_clientes(live_uid) if live_uid else []
        # For real users in identity store, assignments are the source of truth (even if empty).
        allowed_clientes = dynamic_allowed

    try:
        return UserContext(
            sub=sub,
            org_id=str(payload.get("org_id") or "socio-default-org"),
            allowed_clientes=[str(c) for c in allowed_clientes],
            role=live_role if isinstance(live_user, dict) else str(payload.get("role") or "auditor"),
            user_id=live_uid if isinstance(live_user, dict) else str(payload.get("uid") or ""),
            display_name=live_display_name if isinstance(live_user, dict) else str(payload.get("display_name") or ""),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Payload de token invalido",
        ) from exc


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
