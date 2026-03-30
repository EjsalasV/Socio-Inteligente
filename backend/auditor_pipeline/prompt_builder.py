from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.repositories.file_repository import read_area_yaml, read_perfil

ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT_PATH = ROOT / "backend" / "auditor_pipeline" / "system_prompt.txt"

MODO_MAX_TOKENS = {
    "briefing": 800,
    "consulta_rapida": 300,
    "hallazgo": 600,
    "cierre": 500,
}


def load_system_prompt() -> str:
    try:
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    except Exception:
        return "Eres un auditor senior. Responde solo JSON valido."


def max_tokens_for_mode(modo: str) -> int:
    return int(MODO_MAX_TOKENS.get((modo or "").strip().lower(), 600))


def _safe_str(value: Any, default: str = "N/D") -> str:
    text = str(value or "").strip()
    return text if text else default


def format_client_context(
    perfil: dict[str, Any],
    area: dict[str, Any],
    signals_python: dict[str, Any],
) -> str:
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}
    riesgo_global = perfil.get("riesgo_global", {}) if isinstance(perfil.get("riesgo_global"), dict) else {}

    patterns = area.get("patrones_historicos")
    if isinstance(patterns, list) and patterns:
        patterns_block = "\n".join([f"  - {str(p)}" for p in patterns[:8]])
    else:
        patterns_block = "  - Sin patrones historicos registrados"

    findings = area.get("hallazgos_previos")
    if isinstance(findings, list) and findings:
        findings_block = "\n".join(
            [f"  - {str(f.get('año') or f.get('year') or 'N/D')}: {str(f.get('descripcion') or '')}" for f in findings[:8] if isinstance(f, dict)]
        )
    else:
        findings_block = "  - Sin hallazgos previos registrados"

    signals_block = "\n".join([f"  - {k}: {v}" for k, v in (signals_python or {}).items()]) if signals_python else "  - Sin senales python"

    mat = area.get("materialidad_area")
    if mat in {None, ""}:
        mat = (
            perfil.get("materialidad", {}).get("final", {}).get("materialidad_planeacion")
            if isinstance(perfil.get("materialidad"), dict)
            else None
        )

    return (
        "CLIENTE ACTIVO:\n"
        f"  Nombre: {_safe_str(cliente.get('nombre_legal') or cliente.get('nombre_corto'))}\n"
        f"  Sector: {_safe_str(cliente.get('sector'))}\n"
        f"  Marco: {_safe_str(encargo.get('marco_referencial'))}\n"
        f"  Ano fiscal: {_safe_str(encargo.get('anio_activo'))}\n"
        f"  Riesgo global: {_safe_str(riesgo_global.get('nivel'), 'medio')}\n\n"
        "AREA ACTIVA:\n"
        f"  Codigo: {_safe_str(area.get('codigo'))}\n"
        f"  Nombre: {_safe_str(area.get('nombre'))}\n"
        f"  Estado: {_safe_str(area.get('estado_area') or area.get('estado'), 'planificado')}\n"
        f"  Riesgo asignado: {_safe_str(area.get('riesgo'), 'medio')}\n"
        f"  Materialidad area: {_safe_str(mat)}\n"
        f"  Afirmaciones criticas: {', '.join([str(x) for x in area.get('afirmaciones_criticas', [])]) or 'N/D'}\n\n"
        "SENALES PYTHON:\n"
        f"{signals_block}\n\n"
        "PATRONES HISTORICOS:\n"
        f"{patterns_block}\n\n"
        "HALLAZGOS PREVIOS:\n"
        f"{findings_block}"
    )


def format_rag_chunks(chunks_rag: list[dict[str, Any]]) -> str:
    if not chunks_rag:
        return "NORMATIVA RAG: Sin chunks recuperados."
    blocks: list[str] = []
    for i, c in enumerate(chunks_rag[:8], start=1):
        ref = str(c.get("referencia") or c.get("source") or "N/D")
        txt = str(c.get("texto") or c.get("excerpt") or "").strip()
        score = c.get("score")
        blocks.append(f"[CHUNK {i}] {ref} (score: {score})\n{txt[:700]}")
    return "NORMATIVA RAG:\n" + "\n\n".join(blocks)


def instruction_for_mode(modo: str) -> str:
    m = (modo or "").strip().lower()
    mapping = {
        "briefing": "Genera analisis completo del area con max 5 procedimientos priorizados.",
        "consulta_rapida": "Responde directo, max 3 procedimientos y analisis corto.",
        "hallazgo": "Estructura condicion/criterio/causa/efecto/recomendacion.",
        "cierre": "Evalua cobertura de afirmaciones y pendientes de cierre.",
    }
    return mapping.get(m, "Responde segun contexto del caso.")


def build_user_prompt(
    *,
    modo: str,
    contexto_cliente: str,
    chunks_rag: str,
    consulta_adicional: str = "",
) -> str:
    parts = [
        "=== CONTEXTO DEL CASO ===",
        contexto_cliente,
        "",
        "=== NORMATIVA DISPONIBLE ===",
        chunks_rag,
        "",
        "=== INSTRUCCION ===",
        f"MODO: {modo}",
        instruction_for_mode(modo),
    ]
    if consulta_adicional.strip():
        parts.extend(["", "=== CONSULTA DEL AUDITOR ===", consulta_adicional.strip()])
    parts.extend(["", "Responde solo JSON valido, sin texto fuera del JSON."])
    return "\n".join(parts)


def load_context(cliente_id: str, area_code: str) -> tuple[dict[str, Any], dict[str, Any]]:
    perfil = read_perfil(cliente_id)
    area = read_area_yaml(cliente_id, area_code)
    if not area:
        area = {
            "codigo": area_code,
            "nombre": f"Area {area_code}",
            "riesgo": "medio",
            "afirmaciones_criticas": [],
        }
    return perfil, area

