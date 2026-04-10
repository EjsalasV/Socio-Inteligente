from __future__ import annotations

import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from backend.auth import AUTH_COOKIE_NAME, CSRF_HEADER_NAME, decode_token
from backend.schemas import ApiResponse

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
EXEMPT_PATHS = {"/health", "/auth/login", "/auth/logout"}


async def enforce_csrf(request: Request, call_next):
    method = request.method.upper()
    if method in SAFE_METHODS or request.url.path in EXEMPT_PATHS:
        return await call_next(request)

    session_token = str(request.cookies.get(AUTH_COOKIE_NAME) or "").strip()
    if not session_token:
        # Requests authenticated via Authorization header are not CSRF-prone browser cookies.
        return await call_next(request)

    csrf_header = str(request.headers.get(CSRF_HEADER_NAME) or "").strip()
    if not csrf_header:
        return JSONResponse(
            status_code=403,
            content=ApiResponse(
                status="error",
                data={
                    "code": "CSRF_MISSING",
                    "message": "Falta cabecera X-CSRF-Token.",
                    "action_hint": "Recarga la sesion e intenta nuevamente.",
                },
            ).model_dump(mode="json"),
        )

    try:
        payload = decode_token(session_token)
    except Exception:
        return JSONResponse(
            status_code=401,
            content=ApiResponse(
                status="error",
                data={
                    "code": "SESSION_INVALID",
                    "message": "Sesion invalida o expirada.",
                },
            ).model_dump(mode="json"),
        )

    csrf_claim = str(payload.get("csrf") or "").strip()
    if not csrf_claim or not secrets.compare_digest(csrf_claim, csrf_header):
        return JSONResponse(
            status_code=403,
            content=ApiResponse(
                status="error",
                data={
                    "code": "CSRF_INVALID",
                    "message": "Token CSRF invalido.",
                    "action_hint": "Cierra sesion y vuelve a iniciar.",
                },
            ).model_dump(mode="json"),
        )

    return await call_next(request)
