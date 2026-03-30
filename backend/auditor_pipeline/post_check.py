from __future__ import annotations

import json
import re
from typing import Any

FLAG_FORMATO_INVALIDO = "FORMATO_INVALIDO"
FLAG_RIESGO_INCONSISTENTE = "RIESGO_INCONSISTENTE"
FLAG_CITA_NO_VERIFICADA = "CITA_NO_VERIFICADA"
FLAG_CITA_INVENTADA = "CITA_INVENTADA_SIN_CHUNK"
FLAG_MATERIALIDAD_IGNORADA = "MATERIALIDAD_NO_REFERENCIADA"
FLAG_CONFIDENCE_INFLADO = "CONFIDENCE_INFLADO"
FLAG_AFIRMACION_SIN_COBERTURA = "AFIRMACION_SIN_COBERTURA"


def parse_response_json(raw_text: str) -> tuple[dict[str, Any] | None, list[str]]:
    text = (raw_text or "").strip()
    text = re.sub(r"```json\s*|\s*```", "", text)
    try:
        return json.loads(text), []
    except Exception:
        pass

    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None, [FLAG_FORMATO_INVALIDO]
    try:
        return json.loads(m.group(0)), []
    except Exception as exc:
        return None, [f"{FLAG_FORMATO_INVALIDO}: {str(exc)[:80]}"]


def check_risk_consistency(response: dict[str, Any], area_yaml: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    risk_yaml = str(area_yaml.get("riesgo") or "").strip().lower()
    risk_llm = str(response.get("riesgo_nivel") or "").strip().lower()
    if risk_yaml and risk_llm and risk_yaml != risk_llm:
        flags.append(f"{FLAG_RIESGO_INCONSISTENTE}: yaml={risk_yaml}, llm={risk_llm}")
    return flags


def check_citations(response: dict[str, Any], chunks_rag: list[dict[str, Any]]) -> list[str]:
    flags: list[str] = []
    refs = [str(c.get("referencia") or c.get("source") or "").lower() for c in chunks_rag]
    for c in response.get("citas_normativas", []) or []:
        if not isinstance(c, dict):
            continue
        ref = str(c.get("referencia") or "").strip()
        respaldo = str(c.get("respaldo") or "").strip().lower()
        para = str(c.get("texto_parafraseado") or "").strip()
        if respaldo == "con_chunk":
            if not any(ref.lower() in r for r in refs):
                flags.append(f"{FLAG_CITA_NO_VERIFICADA}: {ref}")
        if respaldo == "sin_chunk" and para:
            flags.append(f"{FLAG_CITA_INVENTADA}: {ref}")
    return flags


def check_confidence(response: dict[str, Any], chunks_rag: list[dict[str, Any]]) -> list[str]:
    flags: list[str] = []
    conf = str(response.get("confidence") or "").strip().lower()
    if conf == "alto" and not chunks_rag:
        flags.append(f"{FLAG_CONFIDENCE_INFLADO}: confidence=alto sin chunks")
    return flags


def check_materiality(response: dict[str, Any], perfil_yaml: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    risk = str(response.get("riesgo_nivel") or "").strip().lower()
    if risk not in {"alto", "critico"}:
        return flags
    materialidad = (
        perfil_yaml.get("materialidad", {}).get("final", {}).get("materialidad_planeacion")
        if isinstance(perfil_yaml.get("materialidad"), dict)
        else None
    )
    mat_str = str(materialidad or "")
    procedures_text = " ".join([str(p) for p in response.get("procedimientos", [])]).lower()
    if not procedures_text:
        flags.append(f"{FLAG_MATERIALIDAD_IGNORADA}: sin procedimientos")
        return flags
    if mat_str and mat_str not in procedures_text and "materialidad" not in procedures_text and "$" not in procedures_text:
        flags.append(f"{FLAG_MATERIALIDAD_IGNORADA}: riesgo={risk}")
    return flags


def check_assertion_coverage(response: dict[str, Any], area_yaml: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    if str(response.get("modo") or "").strip().lower() != "cierre":
        return flags
    required = [str(x).strip().lower() for x in area_yaml.get("afirmaciones_criticas", []) if str(x).strip()]
    blob = json.dumps(response, ensure_ascii=False).lower()
    for a in required:
        if a and a not in blob:
            flags.append(f"{FLAG_AFIRMACION_SIN_COBERTURA}: {a}")
    return flags


def run_post_check(
    *,
    texto_llm: str,
    perfil_yaml: dict[str, Any],
    area_yaml: dict[str, Any],
    chunks_rag: list[dict[str, Any]],
) -> dict[str, Any]:
    parsed, flags = parse_response_json(texto_llm)
    result: dict[str, Any] = {
        "texto_raw": texto_llm,
        "respuesta": parsed,
        "flags": list(flags),
        "usable": parsed is not None,
        "requiere_revision": bool(flags),
    }
    if parsed is None:
        return result

    result["flags"].extend(check_risk_consistency(parsed, area_yaml))
    result["flags"].extend(check_citations(parsed, chunks_rag))
    result["flags"].extend(check_confidence(parsed, chunks_rag))
    result["flags"].extend(check_materiality(parsed, perfil_yaml))
    result["flags"].extend(check_assertion_coverage(parsed, area_yaml))

    llm_flags = parsed.get("flags_internos")
    if isinstance(llm_flags, list):
        for f in llm_flags:
            result["flags"].append(f"LLM_FLAG: {str(f)}")

    result["requiere_revision"] = len(result["flags"]) > 0
    return result
