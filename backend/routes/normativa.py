from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi import status

from backend.auth import get_current_user
from backend.repositories.file_repository import append_audit_log
from backend.schemas import ApiResponse, UserContext
from backend.services.normativa_monitor_service import run_monthly_normative_refresh
from backend.utils.api_errors import raise_api_error

router = APIRouter(prefix="/api/normativa", tags=["normativa"])


@router.post("/refresh-monthly", response_model=ApiResponse)
def post_refresh_monthly(user: UserContext = Depends(get_current_user)) -> ApiResponse:
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
    append_audit_log(
        user_id=user.sub,
        cliente_id="*",
        endpoint="POST /api/normativa/refresh-monthly",
        extra=result,
    )
    return ApiResponse(data=result)
