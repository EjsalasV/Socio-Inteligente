from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.repositories.file_repository import list_area_codes, read_area_yaml, read_hallazgos, read_perfil, read_workpapers
from backend.repositories.metrics_repository import read_metric_events


def _to_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


def _coverage_for_area(area: dict[str, Any]) -> tuple[int, int, list[str], list[str]]:
    criticas = area.get("afirmaciones_criticas") if isinstance(area.get("afirmaciones_criticas"), list) else []
    coverage_rows = area.get("afirmaciones_coverage") if isinstance(area.get("afirmaciones_coverage"), list) else []

    covered_map: dict[str, tuple[bool, str]] = {}
    for row in coverage_rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("nombre") or "").strip().lower()
        if not name:
            continue
        is_cov = bool(row.get("covered", False))
        evidencia = str(row.get("evidencia") or "").strip()
        covered_map[name] = (is_cov and bool(evidencia), evidencia)

    total = 0
    covered = 0
    missing: list[str] = []
    weak_evidence: list[str] = []
    for a in criticas:
        name = str(a or "").strip().lower()
        if not name:
            continue
        total += 1
        ok, ev = covered_map.get(name, (False, ""))
        if ok:
            covered += 1
            if len(ev) < 20:
                weak_evidence.append(name)
        else:
            missing.append(name)
    return total, covered, missing, weak_evidence


def evaluate_pre_emit_check(cliente_id: str, *, fase: str = "informe", area_codigo: str | None = None, document_type: str | None = None) -> dict[str, Any]:
    area_codes = [area_codigo] if area_codigo else list_area_codes(cliente_id)
    perfil = read_perfil(cliente_id) or {}
    mat = _to_float(
        ((perfil.get("materialidad") or {}).get("final") or {}).get("materialidad_planeacion")
        if isinstance(perfil.get("materialidad"), dict)
        else 0
    )

    blocking: list[str] = []
    warnings: list[str] = []

    total_assertions = 0
    covered_assertions = 0
    missing_by_area: dict[str, list[str]] = {}

    for code in area_codes:
        area = read_area_yaml(cliente_id, str(code))
        riesgo = str(area.get("riesgo") or "medio").strip().lower()
        total, covered, missing, weak_evidence = _coverage_for_area(area)
        total_assertions += total
        covered_assertions += covered
        if missing:
            missing_by_area[str(code)] = missing
            if riesgo in {"alto", "critico"}:
                blocking.append(f"{code}: afirmaciones críticas sin cobertura ({', '.join(missing)})")
            else:
                warnings.append(f"{code}: cobertura parcial de afirmaciones ({', '.join(missing)})")
        for a in weak_evidence:
            warnings.append(f"{code}: evidencia secundaria débil en afirmación '{a}'")

        hallazgos = area.get("hallazgos_abiertos") if isinstance(area.get("hallazgos_abiertos"), list) else []
        for h in hallazgos:
            if not isinstance(h, dict):
                continue
            estado = str(h.get("estado") or "abierto").strip().lower()
            if estado not in {"abierto", "open", "pendiente"}:
                continue
            prioridad = str(h.get("prioridad") or "media").strip().lower()
            respuesta = str(h.get("respuesta_gerencia") or h.get("plan_accion") or "").strip()
            if prioridad in {"alta", "critica", "crítico"} and not respuesta:
                blocking.append(f"{code}: hallazgo crítico abierto sin plan/respuesta")
            elif not respuesta:
                warnings.append(f"{code}: hallazgo abierto sin plan de acción")

            monto_efecto = _to_float(h.get("monto_efecto") or h.get("impacto_monetario"))
            ref_materialidad = _to_float(h.get("materialidad_referencia"))
            if monto_efecto > 0 and mat > 0 and monto_efecto > mat and ref_materialidad <= 0:
                blocking.append(f"{code}: inconsistencia materialidad en hallazgo (efecto {monto_efecto:.2f} > materialidad {mat:.2f})")

        if riesgo in {"alto", "critico"}:
            conclusion = str(area.get("conclusion") or "").strip()
            if len(conclusion) < 80:
                blocking.append(f"{code}: falta conclusión técnica mínima para área de riesgo alto")

    hallazgos_md = str(read_hallazgos(cliente_id) or "").strip()
    if fase.lower().startswith("inform") and len(hallazgos_md) < 120:
        blocking.append("No existe conclusión consolidada suficiente en hallazgos.md")

    coverage_pct = (covered_assertions / total_assertions * 100.0) if total_assertions else 0.0

    score = 100
    score -= min(70, len(blocking) * 15)
    score -= min(30, len(warnings) * 5)
    if score < 0:
        score = 0

    status = "blocked" if blocking else "ok"
    return {
        "status": status,
        "fase": fase,
        "document_type": document_type or "",
        "blocking_reasons": sorted(set(blocking)),
        "warnings": sorted(set(warnings)),
        "score_calidad": int(score),
        "coverage": {
            "total_assertions": total_assertions,
            "covered_assertions": covered_assertions,
            "coverage_pct": round(coverage_pct, 2),
            "missing_by_area": missing_by_area,
        },
    }


