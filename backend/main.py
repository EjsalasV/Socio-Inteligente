from __future__ import annotations

import logging
import os
import time
from typing import Awaitable, Callable
from uuid import uuid4

# [IMPORTANT] Load .env FIRST, before any other imports
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(title="Socio AI Backend", version="0.1.0")
LOGGER = logging.getLogger("socio_ai.api")
if not LOGGER.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ============= DATABASE INITIALIZATION =============
@app.on_event("startup")
async def startup_event():
    """Inicializar base de datos al startup"""
    try:
        from backend.utils.database import init_db
        init_db()
        LOGGER.info("[OK] Database initialized at startup")
    except Exception as e:
        LOGGER.error(f"[ERROR] Failed to initialize database: {e}")

_csrf_enforcer: Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]] | None = None
_observed_prefixes: tuple[str, ...] | None = None
_csrf_header_name: str | None = None
_rate_limit_module = None
_observability_module = None
_routes_registered = False


def _get_csrf_header_name() -> str:
    global _csrf_header_name
    if _csrf_header_name is None:
        from backend.auth import CSRF_HEADER_NAME

        _csrf_header_name = CSRF_HEADER_NAME
    return _csrf_header_name


def _get_rate_limit_module():
    global _rate_limit_module
    if _rate_limit_module is None:
        from backend.middleware import rate_limit as rate_limit_module

        _rate_limit_module = rate_limit_module
    return _rate_limit_module


def _get_observability_module():
    global _observability_module
    if _observability_module is None:
        from backend.services import observability_service as observability_module

        _observability_module = observability_module
    return _observability_module


def _get_request_id(request: Request) -> str:
    state_id = str(getattr(request.state, "request_id", "") or "").strip()
    if state_id:
        return state_id
    header_id = str(request.headers.get("X-Request-ID") or "").strip()
    if header_id:
        return header_id[:128]
    return str(uuid4())


def _register_routes_once() -> None:
    global _routes_registered
    if _routes_registered:
        return
    from backend.routes import (
        alertas,
        area_catalog,
        admin,
        areas,
        audit_validator,
        auth,
        briefing,
        chat,
        clientes,
        dashboard,
        expert_criteria,
        export,
        hallazgos,
        historicos,
        holdings_cascade_route,
        metodologia,
        normativa,
        # papeles_trabajo_v2,  # TODO: Enable in FASE 0 when dependencies are complete
        papeles_trabajo_plantilla,
        perfil,
        quality,
        realtime,
        reportes,
        reportes_papeles,
        risk_engine,
        search,
        trial_balance,
        mayor,
        user_preferences,
        workpapers,
        workflow,
        audit_programs_dashboard,
    )

    app.include_router(auth.router)
    app.include_router(clientes.router)
    app.include_router(perfil.router)
    app.include_router(dashboard.router)
    app.include_router(risk_engine.router)
    app.include_router(areas.router)
    app.include_router(chat.router)
    app.include_router(metodologia.router)
    app.include_router(reportes.router)
    app.include_router(reportes_papeles.router)
    app.include_router(papeles_trabajo_plantilla.router)
    app.include_router(workpapers.router)
    # app.include_router(papeles_trabajo_v2.router)  # TODO: Enable in FASE 0 when dependencies are complete
    app.include_router(workflow.router)
    app.include_router(briefing.router)
    app.include_router(hallazgos.router)
    app.include_router(quality.router)
    app.include_router(normativa.router)
    app.include_router(user_preferences.router)
    app.include_router(admin.router)
    app.include_router(realtime.router)
    app.include_router(audit_validator.router)
    app.include_router(audit_programs_dashboard.router)
    app.include_router(holdings_cascade_route.router)
    app.include_router(area_catalog.router)
    app.include_router(expert_criteria.router)
    app.include_router(historicos.router)
    app.include_router(alertas.router)
    app.include_router(search.router)
    app.include_router(trial_balance.router)
    app.include_router(mayor.router)
    app.include_router(export.router)
    _routes_registered = True


def _get_csrf_enforcer() -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    global _csrf_enforcer
    if _csrf_enforcer is None:
        from backend.middleware.csrf import enforce_csrf

        _csrf_enforcer = enforce_csrf
    return _csrf_enforcer


