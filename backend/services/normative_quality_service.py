from __future__ import annotations

import hashlib
from pathlib import Path
from datetime import date
from typing import Any, Iterable
from urllib.parse import urlparse


INDEX_VERSION = "v3_normative_quality_gate"

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
    }
    for target, candidates in aliases.items():
        value = next((_text(metadata.get(key)) for key in candidates if _text(metadata.get(key))), "")
        metadata[target] = value

    issues: list[str] = []
    if not explicit_content_type:
        issues.append("tipo_contenido_no_declarado")
    if not explicit_review_state:
        issues.append("estado_revision_no_declarado")
    for field in ("autoridad", "version", "jurisdiccion", "vigente_desde", "url_oficial", "localizador"):
        if not metadata[field]:
            issues.append(f"falta_{field}")
    if metadata["version"].lower() in {"vigente", "actual", "n/a", "na", "nd", "n/d"}:
        issues.append("version_no_identificable")
    if metadata["vigente_desde"] and not _looks_like_iso_date(metadata["vigente_desde"]):
        issues.append("vigente_desde_invalido")
    if metadata["vigente_hasta"] and not _looks_like_iso_date(metadata["vigente_hasta"]):
        issues.append("vigente_hasta_invalido")
    if metadata["url_oficial"] and not _looks_like_url(metadata["url_oficial"]):
        issues.append("url_oficial_invalida")

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
