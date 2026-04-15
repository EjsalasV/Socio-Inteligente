from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi import status

from backend.auth import get_current_user
from backend.constants.runtime_config import get_runtime_config
from backend.repositories.file_repository import append_audit_log
from backend.schemas import ApiResponse, UserContext
from backend.services.normativa_monitor_service import run_monthly_normative_refresh
from backend.services.normative_catalog_service import list_normative_catalog
from backend.services.rag_cache_service import invalidate_rag_cache_all
from backend.services.rate_limit_service import RateLimitExceeded, rate_limiter
from backend.utils.api_errors import raise_api_error

router = APIRouter(prefix="/api/normativa", tags=["normativa"])
RUNTIME_CFG = get_runtime_config()


def _refresh_limit_per_minute() -> int:
    cfg = RUNTIME_CFG.get("rate_limit", {}) if isinstance(RUNTIME_CFG, dict) else {}
    raw = cfg.get("normativa_refresh_per_minute", 3) if isinstance(cfg, dict) else 3
    try:
        value = int(raw)
    except Exception:
        value = 3
    return max(1, min(value, 60))


@router.get("/catalogo", response_model=ApiResponse)
def get_normative_catalog(user: UserContext = Depends(get_current_user)) -> ApiResponse:
    rows = list_normative_catalog()
    append_audit_log(
        user_id=user.sub,
        cliente_id="*",
        endpoint="GET /api/normativa/catalogo",
        extra={"total": len(rows)},
    )
    return ApiResponse(data={"normas": rows, "total": len(rows)})


@router.post("/refresh-monthly", response_model=ApiResponse)
def post_refresh_monthly(user: UserContext = Depends(get_current_user)) -> ApiResponse:
    subject = str(user.user_id or user.sub or "anonymous").strip().lower()
    try:
        rate_limiter.enforce(
            scope="normativa:refresh-monthly",
            subject=subject,
            limit=_refresh_limit_per_minute(),
            window_seconds=60,
        )
    except RateLimitExceeded as exc:
        raise_api_error(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="NORMATIVA_RATE_LIMIT_EXCEEDED",
            message=(
                "Demasiadas solicitudes de refresco normativo. "
                f"Limite: {exc.limit} por {exc.window_seconds}s."
            ),
            action_hint=f"Espera {exc.retry_after_seconds}s antes de reintentar.",
            retryable=True,
            details={"retry_after_seconds": exc.retry_after_seconds},
        )

    try:
        result = run_monthly_normative_refresh()
    except Exception:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="NORMATIVA_REFRESH_FAILED",
            message="Fallo la actualizacion mensual de vigencia normativa.",
            action_hint="Verifica conectividad a fuentes SRI/Supercias y reintenta.",
            retryable=True,
        )
    cache_invalidated = invalidate_rag_cache_all()
    if isinstance(result, dict):
        result["rag_cache_invalidated"] = int(cache_invalidated)
    append_audit_log(
        user_id=user.sub,
        cliente_id="*",
        endpoint="POST /api/normativa/refresh-monthly",
        extra=result,
    )
    return ApiResponse(data=result)
