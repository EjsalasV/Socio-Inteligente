from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import append_hallazgo, repo
from backend.schemas import (
    ApiResponse,
    AreaCheckRequest,
    AreaConclusionRequest,
    AreaWorkspaceResponse,
    UserContext,
)
from backend.services.realtime_collab_service import hub
from backend.validation import normalize_area_doc_v1, validate_area_doc_v1

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("/{cliente_id}/{area_code}", response_model=ApiResponse)
def get_area(cliente_id: str, area_code: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    detail = repo.get_area_detail(cliente_id, area_code)
    return ApiResponse(data=AreaWorkspaceResponse(**detail).model_dump())


@router.patch("/{cliente_id}/{area_code}/cuentas/{cuenta_codigo}/check", response_model=ApiResponse)
def patch_check(
    cliente_id: str,
    area_code: str,
    cuenta_codigo: str,
    payload: AreaCheckRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    area_doc = repo.read_area_yaml(cliente_id, area_code)
    normalized = normalize_area_doc_v1(area_doc, area_code=area_code)
    checks = normalized.get("revision_checks", {}) if isinstance(normalized.get("revision_checks"), dict) else {}
    checks[str(cuenta_codigo)] = bool(payload.checked)
    normalized["revision_checks"] = checks

    is_valid, errors = validate_area_doc_v1(normalized, area_code=area_code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Area invalida para schema v1.", "errors": errors, "schema_version": "v1"},
        )

    repo.write_area_yaml(cliente_id, area_code, normalized)
    hub.publish_event_sync(
        cliente_id=cliente_id,
        event_name="area_check_updated",
        actor=user.display_name or user.sub,
        payload={
            "area_code": area_code,
            "cuenta_codigo": str(cuenta_codigo),
            "checked": bool(payload.checked),
        },
    )
    return ApiResponse(data={"saved": True, "cuenta_codigo": str(cuenta_codigo), "checked": bool(payload.checked)})


@router.put("/{cliente_id}/{area_code}/conclusion", response_model=ApiResponse)
def put_conclusion(
    cliente_id: str,
    area_code: str,
    payload: AreaConclusionRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    if not payload.conclusion.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="conclusion cannot be empty")

    area_doc = repo.read_area_yaml(cliente_id, area_code)
    normalized = normalize_area_doc_v1(area_doc, area_code=area_code)
    normalized["conclusion"] = payload.conclusion.strip()

    coverage = normalized.get("afirmaciones_coverage")
    if isinstance(coverage, list):
        updated = []
        for item in coverage:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            row["covered"] = True
            row["evidencia"] = str(row.get("evidencia") or "Conclusion documentada.")
            updated.append(row)
        normalized["afirmaciones_coverage"] = updated

    is_valid, errors = validate_area_doc_v1(normalized, area_code=area_code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Area invalida para schema v1.", "errors": errors, "schema_version": "v1"},
        )

    repo.write_area_yaml(cliente_id, area_code, normalized)
    hub.publish_event_sync(
        cliente_id=cliente_id,
        event_name="area_conclusion_updated",
        actor=user.display_name or user.sub,
        payload={"area_code": area_code},
    )
    append_hallazgo(cliente_id, f"## Area {area_code}\n\n{payload.conclusion.strip()}")
    return ApiResponse(data={"saved": True, "cliente_id": cliente_id, "area_code": area_code})
