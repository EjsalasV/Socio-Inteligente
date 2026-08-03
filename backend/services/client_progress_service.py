from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.repositories.file_repository import repo
from backend.services.context_document_service import list_documents


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def build_client_progress(cliente_id: str) -> dict[str, Any]:
    root = repo.cliente_dir(cliente_id)
    documents = list_documents(cliente_id)
    profile = _read_json(root / "entity_profile_draft.json")
    analysis = profile.get("analysis") if isinstance(profile.get("analysis"), dict) else {}
    has_tb = any((root / name).exists() for name in ("tb.xlsx", "tb.csv"))
    has_mayor = any((root / name).exists() for name in ("mayor.xlsx", "mayor.csv"))
    has_prior = any(
        item.get("document_type") == "prior_financial_statements" and item.get("status") in {"available", "available_with_warnings"}
        for item in documents
    )
    hypotheses = [
        item
        for key in ("changes", "risk_hypotheses", "estimate_hypotheses")
        for item in (analysis.get(key, []) if isinstance(analysis.get(key), list) else [])
        if isinstance(item, dict)
    ]
    pending_decisions = sum(
        1 for item in hypotheses
        if not isinstance(item.get("decision"), dict) or item.get("decision", {}).get("status") == "pending"
    )
    profile_confirmed = profile.get("status") == "confirmed"
    analysis_ready = analysis.get("status") == "ready"

    if not has_tb:
        next_action = {"key": "sources", "label": "Completar fuentes", "href": f"/onboarding/{cliente_id}"}
        stage = "Fuentes pendientes"
    elif not profile_confirmed:
        next_action = {"key": "profile", "label": "Revisar perfil", "href": f"/entity-profile/{cliente_id}"}
        stage = "Perfil por confirmar"
    elif not analysis_ready or pending_decisions:
        next_action = {"key": "hypotheses", "label": "Revisar hipótesis", "href": f"/entity-profile/{cliente_id}"}
        stage = "Contexto por validar"
    else:
        next_action = {"key": "analysis", "label": "Continuar análisis y mentor", "href": f"/trial-balance/{cliente_id}"}
        stage = "Listo para analizar"

    completed_steps = sum([bool(documents), has_tb, profile_confirmed, analysis_ready and pending_decisions == 0])
    return {
        "cliente_id": cliente_id,
        "stage": stage,
        "completion_pct": completed_steps * 25,
        "sources": {"count": len(documents), "has_prior_financials": has_prior, "has_tb": has_tb, "has_mayor": has_mayor},
        "profile": {"confirmed": profile_confirmed, "analysis_ready": analysis_ready, "pending_decisions": pending_decisions},
        "next_action": next_action,
    }
