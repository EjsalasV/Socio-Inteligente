from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from backend.auth import authorize_cliente_access, get_current_user
from backend.schemas import ApiResponse, UserContext
from backend.services.entity_profile_service import (
    build_profile_draft,
    confirm_profile_draft,
    update_pending_item,
    update_profile_answers,
)
from backend.services.entity_profile_analysis_service import analyze_entity_profile, update_analysis_decision
from backend.utils.api_errors import raise_api_error


router = APIRouter(prefix="/api/entity-profile", tags=["entity-profile"])


class ProfileAnswersRequest(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)


class ProfileAnalysisRequest(BaseModel):
    force: bool = False


class PendingItemRequest(BaseModel):
    status: str = Field(min_length=3, max_length=30)
    answer: str = Field(default="", max_length=4000)


class ProfileDecisionRequest(BaseModel):
    hypothesis_id: str = Field(min_length=3, max_length=160)
    status: str
    edited_title: str = Field(default="", max_length=300)
    edited_reason: str = Field(default="", max_length=2000)


@router.get("/{cliente_id}/draft", response_model=ApiResponse)
def get_profile_draft(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    return ApiResponse(data=build_profile_draft(cliente_id))


@router.put("/{cliente_id}/answers", response_model=ApiResponse)
def put_profile_answers(
    cliente_id: str,
    payload: ProfileAnswersRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    return ApiResponse(data=update_profile_answers(cliente_id, payload.answers))


@router.post("/{cliente_id}/confirm", response_model=ApiResponse)
def post_confirm_profile(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    try:
        draft = confirm_profile_draft(cliente_id, user.sub)
    except ValueError as exc:
        raise_api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="PROFILE_CONFIRMATION_INCOMPLETE",
            message=str(exc),
        )
    return ApiResponse(data=draft)


@router.put("/{cliente_id}/pending/{question_id}", response_model=ApiResponse)
def put_pending_item(
    cliente_id: str,
    question_id: str,
    payload: PendingItemRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    try:
        draft = update_pending_item(
            cliente_id,
            question_id,
            status=payload.status,
            answer=payload.answer,
        )
    except ValueError as exc:
        raise_api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INVALID_PENDING_ITEM",
            message=str(exc),
        )
    return ApiResponse(data=draft)


@router.post("/{cliente_id}/analyze", response_model=ApiResponse)
def post_analyze_profile(
    cliente_id: str,
    payload: ProfileAnalysisRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    try:
        analysis = analyze_entity_profile(cliente_id, force=payload.force)
    except PermissionError as exc:
        raise_api_error(status_code=status.HTTP_403_FORBIDDEN, code="AI_CLIENT_DATA_DISABLED", message=str(exc))
    except ValueError as exc:
        raise_api_error(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="PROFILE_NOT_READY", message=str(exc))
    except RuntimeError as exc:
        raise_api_error(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, code="PROFILE_ANALYSIS_UNAVAILABLE", message=str(exc))
    return ApiResponse(data=analysis)


@router.put("/{cliente_id}/analysis/decision", response_model=ApiResponse)
def put_analysis_decision(
    cliente_id: str,
    payload: ProfileDecisionRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    try:
        analysis = update_analysis_decision(
            cliente_id,
            hypothesis_id=payload.hypothesis_id,
            decision_status=payload.status,
            decided_by=user.sub,
            edited_title=payload.edited_title,
            edited_reason=payload.edited_reason,
        )
    except ValueError as exc:
        raise_api_error(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="INVALID_PROFILE_DECISION", message=str(exc))
    return ApiResponse(data=analysis)
