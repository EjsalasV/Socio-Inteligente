from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import read_perfil, write_perfil
from backend.routes.workpapers import _generate_tasks, _merge_saved_tasks, _quality_gates
from backend.schemas import ApiResponse, UserContext, WorkflowAdvanceRequest, WorkflowStateResponse

router = APIRouter(prefix="/workflow", tags=["workflow"])

PHASES = ["planificacion", "ejecucion", "informe"]


def _normalize_phase(raw: str) -> str:
    value = (raw or "").strip().lower()
    if "plan" in value:
        return "planificacion"
    if "ejec" in value or "visita" in value:
        return "ejecucion"
    if "inform" in value or "cier" in value:
        return "informe"
    return "planificacion"


def _next_phase(current: str) -> str:
    if current == "planificacion":
        return "ejecucion"
    if current == "ejecucion":
        return "informe"
    return "informe"


def _gates_by_code(cliente_id: str) -> dict[str, str]:
    generated = _generate_tasks(cliente_id)
    merged = _merge_saved_tasks(cliente_id, generated)
    gates = _quality_gates(cliente_id, merged)
    return {g.code: g.status for g in gates}


def _validate_transition(target: str, gates: dict[str, str]) -> list[str]:
    errors: list[str] = []
    if target == "ejecucion" and gates.get("PLAN") != "ok":
        errors.append("Gate PLAN debe estar en estado ok para pasar a ejecucion.")
    if target == "informe":
        if gates.get("EXEC") != "ok":
            errors.append("Gate EXEC debe estar en estado ok para pasar a informe.")
        if gates.get("REPORT") != "ok":
            errors.append("Gate REPORT debe estar en estado ok para pasar a informe.")
    return errors


@router.get("/{cliente_id}", response_model=ApiResponse)
def get_workflow_state(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    perfil = read_perfil(cliente_id)
    encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}
    current_phase = _normalize_phase(str(encargo.get("fase_actual") or "planificacion"))

    generated = _generate_tasks(cliente_id)
    merged = _merge_saved_tasks(cliente_id, generated)
    gates = _quality_gates(cliente_id, merged)
    state = WorkflowStateResponse(
        cliente_id=cliente_id,
        previous_phase=current_phase,
        current_phase=current_phase,
        changed=False,
        gates=gates,
    )
    return ApiResponse(data=state.model_dump())


@router.post("/{cliente_id}/advance", response_model=ApiResponse)
def advance_workflow(
    cliente_id: str,
    payload: WorkflowAdvanceRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    perfil = read_perfil(cliente_id)
    encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}
    previous_phase = _normalize_phase(str(encargo.get("fase_actual") or "planificacion"))
    target_phase = _normalize_phase(payload.target_phase or _next_phase(previous_phase))

    if target_phase not in PHASES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Fase objetivo invalida.")

    if PHASES.index(target_phase) < PHASES.index(previous_phase):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se permite retroceder de {previous_phase} a {target_phase}.",
        )

    gates_map = _gates_by_code(cliente_id)
    errors = _validate_transition(target_phase, gates_map)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Transicion bloqueada por quality gates.", "errors": errors, "gates": gates_map},
        )

    changed = target_phase != previous_phase
    if changed:
        perfil.setdefault("encargo", {})
        if isinstance(perfil["encargo"], dict):
            perfil["encargo"]["fase_actual"] = target_phase
        write_perfil(cliente_id, perfil)

    generated = _generate_tasks(cliente_id)
    merged = _merge_saved_tasks(cliente_id, generated)
    gates = _quality_gates(cliente_id, merged)

    state = WorkflowStateResponse(
        cliente_id=cliente_id,
        previous_phase=previous_phase,
        current_phase=target_phase,
        changed=changed,
        gates=gates,
    )
    return ApiResponse(data=state.model_dump())