def _parse_date(raw: str | None) -> datetime | None:
    text = str(raw or "").strip()
    if not text:
        return None
    for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"]:
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def build_quality_metrics(*, cliente_id: str | None = None, area_codigo: str | None = None, date_from: str | None = None, date_to: str | None = None) -> dict[str, Any]:
    events = read_metric_events()
    dt_from = _parse_date(date_from)
    dt_to = _parse_date(date_to)

    filtered: list[dict[str, Any]] = []
    for e in events:
        if not isinstance(e, dict):
            continue
        if cliente_id and str(e.get("cliente_id") or "") != str(cliente_id):
            continue
        if area_codigo and str(e.get("area_codigo") or "") != str(area_codigo):
            continue
        ts = _parse_date(str(e.get("timestamp") or ""))
        if dt_from and ts and ts < dt_from:
            continue
        if dt_to and ts and ts > dt_to:
            continue
        filtered.append(e)

    module_usage: dict[str, int] = {}
    manual_times: list[float] = []
    ai_times: list[float] = []
    savings_abs: list[float] = []

    chunks_valid_total = 0
    responses_total = 0
    staleness_warnings = 0
    llm_errors = 0

    blocking_reasons_count: dict[str, int] = {}

    for e in filtered:
        typ = str(e.get("event_type") or "")
        payload = e.get("payload") if isinstance(e.get("payload"), dict) else {}
        module_usage[typ] = module_usage.get(typ, 0) + 1

        if typ in {"briefing_generated", "hallazgo_generated"}:
            responses_total += 1
            if int(payload.get("chunks_count") or 0) > 0 and int(payload.get("normas_count") or 0) > 0:
                chunks_valid_total += 1
            if bool(payload.get("staleness_warning", False)):
                staleness_warnings += 1

        if typ == "briefing_time_logged":
            m = _to_float(payload.get("tiempo_manual_min"))
            a = _to_float(payload.get("tiempo_ai_min"))
            if m > 0:
                manual_times.append(m)
            if a >= 0:
                ai_times.append(a)
            if m > 0 and a >= 0:
                savings_abs.append(m - a)

        if typ == "llm_error":
            llm_errors += 1

        if typ == "quality_pre_emit":
            for reason in payload.get("blocking_reasons") or []:
                r = str(reason).strip()
                if not r:
                    continue
                blocking_reasons_count[r] = blocking_reasons_count.get(r, 0) + 1

    avg_manual = round(sum(manual_times) / len(manual_times), 2) if manual_times else 0.0
    avg_ai = round(sum(ai_times) / len(ai_times), 2) if ai_times else 0.0
    avg_ahorro = round(sum(savings_abs) / len(savings_abs), 2) if savings_abs else 0.0
    chunks_valid_rate = round((chunks_valid_total / responses_total * 100.0), 2) if responses_total else 0.0
    staleness_warning_rate = round((staleness_warnings / responses_total * 100.0), 2) if responses_total else 0.0
    llm_error_rate = round((llm_errors / responses_total * 100.0), 2) if responses_total else 0.0

    top_blocking = sorted(blocking_reasons_count.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "scope": {
            "cliente_id": cliente_id or "",
            "area_codigo": area_codigo or "",
            "date_from": date_from or "",
            "date_to": date_to or "",
            "events_count": len(filtered),
        },
        "operativo": {
            "uso_por_modulo": module_usage,
            "tiempo_manual_promedio_min": avg_manual,
            "tiempo_ai_promedio_min": avg_ai,
            "ahorro_promedio_min": avg_ahorro,
            "ahorro_promedio_pct": round((avg_ahorro / avg_manual * 100.0), 2) if avg_manual > 0 else 0.0,
        },
        "calidad_tecnica": {
            "respuestas_total": responses_total,
            "chunks_valid_rate_pct": chunks_valid_rate,
            "staleness_warning_rate_pct": staleness_warning_rate,
            "llm_error_rate_pct": llm_error_rate,
        },
        "top_blocking_reasons": [{"reason": r, "count": c} for r, c in top_blocking],
    }
