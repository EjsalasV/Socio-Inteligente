from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.auth import authorize_cliente_access, get_current_user
from backend.constants.runtime_config import get_runtime_config
from backend.repositories.file_repository import read_hallazgos, read_perfil, read_workpapers, write_workpapers
from backend.schemas import (
    ApiResponse,
    QualityGateItem,
    UserContext,
    WorkpaperPlanResponse,
    WorkpaperTask,
    WorkpaperTaskUpdateRequest,
)

router = APIRouter(prefix="/papeles-trabajo", tags=["papeles-trabajo"])
RUNTIME_CFG = get_runtime_config()


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "si", "yes"}
    return False


def _build_methodology_tasks(perfil: dict[str, Any]) -> list[dict[str, Any]]:
    encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}
    operacion = perfil.get("operacion", {}) if isinstance(perfil.get("operacion"), dict) else {}
    nomina = perfil.get("nomina", {}) if isinstance(perfil.get("nomina"), dict) else {}
    contexto = perfil.get("contexto_negocio", {}) if isinstance(perfil.get("contexto_negocio"), dict) else {}
    banderas = perfil.get("banderas_generales", {}) if isinstance(perfil.get("banderas_generales"), dict) else {}

    tasks = [
        {
            "id": "plan-memo-300",
            "area_code": "PLAN",
            "area_name": "Planeacion del Encargo",
            "title": "Memorando de planeacion y estrategia de auditoria",
            "nia_ref": "NIA 300",
            "prioridad": "alta",
            "required": True,
            "done": False,
            "evidence_note": "",
        },
        {
            "id": "plan-riesgo-315",
            "area_code": "PLAN",
            "area_name": "Planeacion del Encargo",
            "title": "Matriz de riesgos y aseveraciones documentada",
            "nia_ref": "NIA 315",
            "prioridad": "alta",
            "required": True,
            "done": False,
            "evidence_note": "",
        },
        {
            "id": "plan-materialidad-320",
            "area_code": "PLAN",
            "area_name": "Planeacion del Encargo",
            "title": "Materialidad de planeacion y ejecucion aprobada",
            "nia_ref": "NIA 320",
            "prioridad": "alta",
            "required": True,
            "done": False,
            "evidence_note": "",
        },
        {
            "id": "close-conclusion-230",
            "area_code": "CLOSE",
            "area_name": "Cierre y Calidad",
            "title": "Conclusiones por area y archivo final de papeles",
            "nia_ref": "NIA 230",
            "prioridad": "alta",
            "required": True,
            "done": False,
            "evidence_note": "",
        },
    ]

    if _is_true(operacion.get("tiene_inventarios_significativos")):
        tasks.append(
            {
                "id": "inv-conteo-501",
                "area_code": "INV",
                "area_name": "Inventarios",
                "title": "Conteo fisico y pruebas de valuacion de inventarios",
                "nia_ref": "NIA 501",
                "prioridad": "alta",
                "required": True,
                "done": False,
                "evidence_note": "",
            }
        )

    if _is_true(nomina.get("tiene_empleados")) or _is_true(operacion.get("tiene_empleados")):
        tasks.append(
            {
                "id": "nom-pruebas-500",
                "area_code": "NOM",
                "area_name": "Nomina y Beneficios",
                "title": "Pruebas de nomina, beneficios y obligaciones laborales",
                "nia_ref": "NIA 500",
                "prioridad": "media",
                "required": True,
                "done": False,
                "evidence_note": "",
            }
        )

    if _is_true(contexto.get("tiene_partes_relacionadas")) or _is_true(banderas.get("problemas_partes_relacionadas")):
        tasks.append(
            {
                "id": "pr-rel-550",
                "area_code": "PR",
                "area_name": "Partes Relacionadas",
                "title": "Procedimientos sobre partes relacionadas y revelaciones",
                "nia_ref": "NIA 550",
                "prioridad": "alta",
                "required": True,
                "done": False,
                "evidence_note": "",
            }
        )

    if _is_true(operacion.get("tiene_cartera_significativa")):
        tasks.append(
            {
                "id": "cxp-confirm-505",
                "area_code": "130",
                "area_name": "Cuentas por Cobrar",
                "title": "Circularizacion de cartera significativa",
                "nia_ref": "NIA 505",
                "prioridad": "alta",
                "required": True,
                "done": False,
                "evidence_note": "",
            }
        )

    if _is_true(banderas.get("riesgo_tributario_general")):
        tasks.append(
            {
                "id": "tax-250",
                "area_code": "TAX",
                "area_name": "Cumplimiento Tributario",
                "title": "Revision de contingencias y cumplimiento legal tributario",
                "nia_ref": "NIA 250",
                "prioridad": "media",
                "required": True,
                "done": False,
                "evidence_note": "",
            }
        )

    if str(encargo.get("tipo_encargo") or "").strip().lower() == "auditoria_externa":
        tasks.append(
            {
                "id": "fraud-240",
                "area_code": "FRAUD",
                "area_name": "Riesgo de Fraude",
                "title": "Evaluacion de riesgo de fraude y respuesta del equipo",
                "nia_ref": "NIA 240",
                "prioridad": "media",
                "required": True,
                "done": False,
                "evidence_note": "",
            }
        )

    return tasks


