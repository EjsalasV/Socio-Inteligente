from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from datetime import date
from typing import Any, Iterable
from urllib.parse import urlparse


INDEX_VERSION = "v6_professional_interpretation_library"


@dataclass(frozen=True)
class NormativeRequestDecision:
    action: str
    reason: str = ""

    @property
    def blocked(self) -> bool:
        return self.action.startswith("block_")


@dataclass(frozen=True)
class NormativeOutputValidation:
    allowed: bool
    issues: tuple[str, ...] = ()

CONTENT_TYPES = {
    "oficial",
    "resumen_verificado",
    "metodologia",
    "criterio_practico",
    "pendiente_revision",
    "retirado",
}
CITATION_CONTENT_TYPES = {"oficial", "resumen_verificado"}
REVIEW_STATES = {"verificado", "pendiente", "rechazado", "retirado"}

_CONTENT_TYPE_ALIASES = {
    "official": "oficial",
    "verified_summary": "resumen_verificado",
    "methodology": "metodologia",
    "practical_criterion": "criterio_practico",
    "pending_review": "pendiente_revision",
    "retired": "retirado",
}
_REVIEW_STATE_ALIASES = {
    "verified": "verificado",
    "pending": "pendiente",
    "rejected": "rechazado",
    "retired": "retirado",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _canonical(value: Any, aliases: dict[str, str]) -> str:
    normalized = _text(value).lower().replace(" ", "_")
    return aliases.get(normalized, normalized)


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _looks_like_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _default_content_type(relative_source: str) -> str:
    path = relative_source.lower().replace("\\", "/")
    if "/metodologia/" in path:
        return "metodologia"
    if "/criterios/" in path or "/criterio_practico/" in path:
        return "criterio_practico"
    return "pendiente_revision"


def apply_quality_gate(raw_metadata: dict[str, Any], relative_source: str) -> dict[str, Any]:
    """Normalize source quality and decide whether it may support a normative citation."""
    metadata = dict(raw_metadata or {})
    explicit_content_type = _canonical(metadata.get("tipo_contenido"), _CONTENT_TYPE_ALIASES)
    content_type = explicit_content_type or _default_content_type(relative_source)
    if content_type not in CONTENT_TYPES:
        content_type = "pendiente_revision"

    explicit_review_state = _canonical(metadata.get("estado_revision"), _REVIEW_STATE_ALIASES)
    review_state = explicit_review_state or "pendiente"
    if review_state not in REVIEW_STATES:
        review_state = "pendiente"

    aliases = {
        "autoridad": ("autoridad", "authority"),
        "version": ("version", "edicion", "edition"),
        "jurisdiccion": ("jurisdiccion", "jurisdiction"),
        "vigente_desde": ("vigente_desde", "effective_from"),
        "vigente_hasta": ("vigente_hasta", "effective_to"),
        "url_oficial": ("url_oficial", "official_url"),
        "localizador": ("localizador", "locator", "parrafos"),
        "licencia": ("licencia", "license", "derecho_uso"),
        "aplicacion_local": ("aplicacion_local", "local_application"),
        "revisado_por": ("revisado_por", "reviewed_by"),
        "rol_revisor": ("rol_revisor", "reviewer_role"),
        "fecha_revision": ("fecha_revision", "review_date"),
        "alcance_revision": ("alcance_revision", "review_scope"),
        "evidencia_revision": ("evidencia_revision", "review_evidence"),
        "modo_ingesta": ("modo_ingesta", "ingestion_mode"),
        "origen_contenido": ("origen_contenido", "content_origin"),
    }
    for target, candidates in aliases.items():
        value = next((_text(metadata.get(key)) for key in candidates if _text(metadata.get(key))), "")
        metadata[target] = value

    issues: list[str] = []
    if not explicit_content_type:
        issues.append("tipo_contenido_no_declarado")
    if not explicit_review_state:
        issues.append("estado_revision_no_declarado")
    for field in ("autoridad", "version", "jurisdiccion", "vigente_desde", "url_oficial", "localizador", "licencia"):
        if not metadata[field]:
            issues.append(f"falta_{field}")
    if "pendiente" in metadata["licencia"].lower():
        issues.append("licencia_pendiente")
    restricted_license = any(
        marker in metadata["licencia"].lower()
        for marker in ("pendiente", "permiso escrito", "licencia comercial", "copyright ifac", "copyright ifrs")
    )
    professional_interpretation = (
        metadata["modo_ingesta"].lower() == "interpretacion_profesional"
        and metadata["origen_contenido"].lower() == "interpretacion_profesional_interna"
    )
    if restricted_license and metadata["modo_ingesta"].lower() != "metadata_only" and not professional_interpretation:
        issues.append("ingesta_restringida_sin_metadata_only")
    normalized_source = relative_source.lower().replace("\\", "/")
    international_standard_source = any(
        folder in normalized_source
        for folder in ("/nias/", "/niif_completas/", "/niif_pymes/")
    )
    explicit_ai_permission = any(
        marker in metadata["licencia"].lower()
        for marker in ("permiso_otorgado_para_ia", "licensed_for_ai_product", "licencia_producto_otorgada")
    )
    if (
        international_standard_source
        and not explicit_ai_permission
        and metadata["modo_ingesta"].lower() != "metadata_only"
        and not professional_interpretation
    ):
        issues.append("ingesta_internacional_no_restringida")
    if metadata["jurisdiccion"].lower() in {"internacional", "international"}:
        if not metadata["aplicacion_local"]:
            issues.append("falta_aplicacion_local")
        elif "pendiente" in metadata["aplicacion_local"].lower():
            issues.append("aplicacion_local_pendiente")
    if metadata["version"].lower() in {"vigente", "actual", "n/a", "na", "nd", "n/d"}:
        issues.append("version_no_identificable")
    if metadata["vigente_desde"] and not _looks_like_iso_date(metadata["vigente_desde"]):
        issues.append("vigente_desde_invalido")
    if metadata["vigente_hasta"] and not _looks_like_iso_date(metadata["vigente_hasta"]):
        issues.append("vigente_hasta_invalido")
    if metadata["url_oficial"] and not _looks_like_url(metadata["url_oficial"]):
        issues.append("url_oficial_invalida")
    if review_state == "verificado":
        for field in ("revisado_por", "rol_revisor", "fecha_revision", "alcance_revision", "evidencia_revision"):
            if not metadata[field]:
                issues.append(f"falta_{field}")
        if metadata["fecha_revision"] and not _looks_like_iso_date(metadata["fecha_revision"]):
            issues.append("fecha_revision_invalida")

    citation_eligible = (
        content_type in CITATION_CONTENT_TYPES
        and review_state == "verificado"
        and not issues
    )
    metadata.update(
        {
            "tipo_contenido": content_type,
            "estado_revision": review_state,
            "citation_eligible": citation_eligible,
            "quality_issues": issues,
        }
    )
    return metadata


def is_citation_eligible(metadata: dict[str, Any] | None) -> bool:
    value = (metadata or {}).get("citation_eligible")
    if isinstance(value, bool):
        return value
    return _text(value).lower() in {"true", "1", "si", "yes"}


def _normalized_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _text(value).lower())
    return "".join(char for char in text if not unicodedata.combining(char))


