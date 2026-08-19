from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from backend.repositories.file_repository import append_quality_trace


def _digest(value: Any) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def summarize_quality_controls(result: dict[str, Any]) -> dict[str, Any]:
    mode = str(result.get("mode_used") or "chat")
    withheld = "blocked" in mode

    if "output_blocked" in mode:
        normative = "blocked"
    elif result.get("normative_redaction_used"):
        normative = "redacted"
    elif result.get("normative_repair_used"):
        normative = "repaired"
    else:
        normative = "passed"

    if "grounding_blocked" in mode:
        grounding = "blocked"
    elif result.get("grounding_redaction_used"):
        grounding = "redacted"
    elif result.get("grounding_repair_used"):
        grounding = "repaired"
    else:
        grounding = "passed"

    return {
        "publication": "withheld" if withheld else "published",
        "normative": normative,
        "grounding": grounding,
        "sample_selection": "passed" if "seleccion_cuantitativa_sin_base" not in (result.get("quality_flags") or []) else "blocked",
        "quality_repair_used": bool(result.get("quality_repair_used")),
        "normative_redaction_used": bool(result.get("normative_redaction_used")),
        "grounding_redaction_used": bool(result.get("grounding_redaction_used")),
    }


def record_quality_trace(
    *,
    cliente_id: str,
    conversation_id: str,
    query: str,
    result: dict[str, Any],
    user_id: str,
) -> dict[str, Any]:
    controls = summarize_quality_controls(result)
    event = {
        "trace_id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cliente_id": cliente_id,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "query_sha256": _digest(query),
        "response_sha256": _digest(result.get("answer")),
        "provider": str(result.get("provider") or ""),
        "model": str(result.get("model") or ""),
        "mode_used": str(result.get("mode_used") or "chat"),
        "prompt_id": str((result.get("prompt_meta") or {}).get("prompt_id") or ""),
        "prompt_version": str((result.get("prompt_meta") or {}).get("prompt_version") or ""),
        "controls": controls,
        "quality_flags": [str(flag) for flag in (result.get("quality_flags") or [])],
        "sources": [str(source) for source in (result.get("context_sources") or [])],
    }
    append_quality_trace(cliente_id, event)
    return event
