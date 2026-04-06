from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import append_audit_log
from backend.schemas import ApiResponse, BriefingAreaRequest, BriefingAreaResponse, UserContext
from backend.services.briefing_service import generate_area_briefing

router = APIRouter(prefix="/api/briefing", tags=["briefing"])
LOGGER = logging.getLogger("socio_ai.briefing")


@router.post("/area", response_model=ApiResponse)
def post_briefing_area(payload: BriefingAreaRequest, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(payload.cliente_id, user)
    started = time.perf_counter()
    try:
        result = generate_area_briefing(payload.model_dump())
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

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
        generado_en=str(result.get("generado_en") or ""),
    )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    LOGGER.info(
        "briefing.generated cliente_id=%s area=%s normas=%s elapsed_ms=%s",
        payload.cliente_id,
        payload.area_codigo,
        ",".join(response.normas_activadas),
        elapsed_ms,
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