def _generate_tasks(cliente_id: str) -> list[dict[str, Any]]:
    perfil = read_perfil(cliente_id)
    try:
        from analysis.ranking_areas import calcular_ranking_areas

        ranking = calcular_ranking_areas(cliente_id)
    except Exception:
        ranking = None

    if ranking is None or ranking.empty:
        return []

    if "con_saldo" in ranking.columns:
        ranking = ranking[ranking["con_saldo"] == True]  # noqa: E712
    if ranking.empty:
        return _build_methodology_tasks(perfil)

    templates = _build_methodology_tasks(perfil)
    for _, row in ranking.sort_values("score_riesgo", ascending=False).head(6).iterrows():
        area_code = str(row.get("area") or "")
        area_name = str(row.get("nombre") or f"Area {area_code}")
        prioridad = str(row.get("prioridad") or "media")

        templates.append(
            {
                "id": f"{area_code}-analitica",
                "area_code": area_code,
                "area_name": area_name,
                "title": "Procedimiento analitico focalizado",
                "nia_ref": "NIA 520",
                "prioridad": prioridad,
                "required": True,
                "done": False,
                "evidence_note": "",
            }
        )
        templates.append(
            {
                "id": f"{area_code}-detalle",
                "area_code": area_code,
                "area_name": area_name,
                "title": "Prueba sustantiva de detalle",
                "nia_ref": "NIA 500",
                "prioridad": prioridad,
                "required": True,
                "done": False,
                "evidence_note": "",
            }
        )

        area_name_lower = area_name.lower()
        if area_code.startswith("130") or "cobrar" in area_name_lower:
            templates.append(
                {
                    "id": f"{area_code}-confirmacion",
                    "area_code": area_code,
                    "area_name": area_name,
                    "title": "Confirmacion externa de saldos",
                    "nia_ref": "NIA 505",
                    "prioridad": "alta",
                    "required": True,
                    "done": False,
                    "evidence_note": "",
                }
            )
        if area_code.startswith("140") or "efectivo" in area_name_lower or "banco" in area_name_lower:
            templates.append(
                {
                    "id": f"{area_code}-conciliacion",
                    "area_code": area_code,
                    "area_name": area_name,
                    "title": "Conciliaciones bancarias y corte",
                    "nia_ref": "NIA 505",
                    "prioridad": "alta",
                    "required": True,
                    "done": False,
                    "evidence_note": "",
                }
            )

    # dedupe by id preserving order
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in templates:
        task_id = str(item.get("id") or "")
        if not task_id or task_id in seen:
            continue
        seen.add(task_id)
        out.append(item)
    return out


def _merge_saved_tasks(cliente_id: str, generated: list[dict[str, Any]]) -> list[dict[str, Any]]:
    saved = read_workpapers(cliente_id)
    if not saved:
        return generated

    saved_by_id = {str(task.get("id") or ""): task for task in saved if isinstance(task, dict)}
    merged: list[dict[str, Any]] = []
    for task in generated:
        task_id = str(task.get("id") or "")
        if task_id in saved_by_id:
            prev = saved_by_id[task_id]
            task["done"] = bool(prev.get("done", False))
            task["evidence_note"] = str(prev.get("evidence_note", "") or "")
        merged.append(task)

    # preserve tasks manually added in past runs
    generated_ids = {str(t.get("id") or "") for t in generated}
    for task in saved:
        task_id = str(task.get("id") or "")
        if task_id and task_id not in generated_ids:
            merged.append(task)
    return merged


