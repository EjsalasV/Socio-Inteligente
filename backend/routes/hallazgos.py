from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import append_audit_log, append_briefing_time_log, append_hallazgo
from backend.schemas import (
    ApiResponse,
    BriefingTiempoLogRequest,
    BriefingTiempoLogResponse,
    HallazgoEstructurarRequest,
    HallazgoEstructurarResponse,
    UserContext,
)
from backend.services.hallazgo_service import generate_hallazgo_estructurado

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
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

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
        generado_en=str(result.get("generado_en") or ""),
    )

    if payload.guardar_en_hallazgos and response.hallazgo.strip():
        append_hallazgo(
            payload.cliente_id,
            f"## Hallazgo {payload.area_codigo} - {payload.area_nombre}\n\n{response.hallazgo.strip()}",
        )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    LOGGER.info(
        "hallazgo.estructurado cliente_id=%s area=%s normas=%s elapsed_ms=%s",
        payload.cliente_id,
        payload.area_codigo,
        ",".join(response.normas_activadas),
        elapsed_ms,
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

    return ApiResponse(data=BriefingTiempoLogResponse(**saved).model_dump())
