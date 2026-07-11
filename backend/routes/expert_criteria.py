from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.schemas import ApiResponse, UserContext
from backend.services.expert_criteria_service import (
    get_expert_criteria_by_area,
    get_expert_criteria_by_sector,
    get_quality_review_criteria,
    update_expert_criteria,
)
from backend.services.grupo_criteria_service import get_grupo_criteria, list_grupos

LOGGER = logging.getLogger("socio_ai.expert_criteria")
router = APIRouter(prefix="/api/expert-criteria", tags=["expert-criteria"])


class ExpertCriteriaUpdateRequest(BaseModel):
    content: str


def _ensure_admin(user: UserContext) -> None:
    role = str(user.role or "").strip().lower()
    if role in {"admin", "socio"}:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Solo perfiles admin o socio pueden editar criterio experto.",
    )


@router.get("/area/{area_codigo}", response_model=ApiResponse)
def get_area_criteria(area_codigo: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    payload = get_expert_criteria_by_area(area_codigo)
    LOGGER.info("expert_criteria.area requested_by=%s area=%s found=%s", user.sub, area_codigo, payload.get("found"))
    return ApiResponse(data=payload)


@router.get("/sector/{sector}", response_model=ApiResponse)
def get_sector_criteria(sector: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    payload = get_expert_criteria_by_sector(sector)
    LOGGER.info("expert_criteria.sector requested_by=%s sector=%s found=%s", user.sub, sector, payload.get("found"))
    return ApiResponse(data=payload)


@router.get("/revision/general", response_model=ApiResponse)
def get_quality_criteria(user: UserContext = Depends(get_current_user)) -> ApiResponse:
    payload = get_quality_review_criteria()
    LOGGER.info("expert_criteria.review requested_by=%s found=%s", user.sub, payload.get("found"))
    return ApiResponse(data=payload)


@router.get("/grupos", response_model=ApiResponse)
def get_grupos_mapa(user: UserContext = Depends(get_current_user)) -> ApiResponse:
    grupos = list_grupos()
    LOGGER.info("expert_criteria.grupos requested_by=%s total=%s", user.sub, len(grupos))
    return ApiResponse(data={"grupos": grupos, "total": len(grupos)})


@router.get("/grupo/{grupo}", response_model=ApiResponse)
def get_grupo(grupo: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    payload = get_grupo_criteria(grupo)
    LOGGER.info("expert_criteria.grupo requested_by=%s grupo=%s found=%s", user.sub, grupo, payload.get("found"))
    return ApiResponse(data=payload)


@router.post("/{path:path}", response_model=ApiResponse)
def post_expert_criteria(
    path: str,
    payload: ExpertCriteriaUpdateRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    _ensure_admin(user)
    result = update_expert_criteria(path, payload.content)
    LOGGER.info("expert_criteria.update requested_by=%s path=%s", user.sub, path)
    return ApiResponse(data=result)

