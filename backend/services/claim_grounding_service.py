from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ClaimGroundingValidation:
    allowed: bool
    issues: tuple[str, ...] = ()


_FALSE_FLAG_PATTERNS = {
    "presion_resultados": re.compile(r"\bpresion\b.{0,35}\b(resultados|metas|desempeno)\b"),
    "partes_relacionadas": re.compile(r"\b(partes?|entidades?)\s+relacionadas?\b"),
    "ingresos_complejos": re.compile(
        r"\b(ingresos?|corte|reconocimiento)\b.{0,55}\b(inherentemente\s+)?complej[oa]s?\b"
    ),
    "multi_moneda": re.compile(r"\b(multimoneda|multi\s+moneda|moneda\s+extranjera)\b"),
    "inventarios": re.compile(r"\binventarios?\b"),
    "subsidiarias": re.compile(r"\b(subsidiarias?|filiales?)\b"),
    "litigios": re.compile(r"\b(litigios?|demandas?\s+judiciales?)\b"),
    "erp_implementado": re.compile(r"\b(erp|sistema\s+erp)\b"),
}

_CONDITIONAL_LANGUAGE = re.compile(
    r"\b(podria|podrian|hipotesis|candidato|posible|por confirmar|no (?:esta|estan) confirmad[oa]s?|"
    r"debe investigarse|deben investigarse|verificar si|si existiera|si existieran|si hubiera|"
    r"no hay evidencia|no se ha confirmado|no sabemos|antecedente|periodo anterior)\b"
)
_PRIOR_PERIOD_LANGUAGE = re.compile(r"\b(antecedente|periodo anterior|ejercicio anterior|historico|20\d{2})\b")

_UNSUPPORTED_PROCESS_PHRASES = {
    "manejo_efectivo": re.compile(r"\bmanejo\s+de\s+efectivo\b"),
    "facturacion_horas": re.compile(r"\bfactur(?:a|acion)\b.{0,25}\bhoras?\b"),
    "contratos_hitos": re.compile(r"\bcontratos?\b.{0,25}\bhitos?\b"),
    "cobranza_debil": re.compile(r"\bpolitica\s+de\s+cobranza\b.{0,20}\bdebil\b"),
}


def _normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").lower())
    return "".join(char for char in text if not unicodedata.combining(char))


def _chunk_metadata(chunk: Any) -> dict[str, Any]:
    if isinstance(chunk, dict):
        metadata = chunk.get("metadata")
    else:
        metadata = getattr(chunk, "metadata", None)
    return metadata if isinstance(metadata, dict) else {}


def _chunk_excerpt(chunk: Any) -> str:
    if isinstance(chunk, dict):
        return str(chunk.get("excerpt") or "")
    return str(getattr(chunk, "excerpt", "") or "")


def _currency_values(text: str) -> set[str]:
    values: set[str] = set()
    for match in re.findall(r"(?:us\$|\$)\s*([\d.,]+)", _normalize(text)):
        digits = re.sub(r"\D", "", match)
        if digits:
            values.add(digits)
    return values


def validate_client_grounding(
    answer: str,
    profile: dict[str, Any] | None,
    context_chunks: Iterable[Any] = (),
) -> ClaimGroundingValidation:
    """Reject client-specific assertions that contradict or outrun the expediente."""
    profile = profile if isinstance(profile, dict) else {}
    questionnaire = (
        profile.get("cuestionario_auditoria", {})
        if isinstance(profile.get("cuestionario_auditoria"), dict)
        else {}
    )
    chunks = list(context_chunks)
    evidence_text = _normalize("\n".join(_chunk_excerpt(chunk) for chunk in chunks))
    prior_values: set[str] = set()
    for chunk in chunks:
        metadata = _chunk_metadata(chunk)
        if str(metadata.get("temporal_status") or "").lower() == "antecedente_periodo_anterior":
            prior_values.update(_currency_values(_chunk_excerpt(chunk)))

    issues: list[str] = []
    units = re.split(r"(?<!\d)(?<=[.!?])\s+|[\r\n]+", str(answer or ""))
    for position, raw_unit in enumerate(units, start=1):
        unit = _normalize(raw_unit)
        if not unit:
            continue
        conditional = bool(_CONDITIONAL_LANGUAGE.search(unit))

        for flag, pattern in _FALSE_FLAG_PATTERNS.items():
            if questionnaire.get(flag) is False and pattern.search(unit) and not conditional:
                issues.append(f"contradice_perfil:{flag}:{position}")

        unit_values = _currency_values(unit)
        if unit_values.intersection(prior_values) and not _PRIOR_PERIOD_LANGUAGE.search(unit):
            issues.append(f"importe_previo_como_actual:{position}")

        for label, pattern in _UNSUPPORTED_PROCESS_PHRASES.items():
            match = pattern.search(unit)
            if match and match.group(0) not in evidence_text and not conditional:
                issues.append(f"proceso_no_documentado:{label}:{position}")

    unique_issues = tuple(dict.fromkeys(issues))
    return ClaimGroundingValidation(not unique_issues, unique_issues)


def redact_unsupported_claim_units(answer: str, issues: Iterable[str]) -> str:
    """Remove factual units rejected by validate_client_grounding without rewriting them."""
    blocked_positions = {
        int(match.group(1))
        for issue in issues
        for match in [re.search(r":(\d+)$", str(issue))]
        if match
    }
    units = re.split(r"(?<!\d)(?<=[.!?])\s+|[\r\n]+", str(answer or ""))
    return "\n".join(
        unit.strip()
        for position, unit in enumerate(units, start=1)
        if position not in blocked_positions and unit.strip()
    ).strip()
