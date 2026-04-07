from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from backend.repositories.file_repository import list_area_codes, read_area_yaml, read_hallazgos, read_perfil, read_workflow, write_workflow

ROOT = Path(__file__).resolve().parents[2]

PHASE_TEMPLATES: dict[str, dict[str, Any]] = {
    "planificacion": {
        "obligatorios": [
            "cliente.nombre_legal",
            "encargo.anio_activo",
            "encargo.marco_referencial",
            "materialidad.final.materialidad_planeacion",
        ],
        "autorrellenables": [
            "riesgo_global.nivel",
            "encargo.fase_actual",
            "areas_con_riesgo",
        ],
        "solo_lectura_historica": [
            "transitions",
            "hallazgos_resumen",
        ],
    },
    "ejecucion": {
        "obligatorios": [
            "materialidad.final.materialidad_ejecucion",
            "areas[*].afirmaciones_criticas",
            "areas[*].procedimientos",
        ],
        "autorrellenables": [
            "areas[*].hallazgos_abiertos",
            "workflow.gates",
            "hallazgos_resumen",
        ],
        "solo_lectura_historica": [
            "transitions",
        ],
    },
    "cierre": {
        "obligatorios": [
            "hallazgos_conclusion_general",
            "areas[*].conclusion",
            "workflow.gates",
        ],
        "autorrellenables": [
            "hallazgos_resumen",
            "areas[*].hallazgos_abiertos",
            "materialidad.final",
        ],
        "solo_lectura_historica": [
            "transitions",
        ],
    },
}


def _get_nested(doc: dict[str, Any], path: str) -> Any:
    cur: Any = doc
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _phase_key(raw: str) -> str:
    v = str(raw or "").strip().lower()
    if "plan" in v:
        return "planificacion"
    if "ejec" in v or "visit" in v:
        return "ejecucion"
    if "cierre" in v or "inform" in v:
        return "cierre"
    return "planificacion"


def build_phase_template(cliente_id: str, *, phase: str | None = None) -> dict[str, Any]:
    perfil = read_perfil(cliente_id) or {}
    workflow = read_workflow(cliente_id) or {}
    encargo = perfil.get("encargo") if isinstance(perfil.get("encargo"), dict) else {}
    phase_key = _phase_key(phase or encargo.get("fase_actual") or workflow.get("phase") or "planificacion")

    template = PHASE_TEMPLATES.get(phase_key, PHASE_TEMPLATES["planificacion"])
    missing: list[str] = []

    for req in template.get("obligatorios") or []:
        req = str(req)
        if req.startswith("areas[*]."):
            field = req.replace("areas[*].", "", 1)
            for code in list_area_codes(cliente_id):
                area = read_area_yaml(cliente_id, code)
                val = area.get(field)
                if not val:
                    missing.append(f"{code}.{field}")
        elif req == "hallazgos_conclusion_general":
            hall = str(read_hallazgos(cliente_id) or "").strip()
            if len(hall) < 120:
                missing.append(req)
        elif req == "workflow.gates":
            gates = workflow.get("gates") if isinstance(workflow.get("gates"), list) else []
            if not gates:
                missing.append(req)
        else:
            if not _get_nested(perfil, req):
                missing.append(req)

    areas_riesgo: list[dict[str, Any]] = []
    for code in list_area_codes(cliente_id):
        area = read_area_yaml(cliente_id, code)
        areas_riesgo.append(
            {
                "codigo": code,
                "nombre": str(area.get("nombre") or f"Area {code}"),
                "riesgo": str(area.get("riesgo") or "medio"),
                "estado": str(area.get("estado_area") or "pendiente"),
            }
        )

    hall_summary = {
        "total_open": 0,
        "high_open": 0,
    }
    for code in list_area_codes(cliente_id):
        area = read_area_yaml(cliente_id, code)
        hallazgos = area.get("hallazgos_abiertos") if isinstance(area.get("hallazgos_abiertos"), list) else []
        for h in hallazgos:
            if not isinstance(h, dict):
                continue
            estado = str(h.get("estado") or "abierto").lower()
            if estado in {"abierto", "open", "pendiente"}:
                hall_summary["total_open"] += 1
                if str(h.get("prioridad") or "").lower() in {"alta", "critica", "crítico"}:
                    hall_summary["high_open"] += 1

    prefilled = {
        "cliente": perfil.get("cliente") if isinstance(perfil.get("cliente"), dict) else {},
        "encargo": encargo,
        "materialidad": perfil.get("materialidad") if isinstance(perfil.get("materialidad"), dict) else {},
        "workflow": workflow,
        "areas_con_riesgo": areas_riesgo,
        "hallazgos_resumen": hall_summary,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    hist = workflow.get("field_history") if isinstance(workflow.get("field_history"), list) else []

    return {
        "cliente_id": cliente_id,
        "phase": phase_key,
        "template": template,
        "prefilled": prefilled,
        "checklist": {
            "missing_required": missing,
            "can_advance": len(missing) == 0,
        },
        "field_history": hist,
    }


def record_field_history(cliente_id: str, *, phase: str, field: str, old_value: Any, new_value: Any, user_id: str) -> None:
    workflow = read_workflow(cliente_id) or {}
    history = workflow.get("field_history") if isinstance(workflow.get("field_history"), list) else []
    history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": _phase_key(phase),
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "user_id": user_id,
        }
    )
    workflow["field_history"] = history[-500:]
    write_workflow(cliente_id, workflow)
