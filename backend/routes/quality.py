from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi import status

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import append_audit_log
from backend.repositories.metrics_repository import record_metric_event
from backend.schemas import ApiResponse, UserContext
from backend.services.quality_service import build_quality_metrics, evaluate_pre_emit_check
from backend.utils.api_errors import raise_api_error

router = APIRouter(prefix="/api/quality", tags=["quality"])


@router.post("/pre-emit-check", response_model=ApiResponse)
def post_pre_emit_check(
    payload: dict,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    cliente_id = str(payload.get("cliente_id") or "").strip()
    if not cliente_id:
        raise_api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="MISSING_CLIENTE_ID",
            message="cliente_id es obligatorio para pre-emit-check.",
            action_hint="Envia el identificador del cliente activo.",
            retryable=False,
        )
    authorize_cliente_access(cliente_id, user)

    try:
        result = evaluate_pre_emit_check(
            cliente_id,
            fase=str(payload.get("fase") or "informe"),
            area_codigo=str(payload.get("area_codigo") or "").strip() or None,
            document_type=str(payload.get("document_type") or "").strip() or None,
        )
    except Exception:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="QUALITY_CHECK_FAILED",
            message="No se pudo ejecutar el revisor de calidad.",
            action_hint="Reintenta y, si persiste, revisa la estructura YAML del cliente.",
            retryable=True,
        )

    record_metric_event(
        "quality_pre_emit",
        cliente_id=cliente_id,
        area_codigo=str(payload.get("area_codigo") or ""),
        payload={
            "status": result.get("status"),
            "blocking_reasons": result.get("blocking_reasons") or [],
            "warnings": result.get("warnings") or [],
            "score_calidad": result.get("score_calidad"),
        },
    )

    append_audit_log(
        user_id=user.sub,
        cliente_id=cliente_id,
        endpoint="POST /api/quality/pre-emit-check",
        extra={
            "status": result.get("status"),
            "score_calidad": result.get("score_calidad"),
            "blocking_count": len(result.get("blocking_reasons") or []),
        },
    )
    return ApiResponse(data=result)


@router.get("/metrics", response_model=ApiResponse)
def get_quality_metrics(
    cliente_id: str | None = None,
    area_codigo: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    cid = str(cliente_id or "").strip()
    if cid:
        authorize_cliente_access(cid, user)
    try:
        data = build_quality_metrics(
            cliente_id=cid or None,
            area_codigo=str(area_codigo or "").strip() or None,
            date_from=date_from,
            date_to=date_to,
        )
    except Exception:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="QUALITY_METRICS_FAILED",
            message="No se pudieron calcular las metricas de calidad.",
            action_hint="Reintenta y valida que existan eventos en data/metrics/events.jsonl.",
            retryable=True,
        )
    return ApiResponse(data=data)
