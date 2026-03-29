from __future__ import annotations

import json
import re
from typing import Any

from backend.schemas import RiskCriticalArea, RiskStrategyResponse, RiskStrategyTest
from backend.services.rag_chat_service import generate_judgement_response


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _extract_json_block(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _normalize_pct(control: int, substantive: int) -> tuple[int, int]:
    c = max(0, min(100, control))
    s = max(0, min(100, substantive))
    total = c + s
    if total == 100:
        return c, s
    if total <= 0:
        return 50, 50
    # Renormaliza para mantener suma 100
    c = int(round((c / total) * 100))
    s = 100 - c
    return c, s


def _priority(value: Any, fallback: str = "media") -> str:
    p = str(value or fallback).strip().lower()
    if p in {"alta", "media", "baja"}:
        return p
    return fallback


def _normalize_test(
    raw: dict[str, Any],
    *,
    default_type: str,
    default_area_id: str,
    default_area_name: str,
    index: int,
) -> RiskStrategyTest | None:
    title = str(raw.get("title") or "").strip()
    if not title:
        return None
    area_id = str(raw.get("area_id") or default_area_id).strip()
    area_name = str(raw.get("area_nombre") or default_area_name).strip()
    nia_ref = str(raw.get("nia_ref") or "NIA 500").strip()
    description = str(raw.get("description") or "").strip()
    test_type = str(raw.get("test_type") or default_type).strip().lower()
    if test_type not in {"control", "sustantiva"}:
        test_type = default_type
    return RiskStrategyTest(
        test_id=f"{'ctl' if test_type == 'control' else 'sub'}-{area_id}-{index}",
        test_type=test_type,  # type: ignore[arg-type]
        area_id=area_id,
        area_nombre=area_name,
        nia_ref=nia_ref,
        title=title,
        description=description,
        where_to_execute="workpapers",
        priority=_priority(raw.get("priority")),
    )


def _ai_query_for_risk(areas: list[RiskCriticalArea], deterministic: RiskStrategyResponse) -> str:
    facts = {
        "top_areas": [
            {
                "area_id": a.area_id,
                "area_nombre": a.area_nombre,
                "score": a.score,
                "nivel": a.nivel,
                "drivers": a.drivers[:3],
                "score_components": a.score_components,
            }
            for a in areas[:6]
        ],
        "baseline_strategy": {
            "approach": deterministic.approach,
            "control_pct": deterministic.control_pct,
            "substantive_pct": deterministic.substantive_pct,
            "rationale": deterministic.rationale,
        },
        "constraints": {
            "python_numbers_are_authoritative": True,
            "do_not_modify_scores": True,
            "max_tests_per_type": 6,
        },
    }
    return json.dumps(facts, ensure_ascii=False, indent=2)


def build_risk_judgement_with_ai(
    cliente_id: str,
    *,
    areas: list[RiskCriticalArea],
    deterministic: RiskStrategyResponse,
) -> RiskStrategyResponse:
    if not areas:
        return deterministic

    query = _ai_query_for_risk(areas, deterministic)
    rag = generate_judgement_response(cliente_id, query, mode="judgement_risk")
    raw_answer = str(rag.get("answer") or "").strip()
    parsed = _extract_json_block(raw_answer)
    if not parsed:
        return deterministic

    approach = str(parsed.get("approach") or deterministic.approach).strip() or deterministic.approach
    rationale = str(parsed.get("rationale") or deterministic.rationale).strip() or deterministic.rationale
    control_pct = _safe_int(parsed.get("control_pct"), deterministic.control_pct)
    substantive_pct = _safe_int(parsed.get("substantive_pct"), deterministic.substantive_pct)
    control_pct, substantive_pct = _normalize_pct(control_pct, substantive_pct)

    top_area = areas[0]
    control_tests_raw = parsed.get("control_tests")
    substantive_tests_raw = parsed.get("substantive_tests")
    control_tests: list[RiskStrategyTest] = []
    substantive_tests: list[RiskStrategyTest] = []

    if isinstance(control_tests_raw, list):
        for idx, row in enumerate(control_tests_raw, start=1):
            if not isinstance(row, dict):
                continue
            item = _normalize_test(
                row,
                default_type="control",
                default_area_id=top_area.area_id,
                default_area_name=top_area.area_nombre,
                index=idx,
            )
            if item:
                control_tests.append(item)

    if isinstance(substantive_tests_raw, list):
        for idx, row in enumerate(substantive_tests_raw, start=1):
            if not isinstance(row, dict):
                continue
            item = _normalize_test(
                row,
                default_type="sustantiva",
                default_area_id=top_area.area_id,
                default_area_name=top_area.area_nombre,
                index=idx,
            )
            if item:
                substantive_tests.append(item)

    if not control_tests:
        control_tests = deterministic.control_tests
    if not substantive_tests:
        substantive_tests = deterministic.substantive_tests

    return RiskStrategyResponse(
        approach=approach,
        control_pct=control_pct,
        substantive_pct=substantive_pct,
        rationale=rationale,
        control_tests=control_tests[:6],
        substantive_tests=substantive_tests[:6],
    )


def recommend_workpaper_tasks_from_strategy(
    strategy: RiskStrategyResponse,
    *,
    max_tasks: int = 8,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    ordered = list(strategy.control_tests) + list(strategy.substantive_tests)
    for test in ordered:
        key = f"{test.area_id}|{test.nia_ref.lower()}|{test.title.lower()}"
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "id": f"ai-{test.test_id}",
                "area_code": test.area_id,
                "area_name": test.area_nombre,
                "title": test.title,
                "nia_ref": test.nia_ref,
                "prioridad": _priority(test.priority),
                "required": False,
                "done": False,
                "evidence_note": (
                    f"[AI judgement] {test.description} | Tipo: {test.test_type} | "
                    f"Ejecucion sugerida en {test.where_to_execute}."
                ),
            }
        )
        if len(out) >= max_tasks:
            break
    return out
