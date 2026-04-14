from __future__ import annotations

import os
import threading
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.auth import authorize_cliente_access, get_current_user
from backend.constants.runtime_config import get_runtime_config
from backend.repositories.file_repository import (
    list_area_codes,
    read_area_yaml,
    read_hallazgos,
    read_perfil,
    read_workpapers,
    write_workpapers,
)
from backend.schemas import (
    ApiResponse,
    CoverageSummary,
    QualityGateItem,
    UserContext,
    WorkpaperPlanResponse,
    WorkpaperTask,
    WorkpaperTaskCreateRequest,
    WorkpaperTaskUpdateRequest,
)
from backend.services.judgement_service import recommend_workpaper_tasks_from_strategy
from backend.services.realtime_collab_service import hub
from backend.services.view_cache_service import invalidate_view_cache_for_cliente

router = APIRouter(prefix="/papeles-trabajo", tags=["papeles-trabajo"])
RUNTIME_CFG = get_runtime_config()
WORKFLOW_CFG = RUNTIME_CFG.get("workflow", {}) if isinstance(RUNTIME_CFG, dict) else {}
THRESHOLDS = WORKFLOW_CFG.get("thresholds", {}) if isinstance(WORKFLOW_CFG, dict) else {}
EXEC_MIN_PCT = float(THRESHOLDS.get("exec_required_completion_pct", 70.0) or 70.0)
REPORT_MIN_PCT = float(THRESHOLDS.get("report_required_completion_pct", 95.0) or 95.0)
EXEC_COVERAGE_HIGH_MIN_PCT = float(THRESHOLDS.get("exec_coverage_high_min_pct", 100.0) or 100.0)
EXEC_COVERAGE_MEDIUM_MIN_PCT = float(THRESHOLDS.get("exec_coverage_medium_min_pct", 80.0) or 80.0)

_WORKPAPERS_LOCKS: dict[str, threading.Lock] = {}
_WORKPAPERS_LOCKS_GUARD = threading.Lock()


def _get_workpapers_lock(cliente_id: str) -> threading.Lock:
    key = str(cliente_id or "").strip().lower()
    with _WORKPAPERS_LOCKS_GUARD:
        lock = _WORKPAPERS_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _WORKPAPERS_LOCKS[key] = lock
    return lock


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "si", "yes"}
    return False


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _normalize_assertion_name(value: Any) -> str:
    return str(value or "").strip().lower()


def _workpaper_ai_tasks_enabled() -> bool:
    raw = str(os.getenv("WORKPAPER_AI_TASKS_ENABLED") or "0").strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


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

    # Sugerencias de juicio AI desactivadas por defecto para evitar latencia extrema en endpoints GET.
    if _workpaper_ai_tasks_enabled():
        try:
            from backend.routes.risk_engine import _build_strategy_deterministic, _from_area_files, _from_ranking
            from backend.services.judgement_service import build_risk_judgement_with_ai

            areas = _from_ranking(cliente_id)
            if not areas:
                areas = _from_area_files(cliente_id)
            if areas:
                deterministic = _build_strategy_deterministic(areas)
                judged = build_risk_judgement_with_ai(cliente_id, areas=areas, deterministic=deterministic)
                templates.extend(recommend_workpaper_tasks_from_strategy(judged, max_tasks=8))
        except Exception:
            pass

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


