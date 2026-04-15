from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from backend.auth import get_current_user
from backend.schemas import ApiResponse, UserContext
from backend.services.area_procedures_service import get_procedures_by_area, list_areas_with_procedure_count

LOGGER = logging.getLogger("socio_ai.area_catalog")

router = APIRouter(prefix="/api/areas", tags=["areas-catalog"])


@router.get("", response_model=ApiResponse)
def list_areas(user: UserContext = Depends(get_current_user)) -> ApiResponse:
    rows = list_areas_with_procedure_count()
    LOGGER.info("areas.catalog.list requested_by=%s total=%s", user.sub, len(rows))
    return ApiResponse(data={"areas": rows, "total": len(rows)})


@router.get("/{area_codigo}/procedimientos", response_model=ApiResponse)
def get_area_procedures(area_codigo: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    payload = get_procedures_by_area(area_codigo)
    procedures = payload.get("procedimientos")
    count = len(procedures) if isinstance(procedures, list) else 0
    LOGGER.info("areas.catalog.procedures requested_by=%s area=%s found=%s", user.sub, area_codigo, count)
    return ApiResponse(data=payload)

