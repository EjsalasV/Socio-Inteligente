from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, status

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import append_audit_log, append_briefing_time_log, append_hallazgo, append_traceability_event
from backend.repositories.metrics_repository import record_metric_event
from backend.schemas import (
    ApiResponse,
    BriefingTiempoLogRequest,
    BriefingTiempoLogResponse,
    HallazgoEstructurarRequest,
    HallazgoEstructurarResponse,
    TraceabilityItem,
    UserContext,
)
from backend.services.hallazgo_service import generate_hallazgo_estructurado
from backend.utils.api_errors import raise_api_error

router = APIRouter(prefix="/api/hallazgos", tags=["hallazgos"])
LOGGER = logging.getLogger("socio_ai.hallazgos")


@router.post("/estructurar", response_model=ApiResponse)
def post_estructurar_hallazgo(
    payload: HallazgoEstructurarRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(payload.cliente_id, user)
    started = time.perf_counter()
    try:
        result = generate_hallazgo_estructurado(payload.model_dump())
    except RuntimeError as exc:
        record_metric_event(
            "llm_error",
            cliente_id=payload.cliente_id,
            area_codigo=payload.area_codigo,
            payload={"endpoint": "/api/hallazgos/estructurar", "error": str(exc)},
        )
        raise_api_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="LLM_NOT_AVAILABLE",
            message=str(exc),
            action_hint="Verifica DEEPSEEK_API_KEY y reintenta estructurar el hallazgo.",
            retryable=True,
        )
    except Exception as exc:
        record_metric_event(
            "rag_error",
            cliente_id=payload.cliente_id,
            area_codigo=payload.area_codigo,
            payload={"endpoint": "/api/hallazgos/estructurar", "error": str(exc)},
        )
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="HALLAZGO_GENERATION_FAILED",
            message="No se pudo estructurar el hallazgo.",
            action_hint="Reintenta o registra el hallazgo manualmente.",
            retryable=True,
        )

    response = HallazgoEstructurarResponse(
        area_codigo=str(result.get("area_codigo") or payload.area_codigo),
        area_nombre=str(result.get("area_nombre") or payload.area_nombre),
        hallazgo=str(result.get("hallazgo") or ""),
        normas_activadas=[str(x) for x in (result.get("normas_activadas") or [])],
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

    if payload.guardar_en_hallazgos and response.hallazgo.strip():
        append_hallazgo(
            payload.cliente_id,
            f"## Hallazgo {payload.area_codigo} - {payload.area_nombre}\n\n{response.hallazgo.strip()}",
        )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    has_staleness_warning = "verificar vigencia" in response.hallazgo.lower()
    record_metric_event(
        "hallazgo_generated",
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
        "hallazgo.estructurado cliente_id=%s area=%s normas=%s elapsed_ms=%s",
        payload.cliente_id,
        payload.area_codigo,
        ",".join(response.normas_activadas),
        elapsed_ms,
    )
    for tr in response.trazabilidad:
        append_traceability_event(
            payload.cliente_id,
            {
                "kind": "hallazgo",
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
        endpoint="POST /api/hallazgos/estructurar",
        extra={
            "area_codigo": payload.area_codigo,
            "area_nombre": payload.area_nombre,
            "normas_activadas": response.normas_activadas,
            "elapsed_ms": elapsed_ms,
            "guardado": bool(payload.guardar_en_hallazgos),
        },
    )

    return ApiResponse(data=response.model_dump())


@router.post("/tiempo-briefing", response_model=ApiResponse)
def post_tiempo_briefing(
    payload: BriefingTiempoLogRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(payload.cliente_id, user)
    saved = append_briefing_time_log(
        cliente_id=payload.cliente_id,
        area_codigo=payload.area_codigo,
        area_nombre=payload.area_nombre,
        tiempo_manual_min=payload.tiempo_manual_min,
        tiempo_ai_min=payload.tiempo_ai_min,
        notas=payload.notas,
        user_id=user.sub,
    )

    append_audit_log(
        user_id=user.sub,
        cliente_id=payload.cliente_id,
        endpoint="POST /api/hallazgos/tiempo-briefing",
        extra={
            "area_codigo": payload.area_codigo,
            "tiempo_manual_min": payload.tiempo_manual_min,
            "tiempo_ai_min": payload.tiempo_ai_min,
            "delta_min": saved.get("delta_min"),
            "ahorro_pct": saved.get("ahorro_pct"),
        },
    )
    record_metric_event(
        "briefing_time_logged",
        cliente_id=payload.cliente_id,
        area_codigo=payload.area_codigo,
        payload={
            "tiempo_manual_min": payload.tiempo_manual_min,
            "tiempo_ai_min": payload.tiempo_ai_min,
            "delta_min": saved.get("delta_min"),
            "ahorro_pct": saved.get("ahorro_pct"),
        },
    )

    return ApiResponse(data=BriefingTiempoLogResponse(**saved).model_dump())
