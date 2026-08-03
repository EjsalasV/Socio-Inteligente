from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.identity_repository import store as identity_store
from backend.schemas import ApiResponse, UserContext
from backend.services.mentor_service import generate_account_mentor_guide
from backend.services.mentor_conversation_service import get_mentor_session, reply_to_mentor
from backend.services.learning_progress_service import record_mentor_learning
from backend.utils.api_errors import raise_api_error

router = APIRouter(prefix="/api/mentor", tags=["mentor"])


class AccountMentorRequest(BaseModel):
    area_code: str = Field(max_length=40)
    area_name: str = Field(max_length=200)
    account_code: str = Field(max_length=80)
    account_name: str = Field(max_length=300)
    current_balance: float
    prior_balance: float
    variation_pct: float
    area_assertions: list[dict[str, Any]] = Field(default_factory=list, max_length=12)
    area_accounts: list[dict[str, Any]] = Field(default_factory=list, max_length=250)
    force: bool = False


class MentorReplyRequest(BaseModel):
    session_id: str = Field(default="", max_length=80)
    auditor_response: str = Field(min_length=1, max_length=3000)
    account_context: dict[str, Any] = Field(default_factory=dict)


@router.post("/{cliente_id}/account", response_model=ApiResponse)
def account_mentor(
    cliente_id: str,
    payload: AccountMentorRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    try:
        preferences = identity_store.get_preferences(user.sub)
        role = str(preferences.get("learning_role") or "semi").strip().lower()
        guide = generate_account_mentor_guide(
            cliente_id,
            payload.model_dump(exclude={"force"}),
            learning_role=role,
            force=payload.force,
        )
    except PermissionError as exc:
        raise_api_error(status_code=status.HTTP_403_FORBIDDEN, code="AI_CLIENT_DATA_DISABLED", message=str(exc))
    except RuntimeError as exc:
        raise_api_error(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, code="MENTOR_UNAVAILABLE", message=str(exc))
    return ApiResponse(data=guide)


@router.post("/{cliente_id}/reply", response_model=ApiResponse)
def mentor_reply(
    cliente_id: str,
    payload: MentorReplyRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    try:
        preferences = identity_store.get_preferences(user.sub)
        role = str(preferences.get("learning_role") or "semi").strip().lower()
        result = reply_to_mentor(
            cliente_id,
            account_context=payload.account_context,
            auditor_response=payload.auditor_response,
            learning_role=role,
            user_id=user.sub,
            session_id=payload.session_id,
        )
        mentor_payload = result.get("turn", {}).get("mentor", {})
        resources = mentor_payload.get("recommended_resources", {}) if isinstance(mentor_payload, dict) else {}
        resource_codes = [
            str(item.get("id") or item.get("code") or "")
            for group in ("procedures", "norms")
            for item in (resources.get(group, []) if isinstance(resources, dict) else [])
            if isinstance(item, dict)
        ]
        record_mentor_learning(
            str(user.user_id or user.sub),
            progress_stage=str(mentor_payload.get("progress_stage") or "observe"),
            ready_to_continue=bool(mentor_payload.get("ready_to_continue")),
            resource_codes=resource_codes,
        )
    except PermissionError as exc:
        raise_api_error(status_code=status.HTTP_403_FORBIDDEN, code="MENTOR_SESSION_FORBIDDEN", message=str(exc))
    except ValueError as exc:
        raise_api_error(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="MENTOR_REPLY_INVALID", message=str(exc))
    except RuntimeError as exc:
        raise_api_error(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, code="MENTOR_UNAVAILABLE", message=str(exc))
    return ApiResponse(data=result)


@router.get("/{cliente_id}/sessions/{session_id}", response_model=ApiResponse)
def mentor_session(
    cliente_id: str,
    session_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    session = get_mentor_session(cliente_id, session_id, user.sub)
    if session is None:
        raise_api_error(status_code=status.HTTP_404_NOT_FOUND, code="MENTOR_SESSION_NOT_FOUND", message="Sesión no encontrada.")
    return ApiResponse(data=session)