def _quality_gates(cliente_id: str, tasks: list[dict[str, Any]]) -> list[QualityGateItem]:
    perfil = read_perfil(cliente_id)
    encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    materialidad = perfil.get("materialidad", {}) if isinstance(perfil.get("materialidad"), dict) else {}
    preliminar = materialidad.get("preliminar", {}) if isinstance(materialidad.get("preliminar"), dict) else {}
    final = materialidad.get("final", {}) if isinstance(materialidad.get("final"), dict) else {}

    has_materialidad = any(
        float(v or 0) > 0
        for v in [
            preliminar.get("materialidad_global"),
            preliminar.get("materialidad_desempeno"),
            preliminar.get("error_trivial"),
            final.get("materialidad_planeacion"),
            final.get("materialidad_ejecucion"),
            final.get("umbral_trivialidad"),
        ]
    )

    required = [t for t in tasks if bool(t.get("required", True))]
    required_done = [t for t in required if bool(t.get("done", False))]
    completion = (len(required_done) / len(required) * 100.0) if required else 0.0

    plan_task_ids = {"plan-memo-300", "plan-riesgo-315", "plan-materialidad-320"}
    required_ids = {str(t.get("id") or "") for t in required}
    done_ids = {str(t.get("id") or "") for t in required_done}
    required_plan_ids = {x for x in plan_task_ids if x in required_ids}
    missing_plan_ids = sorted(list(required_plan_ids - done_ids))

    base_fields_ok = bool(encargo.get("anio_activo")) and bool(encargo.get("marco_referencial")) and bool(cliente.get("nombre_legal"))
    plan_ok = base_fields_ok and has_materialidad and len(missing_plan_ids) == 0

    high_priority_areas = {str(t.get("area_code") or "") for t in tasks if str(t.get("prioridad") or "").lower() == "alta"}
    high_priority_done = {
        str(t.get("area_code") or "")
        for t in tasks
        if str(t.get("prioridad") or "").lower() == "alta" and bool(t.get("done", False))
    }
    exec_ok = completion >= exec_min_pct and (not high_priority_areas or high_priority_areas.issubset(high_priority_done)) and plan_ok

    hallazgos_text = read_hallazgos(cliente_id)
    has_conclusion = len(hallazgos_text.strip()) >= 120
    close_done = "close-conclusion-230" in done_ids if "close-conclusion-230" in required_ids else True
    report_ok = completion >= report_min_pct and has_conclusion and close_done and exec_ok

    if not base_fields_ok:
        plan_detail = "Faltan datos base del perfil del cliente."
    elif not has_materialidad:
        plan_detail = "No existe materialidad documentada (preliminar o final)."
    elif missing_plan_ids:
        plan_detail = f"Faltan papeles de planificacion: {', '.join(missing_plan_ids)}."
    else:
        plan_detail = "Perfil base, materialidad y planeacion documentados."

    if exec_ok:
        exec_detail = f"Ejecucion suficiente ({completion:.1f}% de papeles requeridos)."
    else:
        missing_high = sorted(list(high_priority_areas - high_priority_done))
        if missing_high:
            exec_detail = f"Ejecucion insuficiente ({completion:.1f}%). Faltan areas criticas: {', '.join(missing_high)}."
        else:
            exec_detail = f"Ejecucion insuficiente ({completion:.1f}%). Completa papeles requeridos."

    if report_ok:
        report_detail = "Listo para informe final con trazabilidad de calidad."
    elif not exec_ok:
        report_detail = "No listo: primero debe aprobar Gate de Ejecucion."
    elif not close_done:
        report_detail = "No listo: falta concluir y cerrar papeles de trabajo (NIA 230)."
    elif not has_conclusion:
        report_detail = "No listo: falta conclusion tecnica consolidada en hallazgos."
    else:
        report_detail = "No listo para informe final."

    gates = [
        QualityGateItem(
            code="PLAN",
            title="Gate de Planificacion",
            status="ok" if plan_ok else "blocked",
            detail=plan_detail,
        ),
        QualityGateItem(
            code="EXEC",
            title="Gate de Ejecucion",
            status="ok" if exec_ok else "blocked",
            detail=exec_detail,
        ),
        QualityGateItem(
            code="REPORT",
            title="Gate de Informe",
            status="ok" if report_ok else "blocked",
            detail=report_detail,
        ),
    ]
    return gates


@router.get("/{cliente_id}", response_model=ApiResponse)
def get_workpapers(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    generated = _generate_tasks(cliente_id)
    merged = _merge_saved_tasks(cliente_id, generated)
    write_workpapers(cliente_id, merged)

    required = [t for t in merged if bool(t.get("required", True))]
    required_done = [t for t in required if bool(t.get("done", False))]
    completion = (len(required_done) / len(required) * 100.0) if required else 0.0
    gates = _quality_gates(cliente_id, merged)

    payload = WorkpaperPlanResponse(
        cliente_id=cliente_id,
        tasks=[WorkpaperTask(**task) for task in merged],
        gates=gates,
        completion_pct=round(completion, 2),
    )
    return ApiResponse(data=payload.model_dump())


@router.patch("/{cliente_id}/tasks/{task_id}", response_model=ApiResponse)
def patch_workpaper_task(
    cliente_id: str,
    task_id: str,
    payload: WorkpaperTaskUpdateRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    tasks = read_workpapers(cliente_id)
    if not tasks:
        raise HTTPException(status_code=404, detail="No hay papeles de trabajo para este cliente.")

    updated = False
    for task in tasks:
        if str(task.get("id") or "") == task_id:
            task["done"] = bool(payload.done)
            task["evidence_note"] = payload.evidence_note.strip()
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail=f"Tarea no encontrada: {task_id}")

    write_workpapers(cliente_id, tasks)
    return ApiResponse(data={"task_id": task_id, "done": payload.done, "saved": True})
    workflow_cfg = RUNTIME_CFG.get("workflow", {}) if isinstance(RUNTIME_CFG, dict) else {}
    thresholds = workflow_cfg.get("thresholds", {}) if isinstance(workflow_cfg, dict) else {}
    exec_min_pct = float(thresholds.get("exec_required_completion_pct", 70.0) or 70.0)
    report_min_pct = float(thresholds.get("report_required_completion_pct", 95.0) or 95.0)