_EXACT_SUPPORT_PATTERNS = (
    r"\b(cita|indica|dime|sustenta)\b.{0,45}\b(parrafo|articulo|seccion|caso|referencia|fuente)\b",
    r"\b(parrafo|articulo|localizador|referencia)\s+exact[oa]\b",
)
_AUTOMATIC_DECISION_PATTERNS = (
    r"\b(aplica|acepta|asigna|copia|registra)\b.{0,45}\bautomaticamente\b",
    r"\bdecide\s+definitivamente\b",
    r"\baprueba\b",
    r"\bconcluye\s+que\b",
    r"\bignora\b",
    r"\bcrea\s+porcentajes\b",
    r"\busa\b.{0,110}\b(sin evidencia|sin utilizar datos|misma lista generica)\b",
    r"\basigna\b.{0,60}\bsin pedir\b",
    r"\baplica\s+directamente\b.{0,60}\bsin preguntar\b",
    r"\baplica\b.{0,70}\b(propuesta|borrador)\b.{0,35}\bvigente\b",
    r"\baplica\b.{0,70}\btercera edicion\b.{0,70}\b(sin verificar|porque.{0,25}anticipada)\b",
    r"\bconfia\b.{0,70}\b(gerencia afirma|afirmacion verbal)\b",
    r"\btrata\b.{0,55}\bcomo fecha\b",
)
_NORMATIVE_TERMS = re.compile(
    r"\b(nia|niif|ifrs|isa|norma|normativa|reglamento|resolucion|parrafo|articulo)\b"
)
_SOURCE_REFERENCE = re.compile(r"\[FUENTE\s+(\d+)\]", flags=re.IGNORECASE)
_NORMATIVE_ATTRIBUTION_PATTERNS = (
    re.compile(
        r"\b(segun|de acuerdo con|conforme a)\b.{0,35}"
        r"\b(nia|niif|ifrs|isa|norma|normativa|resolucion|reglamento)\b"
    ),
    re.compile(
        r"\b(nia|niif|ifrs|isa|norma|normativa|resolucion|reglamento)\b.{0,80}"
        r"\b(establece|exige|requiere|permite|prohibe|dispone|define|indica|presume|obliga|obligatori[oa]|debe|senala)\b"
    ),
    re.compile(r"\b(parrafo|articulo)\s+(?:n(?:ro|o)?\.?\s*)?\d+[a-z]?(?:\.\d+)*\b"),
)
_LIMITATION_STATEMENT = re.compile(
    r"\b(no puedo|no es posible)\b.{0,60}\b(confirmar|atribuir|citar|verificar|validar)\b"
)
_UNSUPPORTED_SELECTION_PATTERNS = (
    re.compile(r"\b(ultimas|primeras)\s+\d+\s+(facturas|transacciones|partidas|clientes|saldos)\b"),
    re.compile(r"\b(muestra|seleccion)\s+(?:de\s+)?\d+\b"),
    re.compile(r"\b(revisa|selecciona|toma|elige)\b.{0,25}\b\d+\s+(facturas|transacciones|partidas|clientes|saldos)\b"),
)


