from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
PROGRESS_FILE = ROOT / "data" / "security" / "learning_progress.yaml"
_LOCK = RLock()

STAGES = {
    "observe": ("observacion_analitica", "Identificar hechos antes de concluir"),
    "connect": ("conexion_riesgo_aseveracion", "Conectar señales, riesgos y aseveraciones"),
    "test": ("diseno_evidencia", "Diseñar evidencia que confirme o refute hipótesis"),
    "reflect": ("juicio_y_reflexion", "Reflexionar sobre suficiencia y conclusiones"),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read() -> dict[str, Any]:
    if not PROGRESS_FILE.exists():
        return {}
    try:
        value = yaml.safe_load(PROGRESS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def _write(payload: dict[str, Any]) -> None:
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = PROGRESS_FILE.with_suffix(".tmp")
    temporary.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    temporary.replace(PROGRESS_FILE)


def record_mentor_learning(
    user_id: str,
    *,
    progress_stage: str,
    ready_to_continue: bool,
    resource_codes: list[str],
) -> dict[str, Any]:
    stage = progress_stage if progress_stage in STAGES else "observe"
    competency_id, label = STAGES[stage]
    with _LOCK:
        payload = _read()
        current = payload.get(user_id) if isinstance(payload.get(user_id), dict) else {}
        competencies = current.get("competencies") if isinstance(current.get("competencies"), dict) else {}
        competency = competencies.get(competency_id) if isinstance(competencies.get(competency_id), dict) else {}
        competency["label"] = label
        competency["practice_count"] = int(competency.get("practice_count") or 0) + 1
        competency["positive_count"] = int(competency.get("positive_count") or 0) + (1 if ready_to_continue else 0)
        competency["last_practiced_at"] = _now()
        competencies[competency_id] = competency
        resources = current.get("resource_codes") if isinstance(current.get("resource_codes"), dict) else {}
        for code in resource_codes[:8]:
            safe_code = str(code or "").strip()[:100]
            if safe_code:
                resources[safe_code] = int(resources.get(safe_code) or 0) + 1
        current.update(
            {
                "competencies": competencies,
                "resource_codes": resources,
                "total_sessions": int(current.get("total_sessions") or 0) + 1,
                "updated_at": _now(),
                "privacy": "No contiene cliente, cuenta, saldos, respuestas ni texto generado por IA.",
            }
        )
        payload[user_id] = current
        _write(payload)
        return build_learning_progress(user_id, payload=payload)


def build_learning_progress(user_id: str, *, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    source = payload if payload is not None else _read()
    current = source.get(user_id) if isinstance(source.get(user_id), dict) else {}
    competencies = current.get("competencies") if isinstance(current.get("competencies"), dict) else {}
    rows = []
    for competency_id, value in competencies.items():
        if not isinstance(value, dict):
            continue
        practice = int(value.get("practice_count") or 0)
        positive = int(value.get("positive_count") or 0)
        rows.append(
            {
                "id": competency_id,
                "label": value.get("label") or competency_id,
                "practice_count": practice,
                "positive_count": positive,
                "progress_pct": round((positive / practice) * 100) if practice else 0,
                "last_practiced_at": value.get("last_practiced_at"),
            }
        )
    rows.sort(key=lambda item: (-item["practice_count"], item["label"]))
    resources = current.get("resource_codes") if isinstance(current.get("resource_codes"), dict) else {}
    frequent_resources = sorted(
        ({"code": code, "count": int(count or 0)} for code, count in resources.items()),
        key=lambda item: (-item["count"], item["code"]),
    )[:10]
    return {
        "total_practices": int(current.get("total_sessions") or 0),
        "competencies": rows,
        "frequent_resources": frequent_resources,
        "updated_at": current.get("updated_at"),
        "privacy": current.get("privacy") or "No se han almacenado datos de clientes ni respuestas del auditor.",
    }


def delete_learning_progress(user_id: str) -> bool:
    with _LOCK:
        payload = _read()
        existed = user_id in payload
        payload.pop(user_id, None)
        _write(payload)
        return existed
