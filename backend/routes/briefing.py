from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, status

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import append_audit_log, append_traceability_event
from backend.repositories.metrics_repository import record_metric_event
from backend.schemas import ApiResponse, BriefingAreaRequest, BriefingAreaResponse, TraceabilityItem, UserContext
from backend.services.briefing_service import generate_area_briefing
from backend.utils.api_errors import raise_api_error

router = APIRouter(prefix="/api/briefing", tags=["briefing"])
LOGGER = logging.getLogger("socio_ai.briefing")


@router.post("/area", response_model=ApiResponse)
def post_briefing_area(payload: BriefingAreaRequest, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(payload.cliente_id, user)
    started = time.perf_counter()
    try:
        result = generate_area_briefing(payload.model_dump())
    except RuntimeError as exc:
        record_metric_event(
            "llm_error",
            cliente_id=payload.cliente_id,
            area_codigo=payload.area_codigo,
            payload={"endpoint": "/api/briefing/area", "error": str(exc)},
        )
        raise_api_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="LLM_NOT_AVAILABLE",
            message=str(exc),
            action_hint="Verifica DEEPSEEK_API_KEY y reintenta generar briefing.",
            retryable=True,
        )
    except Exception as exc:
        record_metric_event(
            "rag_error",
            cliente_id=payload.cliente_id,
            area_codigo=payload.area_codigo,
            payload={"endpoint": "/api/briefing/area", "error": str(exc)},
        )
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="BRIEFING_GENERATION_FAILED",
            message="No se pudo generar el briefing del area.",
            action_hint="Reintenta en unos segundos o continua sin normativa especifica.",
            retryable=True,
        )

    response = BriefingAreaResponse(
        area_codigo=str(result.get("area_codigo") or payload.area_codigo),
        area_nombre=str(result.get("area_nombre") or payload.area_nombre),
        briefing=str(result.get("briefing") or ""),
        normas_activadas=[str(n) for n in result.get("normas_activadas") or []],
        chunks_usados=[
            {
                "norma": str(ch.get("norma") or ""),
                "fuente": str(ch.get("fuente") or ""),
                "excerpt": str(ch.get("excerpt") or ""),
            }
            for ch in (result.get("chunks_usados") or [])
            if isinstance(ch, dict)
        ],
        trazabilidad=[
            TraceabilityItem(
                norma=str(tr.get("norma") or ""),
                fuente_chunk=str(tr.get("fuente_chunk") or ""),
                chunk_id=str(tr.get("chunk_id") or ""),
                area_codigo=str(tr.get("area_codigo") or payload.area_codigo),
                paper_id=str(tr.get("paper_id") or "") or None,
                timestamp=str(tr.get("timestamp") or ""),
            )
            for tr in (result.get("trazabilidad") or [])
            if isinstance(tr, dict)
        ],
        generado_en=str(result.get("generado_en") or ""),
    )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    has_staleness_warning = "verificar vigencia" in response.briefing.lower()
    record_metric_event(
        "briefing_generated",
        cliente_id=payload.cliente_id,
        area_codigo=payload.area_codigo,
        payload={
            "chunks_count": len(response.chunks_usados),
            "normas_count": len(response.normas_activadas),
            "staleness_warning": has_staleness_warning,
            "elapsed_ms": elapsed_ms,
        },
    )
    LOGGER.info(
        "briefing.generated cliente_id=%s area=%s normas=%s elapsed_ms=%s",
        payload.cliente_id,
        payload.area_codigo,
        ",".join(response.normas_activadas),
        elapsed_ms,
    )
    for tr in response.trazabilidad:
        append_traceability_event(
            payload.cliente_id,
            {
                "kind": "briefing",
                "area_codigo": payload.area_codigo,
                "area_nombre": payload.area_nombre,
                "norma": tr.norma,
                "fuente_chunk": tr.fuente_chunk,
                "chunk_id": tr.chunk_id,
                "paper_id": tr.paper_id or "",
                "timestamp_ref": tr.timestamp,
                "user_id": user.sub,
            },
        )
    append_audit_log(
        user_id=user.sub,
        cliente_id=payload.cliente_id,
        endpoint="POST /api/briefing/area",
        extra={
            "area_codigo": payload.area_codigo,
            "area_nombre": payload.area_nombre,
            "normas_activadas": response.normas_activadas,
            "elapsed_ms": elapsed_ms,
        },
    )
    return ApiResponse(data=response.model_dump())