def evaluate_normative_request(
    query: str,
    source_metadata: Iterable[dict[str, Any] | None] = (),
) -> NormativeRequestDecision:
    """Apply deterministic citation and professional-judgement boundaries."""
    metadata_rows = [row for row in source_metadata if isinstance(row, dict)]
    normative_rows = [
        row
        for row in metadata_rows
        if _text(row.get("tipo")).upper() != "CLIENTE"
        and any(_text(row.get(key)) for key in ("autoridad", "tipo_contenido", "jurisdiccion"))
    ]
    normalized_query = _normalized_text(query)
    normative_request = bool(normative_rows) or bool(_NORMATIVE_TERMS.search(normalized_query))
    if not normative_request:
        return NormativeRequestDecision("allow")

    has_verified_source = any(is_citation_eligible(row) for row in normative_rows)
    if not has_verified_source and any(re.search(pattern, normalized_query) for pattern in _EXACT_SUPPORT_PATTERNS):
        return NormativeRequestDecision(
            "block_unverified_citation",
            "La cita o el localizador solicitado no esta respaldado por una fuente verificada.",
        )
    if any(re.search(pattern, normalized_query) for pattern in _AUTOMATIC_DECISION_PATTERNS):
        return NormativeRequestDecision(
            "block_automatic_decision",
            "La solicitud delega una conclusion profesional o presupone hechos no documentados.",
        )
    if not has_verified_source:
        return NormativeRequestDecision(
            "orientation_only",
            "El contexto normativo recuperado aun no esta habilitado para citar.",
        )
    return NormativeRequestDecision("allow")