def _compute_assertion_coverage(cliente_id: str, tasks: list[dict[str, Any]]) -> CoverageSummary:
    area_codes = list_area_codes(cliente_id)
    missing_by_area: dict[str, list[str]] = {}

    total = 0
    covered = 0

    for area_code in area_codes:
        area = read_area_yaml(cliente_id, area_code)
        criticas = area.get("afirmaciones_criticas")
        coverage_rows = area.get("afirmaciones_coverage")
        if not isinstance(criticas, list):
            criticas = []
        if not isinstance(coverage_rows, list):
            coverage_rows = []

        covered_map: dict[str, bool] = {}
        for row in coverage_rows:
            if not isinstance(row, dict):
                continue
            nombre = _normalize_assertion_name(row.get("nombre"))
            if not nombre:
                continue
            is_covered = bool(row.get("covered", False))
            evidencia = str(row.get("evidencia") or "").strip()
            covered_map[nombre] = is_covered and bool(evidencia)

        area_missing: list[str] = []
        for raw_assertion in criticas:
            assertion = str(raw_assertion or "").strip()
            if not assertion:
                continue
            total += 1
            is_covered = covered_map.get(_normalize_assertion_name(assertion), False)
            if is_covered:
                covered += 1
            else:
                area_missing.append(assertion)
        if area_missing:
            missing_by_area[area_code] = area_missing

    pct = (covered / total * 100.0) if total else 0.0
    return CoverageSummary(
        total_assertions=total,
        covered_assertions=covered,
        coverage_pct=round(pct, 2),
        missing_by_area=missing_by_area,
    )


