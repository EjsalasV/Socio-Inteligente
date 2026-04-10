from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.auth import get_current_user
from backend.constants.runtime_config import get_runtime_config
from backend.middleware.rate_limit import get_rate_limit_metrics_snapshot, rate_limit_backend_name
from backend.repositories.file_repository import append_audit_log
from backend.repositories.identity_repository import store as identity_store
from backend.schemas import (
    AdminUserAssignClientesRequest,
    AdminUserCreateRequest,
    AdminUserPatchRequest,
    AdminUserSummary,
    ApiResponse,
    UserContext,
)
from backend.services.observability_service import store as observability_store
from backend.services.rate_limit_service import RateLimitExceeded, rate_limiter
from backend.utils.api_errors import raise_api_error

router = APIRouter(prefix="/api/admin", tags=["admin"])
RUNTIME_CFG = get_runtime_config()


def _role_norm(user: UserContext) -> str:
    return str(user.role or "").strip().lower()


def _ensure_admin_access(user: UserContext) -> None:
    if _role_norm(user) in {"admin", "socio"}:
        return
    raise_api_error(
        status_code=status.HTTP_403_FORBIDDEN,
        code="ADMIN_ACCESS_DENIED",
        message="Solo perfiles admin o socio pueden acceder a esta seccion.",
        action_hint="Solicita permisos al administrador del sistema.",
        retryable=False,
    )


def _admin_write_limit_per_minute() -> int:
    cfg = RUNTIME_CFG.get("rate_limit", {}) if isinstance(RUNTIME_CFG, dict) else {}
    raw = cfg.get("admin_writes_per_minute", 20) if isinstance(cfg, dict) else 20
    try:
        value = int(raw)
    except Exception:
        value = 20
    return max(1, min(value, 200))


def _enforce_admin_write_rate_limit(user: UserContext, action: str) -> None:
    subject = str(user.user_id or user.sub or "anonymous").strip().lower()
    scope = f"admin:{action}"
    limit = _admin_write_limit_per_minute()
    try:
        rate_limiter.enforce(
            scope=scope,
            subject=subject,
            limit=limit,
            window_seconds=60,
        )
    except RateLimitExceeded as exc:
        raise_api_error(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="ADMIN_RATE_LIMIT_EXCEEDED",
            message=(
                f"Demasiadas solicitudes administrativas para {action}. "
                f"Limite: {exc.limit} por {exc.window_seconds}s."
            ),
            action_hint=f"Espera {exc.retry_after_seconds}s antes de reintentar.",
            retryable=True,
            details={
                "retry_after_seconds": exc.retry_after_seconds,
                "scope": scope,
            },
        )


def _user_summary(row: dict, cliente_ids: list[str]) -> dict:
    return AdminUserSummary(
        user_id=str(row.get("user_id") or "").strip(),
        username=str(row.get("username") or "").strip(),
        display_name=str(row.get("display_name") or row.get("username") or "").strip(),
        role=str(row.get("role") or "auditor").strip().lower(),
        active=bool(row.get("active", True)),
        cliente_ids=cliente_ids,
        created_at=str(row.get("created_at") or ""),
        updated_at=str(row.get("updated_at") or ""),
    ).model_dump()


@router.get("/users", response_model=ApiResponse)
def get_users(user: UserContext = Depends(get_current_user)) -> ApiResponse:
    _ensure_admin_access(user)
    identity_store.ensure_legacy_admin()
    rows = identity_store.list_users()
    out: list[dict] = []
    for row in rows:
        uid = str(row.get("user_id") or "").strip()
        out.append(_user_summary(row, identity_store.get_user_clientes(uid)))
    out.sort(key=lambda x: x.get("username", ""))
    return ApiResponse(data={"users": out})