def validate_normative_output(
    answer: str,
    source_metadata: Iterable[dict[str, Any] | None] = (),
) -> NormativeOutputValidation:
    """Block unsupported normative attributions before an LLM answer is exposed."""
    metadata_rows = [row if isinstance(row, dict) else {} for row in source_metadata]
    verified_indexes = {
        index
        for index, metadata in enumerate(metadata_rows, start=1)
        if is_citation_eligible(metadata)
    }
    issues: list[str] = []
    normalized_answer = _normalized_text(answer)
    if any(pattern.search(normalized_answer) for pattern in _UNSUPPORTED_SELECTION_PATTERNS):
        issues.append("seleccion_cuantitativa_sin_base")

    for raw_index in _SOURCE_REFERENCE.findall(_text(answer)):
        index = int(raw_index)
        if index < 1 or index > len(metadata_rows):
            issues.append(f"fuente_inexistente:{index}")
        elif index not in verified_indexes:
            issues.append(f"fuente_no_verificada:{index}")

    units = re.split(r"(?<!\d)(?<=[.!?])\s+|[\r\n]+", _text(answer))
    for position, unit in enumerate(units, start=1):
        normalized_unit = _normalized_text(unit)
        if not normalized_unit or _LIMITATION_STATEMENT.search(normalized_unit):
            continue
        if not any(pattern.search(normalized_unit) for pattern in _NORMATIVE_ATTRIBUTION_PATTERNS):
            continue
        references = {int(value) for value in _SOURCE_REFERENCE.findall(unit)}
        if not references:
            issues.append(f"atribucion_sin_fuente:{position}")
        elif not references.issubset(verified_indexes):
            issues.append(f"atribucion_con_fuente_no_verificada:{position}")

    return NormativeOutputValidation(not issues, tuple(dict.fromkeys(issues)))


def redact_unsupported_normative_units(answer: str, issues: Iterable[str]) -> str:
    """Remove only units identified by the normative validator; never rewrite them."""
    issue_list = tuple(str(issue) for issue in issues)
    blocked_positions = {
        int(match.group(1))
        for issue in issue_list
        for match in [re.search(r"atribucion_(?:sin_fuente|con_fuente_no_verificada):(\d+)$", issue)]
        if match
    }
    blocked_source_indexes = {
        int(match.group(1))
        for issue in issue_list
        for match in [re.search(r"fuente_(?:inexistente|no_verificada):(\d+)$", issue)]
        if match
    }
    units = re.split(r"(?<!\d)(?<=[.!?])\s+|[\r\n]+", _text(answer))
    kept: list[str] = []
    for position, unit in enumerate(units, start=1):
        if position in blocked_positions:
            continue
        references = {int(value) for value in _SOURCE_REFERENCE.findall(unit)}
        if references.intersection(blocked_source_indexes):
            continue
        if unit.strip():
            kept.append(unit.strip())
    return "\n".join(kept).strip()


def active_markdown_files(knowledge_root: Path) -> list[Path]:
    if not knowledge_root.exists():
        return []
    return sorted(
        (
            path
            for path in knowledge_root.rglob("*.md")
            if "_backup" not in {part.lower() for part in path.parts}
        ),
        key=lambda path: path.as_posix().lower(),
    )


def source_signature(knowledge_root: Path, files: Iterable[Path] | None = None) -> str:
    digest = hashlib.sha256()
    selected = list(files) if files is not None else active_markdown_files(knowledge_root)
    for path in selected:
        try:
            relative = path.relative_to(knowledge_root).as_posix()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
        except (OSError, ValueError):
            continue
    return digest.hexdigest()


def backup_file_count(knowledge_root: Path) -> int:
    if not knowledge_root.exists():
        return 0
    return sum(
        1
        for path in knowledge_root.rglob("*.md")
        if "_backup" in {part.lower() for part in path.parts}
    )