def _quality_gates(cliente_id: str, tasks: list[dict[str, Any]]) -> tuple[list[QualityGateItem], CoverageSummary]:
    perfil = read_perfil(cliente_id)
    encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    materialidad = perfil.get("materialidad", {}) if isinstance(perfil.get("materialidad"), dict) else {}
    preliminar = materialidad.get("preliminar", {}) if isinstance(materialidad.get("preliminar"), dict) else {}
    final = materialidad.get("final", {}) if isinstance(materialidad.get("final"), dict) else {}

    has_materialidad = any(
        _safe_float(v, 0.0) > 0
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
    coverage = _compute_assertion_coverage(cliente_id, tasks)
    high_risk_area_codes: set[str] = set()
    medium_or_lower_area_codes: set[str] = set()
    for area_code in list_area_codes(cliente_id):
        area = read_area_yaml(cliente_id, area_code)
        riesgo = str(area.get("riesgo") or "medio").strip().lower()
        if riesgo in {"alto", "critico"}:
            high_risk_area_codes.add(area_code)
        else:
            medium_or_lower_area_codes.add(area_code)

    def _coverage_ok_for(codes: set[str], min_pct: float) -> bool:
        if not codes:
            return True
        total_local = 0
        covered_local = 0
        for code in codes:
            area = read_area_yaml(cliente_id, code)
            criticas = area.get("afirmaciones_criticas")
            cov_rows = area.get("afirmaciones_coverage")
            if not isinstance(criticas, list):
                continue
            cov_map: dict[str, bool] = {}
            if isinstance(cov_rows, list):
                for row in cov_rows:
                    if not isinstance(row, dict):
                        continue
                    n = _normalize_assertion_name(row.get("nombre"))
                    if not n:
                        continue
                    cov_map[n] = bool(row.get("covered", False)) and bool(str(row.get("evidencia") or "").strip())
            for assertion in criticas:
                a = str(assertion or "").strip()
                if not a:
                    continue
                total_local += 1
                if cov_map.get(_normalize_assertion_name(a), False):
                    covered_local += 1
        if total_local == 0:
            return True
        return (covered_local / total_local * 100.0) >= min_pct

    coverage_high_ok = _coverage_ok_for(high_risk_area_codes, EXEC_COVERAGE_HIGH_MIN_PCT)
    coverage_medium_ok = _coverage_ok_for(medium_or_lower_area_codes, EXEC_COVERAGE_MEDIUM_MIN_PCT)

    exec_ok = (
        completion >= EXEC_MIN_PCT
        and (not high_priority_areas or high_priority_areas.issubset(high_priority_done))
        and coverage_high_ok
        and coverage_medium_ok
        and plan_ok
    )

    hallazgos_text = read_hallazgos(cliente_id)
    has_conclusion = len(hallazgos_text.strip()) >= 120
    close_done = "close-conclusion-230" in done_ids if "close-conclusion-230" in required_ids else True
    report_ok = completion >= REPORT_MIN_PCT and has_conclusion and close_done and exec_ok and coverage.coverage_pct > 0

    if not base_fields_ok:
        plan_detail = "Faltan datos base del perfil del cliente."
    elif not has_materialidad:
        plan_detail = "No existe materialidad documentada (preliminar o final)."
    elif missing_plan_ids:
        plan_detail = f"Faltan papeles de planificacion: {', '.join(missing_plan_ids)}."
    else:
        plan_detail = "Perfil base, materialidad y planeacion documentados."

    if exec_ok:
        exec_detail = (
            f"Ejecucion suficiente ({completion:.1f}% papeles, cobertura afirmaciones {coverage.coverage_pct:.1f}%)."
        )
    else:
        missing_high = sorted(list(high_priority_areas - high_priority_done))
        if missing_high:
            exec_detail = f"Ejecucion insuficiente ({completion:.1f}%). Faltan areas criticas: {', '.join(missing_high)}."
        elif not coverage_high_ok or not coverage_medium_ok:
            details: list[str] = []
            if not coverage_high_ok:
                details.append(f"areas altas deben llegar a {EXEC_COVERAGE_HIGH_MIN_PCT:.0f}%")
            if not coverage_medium_ok:
                details.append(f"areas medias/bajas deben llegar a {EXEC_COVERAGE_MEDIUM_MIN_PCT:.0f}%")
            missing_codes = ", ".join(sorted(coverage.missing_by_area.keys())[:6]) or "sin detalle"
            exec_detail = (
                f"Ejecucion insuficiente por cobertura de afirmaciones ({coverage.coverage_pct:.1f}%). "
                f"Regla: {'; '.join(details)}. Faltantes en: {missing_codes}."
            )
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
        report_detail = "No listo para informe final: cobertura de afirmaciones incompleta."

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
    return gates, coverage


@router.get("/{cliente_id}", response_model=ApiResponse)
def get_workpapers(
    cliente_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(0, ge=0, le=500),
    area_code: str = Query(""),
    q: str = Query(""),
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    with _get_workpapers_lock(cliente_id):
        generated = _generate_tasks(cliente_id)
        merged = _merge_saved_tasks(cliente_id, generated)
        write_workpapers(cliente_id, merged)

    tasks_filtered = merged
    area_code_filter = area_code.strip().upper()
    if area_code_filter:
        tasks_filtered = [t for t in tasks_filtered if str(t.get("area_code") or "").strip().upper() == area_code_filter]

    query_filter = q.strip().lower()
    if query_filter:
        filtered: list[dict[str, Any]] = []
        for task in tasks_filtered:
            title = str(task.get("title") or "").lower()
            nia_ref = str(task.get("nia_ref") or "").lower()
            evidence_note = str(task.get("evidence_note") or "").lower()
            area_name = str(task.get("area_name") or "").lower()
            if query_filter in f"{title} {nia_ref} {evidence_note} {area_name}":
                filtered.append(task)
        tasks_filtered = filtered

    tasks_total_all = len(merged)
    tasks_total = len(tasks_filtered)
    if page_size <= 0:
        tasks_page = 1
        tasks_page_size = tasks_total
        tasks_has_more = False
        tasks_paged = tasks_filtered
    else:
        start = max(0, (page - 1) * page_size)
        end = start + page_size
        tasks_page = page
        tasks_page_size = page_size
        tasks_has_more = end < tasks_total
        tasks_paged = tasks_filtered[start:end]

    required = [t for t in merged if bool(t.get("required", True))]
    required_done = [t for t in required if bool(t.get("done", False))]
    completion = (len(required_done) / len(required) * 100.0) if required else 0.0
    gates, coverage = _quality_gates(cliente_id, merged)

    payload = WorkpaperPlanResponse(
        cliente_id=cliente_id,
        tasks=[WorkpaperTask(**task) for task in tasks_paged],
        gates=gates,
        completion_pct=round(completion, 2),
        coverage_summary=coverage,
        tasks_page=tasks_page,
        tasks_page_size=tasks_page_size,
        tasks_total=tasks_total,
        tasks_total_all=tasks_total_all,
        tasks_has_more=tasks_has_more,
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
    with _get_workpapers_lock(cliente_id):
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
    invalidate_view_cache_for_cliente(cliente_id)
    hub.publish_event_sync(
        cliente_id=cliente_id,
        event_name="workpaper_task_updated",
        actor=user.display_name or user.sub,
        payload={"task_id": task_id, "done": bool(payload.done)},
    )
    return ApiResponse(data={"task_id": task_id, "done": payload.done, "saved": True})


def _normalize_task_id(area_code: str, nia_ref: str, title: str) -> str:
    import re

    source = f"{area_code}-{nia_ref}-{title}".strip().lower()
    source = re.sub(r"[^a-z0-9]+", "-", source).strip("-")
    source = re.sub(r"-+", "-", source)
    return source[:120] or "task-manual"


@router.post("/{cliente_id}/tasks", response_model=ApiResponse)
def post_workpaper_task(
    cliente_id: str,
    payload: WorkpaperTaskCreateRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)

    area_code = payload.area_code.strip()
    area_name = payload.area_name.strip()
    title = payload.title.strip()
    nia_ref = payload.nia_ref.strip()
    prioridad = payload.prioridad.strip().lower() or "media"
    if not area_code or not area_name or not title:
        raise HTTPException(status_code=422, detail="area_code, area_name y title son obligatorios.")

    with _get_workpapers_lock(cliente_id):
        tasks = read_workpapers(cliente_id)
        if not tasks:
            tasks = _generate_tasks(cliente_id)

        dedupe_key = f"{area_code}|{nia_ref.lower()}|{title.lower()}"
        for task in tasks:
            key = f"{str(task.get('area_code') or '').strip()}|{str(task.get('nia_ref') or '').strip().lower()}|{str(task.get('title') or '').strip().lower()}"
            if key == dedupe_key:
                return ApiResponse(data={"created": False, "task": WorkpaperTask(**task).model_dump()})

        task_id = _normalize_task_id(area_code, nia_ref, title)
        existing_ids = {str(t.get("id") or "") for t in tasks}
        if task_id in existing_ids:
            suffix = 2
            base = task_id
            while f"{base}-{suffix}" in existing_ids:
                suffix += 1
            task_id = f"{base}-{suffix}"

        new_task = {
            "id": task_id,
            "area_code": area_code,
            "area_name": area_name,
            "title": title,
            "nia_ref": nia_ref,
            "prioridad": prioridad,
            "required": bool(payload.required),
            "done": False,
            "evidence_note": payload.evidence_note.strip(),
        }
        tasks.append(new_task)
        write_workpapers(cliente_id, tasks)
    invalidate_view_cache_for_cliente(cliente_id)
    hub.publish_event_sync(
        cliente_id=cliente_id,
        event_name="workpaper_task_created",
        actor=user.display_name or user.sub,
        payload={"task_id": task_id, "area_code": area_code},
    )
    return ApiResponse(data={"created": True, "task": WorkpaperTask(**new_task).model_dump()})


@router.delete("/{cliente_id}/tasks/{task_id}", response_model=ApiResponse)
def delete_workpaper_task(
    cliente_id: str,
    task_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    with _get_workpapers_lock(cliente_id):
        tasks = read_workpapers(cliente_id)
        if not tasks:
            raise HTTPException(status_code=404, detail="No hay papeles de trabajo para este cliente.")

        initial_len = len(tasks)
        filtered = [task for task in tasks if str(task.get("id") or "") != task_id]
        if len(filtered) == initial_len:
            raise HTTPException(status_code=404, detail=f"Tarea no encontrada: {task_id}")

        write_workpapers(cliente_id, filtered)
    invalidate_view_cache_for_cliente(cliente_id)
    hub.publish_event_sync(
        cliente_id=cliente_id,
        event_name="workpaper_task_deleted",
        actor=user.display_name or user.sub,
        payload={"task_id": task_id},
    )
    return ApiResponse(data={"task_id": task_id, "deleted": True})