@router.post("/users", response_model=ApiResponse)
def post_user(payload: AdminUserCreateRequest, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    _ensure_admin_access(user)
    _enforce_admin_write_rate_limit(user, "create_user")
    try:
        created = identity_store.create_user(
            username=payload.username,
            password=payload.password,
            role=payload.role,
            display_name=payload.display_name,
            active=payload.active,
        )
        assigned = identity_store.set_user_clientes(
            str(created.get("user_id") or ""),
            payload.cliente_ids,
        )
    except ValueError as exc:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="ADMIN_USER_CREATE_INVALID",
            message=str(exc),
            action_hint="Corrige username/rol y vuelve a intentar.",
            retryable=False,
        )
    except Exception:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ADMIN_USER_CREATE_FAILED",
            message="No se pudo crear el usuario.",
            action_hint="Reintenta y valida configuracion de persistencia.",
            retryable=True,
        )
    append_audit_log(
        user_id=user.sub,
        cliente_id="*",
        endpoint="POST /api/admin/users",
        extra={
            "target_user_id": created.get("user_id"),
            "target_username": created.get("username"),
            "assigned_clientes": assigned,
        },
    )
    return ApiResponse(data={"user": _user_summary(created, assigned)})


@router.patch("/users/{user_id}", response_model=ApiResponse)
def patch_user(
    user_id: str,
    payload: AdminUserPatchRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    _ensure_admin_access(user)
    _enforce_admin_write_rate_limit(user, "patch_user")
    patch = payload.model_dump(exclude_none=True)
    try:
        updated = identity_store.update_user(user_id, patch)
        assigned = identity_store.get_user_clientes(user_id)
    except ValueError as exc:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ADMIN_USER_NOT_FOUND",
            message=str(exc),
            action_hint="Verifica el user_id solicitado.",
            retryable=False,
        )
    except Exception:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ADMIN_USER_PATCH_FAILED",
            message="No se pudo actualizar el usuario.",
            action_hint="Reintenta y valida conectividad.",
            retryable=True,
        )
    append_audit_log(
        user_id=user.sub,
        cliente_id="*",
        endpoint="PATCH /api/admin/users/{user_id}",
        extra={"target_user_id": user_id, "patched_keys": sorted(list(patch.keys()))},
    )
    return ApiResponse(data={"user": _user_summary(updated, assigned)})


@router.put("/users/{user_id}/clientes", response_model=ApiResponse)
def put_user_clientes(
    user_id: str,
    payload: AdminUserAssignClientesRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    _ensure_admin_access(user)
    _enforce_admin_write_rate_limit(user, "assign_clientes")
    try:
        assigned = identity_store.set_user_clientes(user_id, payload.cliente_ids)
    except Exception:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ADMIN_ASSIGN_CLIENTES_FAILED",
            message="No se pudo actualizar la asignacion de clientes.",
            action_hint="Reintenta y valida IDs de cliente.",
            retryable=True,
        )
    append_audit_log(
        user_id=user.sub,
        cliente_id="*",
        endpoint="PUT /api/admin/users/{user_id}/clientes",
        extra={"target_user_id": user_id, "assigned_clientes": assigned},
    )
    return ApiResponse(data={"user_id": user_id, "cliente_ids": assigned})


@router.get("/clientes/{cliente_id}/miembros", response_model=ApiResponse)
def get_cliente_members(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    _ensure_admin_access(user)
    members = identity_store.list_members_by_cliente(cliente_id)
    return ApiResponse(data={"cliente_id": cliente_id, "miembros": members})


@router.get("/rate-limit/metrics", response_model=ApiResponse)
def get_rate_limit_metrics(user: UserContext = Depends(get_current_user)) -> ApiResponse:
    _ensure_admin_access(user)
    snapshot = get_rate_limit_metrics_snapshot()
    return ApiResponse(
        data={
            "backend_slowapi": rate_limit_backend_name(),
            "backend_service": rate_limiter.backend,
            "snapshot": snapshot,
            "observability": observability_store.snapshot(),
        }
    )