def _get_observed_prefixes() -> tuple[str, ...]:
    global _observed_prefixes
    if _observed_prefixes is None:
        _observed_prefixes = (
            "/auth/",
            "/clientes",
            "/perfil/",
            "/dashboard/",
            "/risk-engine/",
            "/chat/",
            "/papeles-trabajo/",
            "/workflow/",
            "/reportes/",
            "/api/briefing/",
            "/api/hallazgos/",
            "/api/quality/",
            "/api/normativa/",
            "/api/user/",
            "/api/admin/",
            "/api/audit/",
            "/api/audit-programs/",
        )
    return _observed_prefixes


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    observability = _get_observability_module().store
    request_id = _get_request_id(request)
    rate_limit_module = _get_rate_limit_module()
    scope = rate_limit_module.infer_scope_from_path(request.url.path) or "unknown"
    rate_limit_module.record_rate_limit_metric(scope, "blocked")
    observability.record_error(
        code="RATE_LIMIT_EXCEEDED",
        method=request.method,
        path=request.url.path,
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        request_id=request_id,
        message="Too many requests",
    )
    observability.log(
        LOGGER,
        logging.WARNING,
        "api.rate_limit_exceeded",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        scope=scope,
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": "60"},
        content={
            "status": "error",
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "Demasiadas solicitudes. Por favor intenta mas tarde.",
            "action_hint": "Reduce la frecuencia de solicitudes y vuelve a intentar.",
            "retryable": True,
            "details": {},
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    observability = _get_observability_module().store
    request_id = _get_request_id(request)
    detail = exc.detail
    code = f"HTTP_{exc.status_code}"
    message = "Solicitud invalida."
    action_hint = ""
    retryable = exc.status_code >= 500
    details: dict = {}

    if isinstance(detail, dict):
        code = str(detail.get("code") or code)
        message = str(detail.get("message") or message)
        action_hint = str(detail.get("action_hint") or "")
        retryable = bool(detail.get("retryable", retryable))
        raw_details = detail.get("details")
        if isinstance(raw_details, dict):
            details = raw_details
        elif raw_details is not None:
            details = {"raw": raw_details}
    elif isinstance(detail, str) and detail.strip():
        message = detail.strip()
    elif detail is not None:
        details = {"raw": detail}

    observability.record_error(
        code=code,
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
        request_id=request_id,
        message=message,
    )
    observability.log(
        LOGGER,
        logging.WARNING if exc.status_code < 500 else logging.ERROR,
        "api.http_exception",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
        code=code,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": code,
            "message": message,
            "action_hint": action_hint,
            "retryable": retryable,
            "details": details,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    observability = _get_observability_module().store
    request_id = _get_request_id(request)
    code = f"HTTP_{exc.status_code}"
    observability.record_error(
        code=code,
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
        request_id=request_id,
        message=str(exc.detail or ""),
    )
    observability.log(
        LOGGER,
        logging.WARNING if exc.status_code < 500 else logging.ERROR,
        "api.starlette_http_exception",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
        code=code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": code,
            "message": str(exc.detail or "Solicitud invalida."),
            "action_hint": "",
            "retryable": exc.status_code >= 500,
            "details": {},
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    observability = _get_observability_module().store
    request_id = _get_request_id(request)
    safe_errors = jsonable_encoder(exc.errors())
    observability.record_error(
        code="VALIDATION_ERROR",
        method=request.method,
        path=request.url.path,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        request_id=request_id,
        message="Validation error",
    )
    observability.log(
        LOGGER,
        logging.WARNING,
        "api.validation_error",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        errors_count=len(safe_errors) if isinstance(safe_errors, list) else 0,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "status": "error",
            "code": "VALIDATION_ERROR",
            "message": "La solicitud contiene datos invalidos.",
            "action_hint": "Revisa los campos obligatorios y su formato.",
            "retryable": False,
            "details": {"errors": safe_errors},
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    observability = _get_observability_module().store
    request_id = _get_request_id(request)
    observability.record_error(
        code="INTERNAL_SERVER_ERROR",
        method=request.method,
        path=request.url.path,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
        message=str(exc),
    )
    observability.log(
        LOGGER,
        logging.ERROR,
        "api.unhandled_exception",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        error=str(exc),
    )
    LOGGER.exception("api.unhandled_exception.trace request_id=%s", request_id)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Error interno del servidor.",
            "action_hint": "Reintenta en unos segundos. Si persiste, contacta soporte.",
            "retryable": True,
            "details": {},
        },
    )


_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")


def _normalize_origin(origin: str) -> str:
    return origin.strip().rstrip("/")


_origins: list[str] = []
for _origin in _origins_raw.split(","):
    cleaned = _normalize_origin(_origin)
    if cleaned and cleaned not in _origins:
        _origins.append(cleaned)
_is_prod = os.getenv("ENV", "development").lower() == "production"


def _configure_runtime_integrations() -> None:
    from fastapi.middleware.cors import CORSMiddleware

    rate_limit_module = _get_rate_limit_module()
    app.state.limiter = rate_limit_module.limiter
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type", _get_csrf_header_name()],
        expose_headers=[] if _is_prod else ["X-Request-ID"],
    )
    _register_routes_once()


_configure_runtime_integrations()


@app.get("/health")
def health() -> dict[str, str]:
    rate_limit_module = _get_rate_limit_module()
    return {"status": "ok", "rate_limit_backend": rate_limit_module.rate_limit_backend_name()}


@app.middleware("http")
async def csrf_protection(request: Request, call_next) -> Response:
    return await _get_csrf_enforcer()(request, call_next)


@app.middleware("http")
async def request_observability(request: Request, call_next) -> Response:
    start = time.perf_counter()
    observability = _get_observability_module().store
    inbound_request_id = str(request.headers.get("X-Request-ID") or "").strip()
    request_id = inbound_request_id[:128] if inbound_request_id else str(uuid4())
    request.state.request_id = request_id
    response: Response
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = int((time.perf_counter() - start) * 1000)
        observability.log(
            LOGGER,
            logging.ERROR,
            "api.request_failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            duration_ms=duration_ms,
        )
        LOGGER.exception("api.request_failed.trace request_id=%s", request_id)
        raise

    duration_ms = int((time.perf_counter() - start) * 1000)
    path = request.url.path
    observability.record_request(
        method=request.method,
        path=path,
        status_code=response.status_code,
        duration_ms=float(duration_ms),
        request_id=request_id,
    )
    if any(path.startswith(prefix) for prefix in _get_observed_prefixes()):
        observability.log(
            LOGGER,
            logging.INFO,
            "api.request",
            request_id=request_id,
            method=request.method,
            path=path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
    rate_limit_module = _get_rate_limit_module()
    scope = rate_limit_module.infer_scope_from_path(path)
    if scope:
        outcome = "blocked" if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS else "allowed"
        rate_limit_module.record_rate_limit_metric(scope, outcome)
    response.headers["X-Request-ID"] = request_id
    return response
