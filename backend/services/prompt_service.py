from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROMPTS_ROOT = ROOT / "backend" / "prompts" / "v1"
PERSONA_PATH = ROOT / "backend" / "prompts" / "persona_auditor.md"


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _extract_meta(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines()[:12]:
        m = re.match(r"\s*#\s*([a-zA-Z0-9_]+)\s*:\s*(.+?)\s*$", line)
        if not m:
            continue
        out[m.group(1).strip().lower()] = m.group(2).strip()
    return out


def get_prompt_template(mode: str) -> tuple[str, dict[str, str]]:
    mapping = {
        "chat": "consulta_rapida.md",
        "metodologia": "briefing_area.md",
        "memo": "memo_ejecutivo.md",
        "hallazgo": "estructurador_hallazgo.md",
        "judgement_risk": "judgement_risk.md",
        "carta_control_interno": "carta_control_interno.md",
        "niif_notas": "niif_notas.md",
    }
    filename = mapping.get(mode, "consulta_rapida.md")
    path = PROMPTS_ROOT / filename
    raw = _safe_read(path)
    if not raw.strip():
        fallback = (
            "Eres Socio AI. Responde en espanol tecnico con criterio, accion, evidencia y citas.\n"
            "Consulta:\n{{query}}\n\nContexto:\n{{context}}"
        )
        return fallback, {
            "prompt_id": "fallback",
            "prompt_version": "v1",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "owner": "socio-ai-core",
        }
    meta = _extract_meta(raw)
    return raw, {
        "prompt_id": meta.get("prompt", filename.replace(".md", "")),
        "prompt_version": meta.get("version", "v1"),
        "updated_at": meta.get("updated_at", ""),
        "owner": meta.get("owner", "socio-ai-core"),
    }


def get_base_persona() -> tuple[str, dict[str, str]]:
    raw = _safe_read(PERSONA_PATH)
    if not raw.strip():
        fallback = (
            "Eres Socio AI, auditor senior. "
            "Responde con criterio tecnico, accion concreta y evidencia verificable."
        )
        return fallback, {
            "persona_id": "fallback",
            "persona_version": "v1",
            "persona_owner": "socio-ai-core",
            "persona_updated_at": datetime.now(timezone.utc).isoformat(),
        }
    meta = _extract_meta(raw)
    return raw, {
        "persona_id": meta.get("prompt", "persona_auditor"),
        "persona_version": meta.get("version", "v1"),
        "persona_owner": meta.get("owner", "socio-ai-core"),
        "persona_updated_at": meta.get("updated_at", ""),
    }


def render_prompt(mode: str, *, query: str, context: str) -> tuple[str, dict[str, str]]:
    template, meta = get_prompt_template(mode)
    persona, persona_meta = get_base_persona()
    rendered_task = template.replace("{{query}}", query.strip()).replace("{{context}}", context.strip())
    rendered = f"{persona.strip()}\n\n---\n\n{rendered_task.strip()}"
    meta = {**meta, **persona_meta}
    return rendered, meta


def validate_minimum_output(text: str, *, mode: str) -> tuple[bool, list[str]]:
    content = (text or "").strip().lower()
    if mode == "chat":
        # En chat priorizamos conversacion natural; no forzamos plantilla rigida.
        return (len(content) > 0), ([] if len(content) > 0 else ["respuesta_vacia"])
    rules: dict[str, list[str]] = {
        "metodologia": ["criterio", "accion", "evidencia"],
        "memo": ["riesgo", "materialidad", "recomend"],
        "hallazgo": ["condicion", "criterio", "causa", "efecto", "recomend"],
        "carta_control_interno": ["aspectos de mayor interés", "aspectos de control interno", "observación", "recomendación"],
        "niif_notas": ["informacion general", "base de preparacion", "juicios", "notas"],
    }
    required = rules.get(mode, ["criterio", "accion", "evidencia"])
    missing = [token for token in required if token not in content]
    return len(missing) == 0, missing
