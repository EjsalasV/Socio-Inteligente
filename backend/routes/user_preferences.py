from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.auth import get_current_user
from backend.repositories.file_repository import append_audit_log
from backend.repositories.identity_repository import store as identity_store
from backend.schemas import ApiResponse, UserContext, UserPreferencesPatchRequest, UserPreferencesResponse
from backend.utils.api_errors import raise_api_error

router = APIRouter(prefix="/api/user", tags=["user"])


def _prefs_user_id(user: UserContext) -> str:
    uid = str(user.user_id or "").strip()
    if uid:
        return uid
    # Legacy fallback: keep preferences isolated per subject when user_id is not present.
    return f"legacy::{user.sub}"


@router.get("/preferences", response_model=ApiResponse)
def get_preferences(user: UserContext = Depends(get_current_user)) -> ApiResponse:
    uid = _prefs_user_id(user)
    try:
        prefs = identity_store.get_preferences(uid)
    except Exception:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="USER_PREFERENCES_READ_FAILED",
            message="No se pudieron cargar las preferencias del usuario.",
            action_hint="Reintenta en unos segundos.",
            retryable=True,
        )
    return ApiResponse(data=UserPreferencesResponse(**prefs).model_dump())


@router.patch("/preferences", response_model=ApiResponse)
def patch_preferences(
    payload: UserPreferencesPatchRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    uid = _prefs_user_id(user)
    patch = payload.model_dump(exclude_none=True)
    try:
        prefs = identity_store.patch_preferences(uid, patch)
    except Exception:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="USER_PREFERENCES_PATCH_FAILED",
            message="No se pudieron actualizar las preferencias del usuario.",
            action_hint="Verifica conectividad y reintenta.",
            retryable=True,
        )
    append_audit_log(
        user_id=user.sub,
        cliente_id="*",
        endpoint="PATCH /api/user/preferences",
        extra={"patched_keys": sorted(list(patch.keys()))},
    )
    return ApiResponse(data=UserPreferencesResponse(**prefs).model_dump())

