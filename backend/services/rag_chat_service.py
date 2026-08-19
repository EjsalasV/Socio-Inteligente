from __future__ import annotations

import os
import re
import json
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Any

import yaml
from backend.repositories.file_repository import list_documentos, read_hallazgos, read_perfil, read_workflow
from backend.services.area_procedures_service import get_procedures_by_area, list_areas_with_procedure_count
from backend.services.chat_response_cache_service import build_response_cache_key, get_cached_response, set_cached_response
from backend.services.claim_grounding_service import redact_unsupported_claim_units, validate_client_grounding
from backend.services.expert_criteria_service import get_expert_criteria_by_area, get_expert_criteria_by_sector
from backend.services.grupo_criteria_service import build_grupo_context_block, resolve_grupo
from backend.services.rag_cache_service import build_rag_cache_key, get_cached_chunks, set_cached_chunks
from backend.services.normativa_monitor_service import get_pending_normative_changes
from backend.services.normative_version_service import build_profile_version_context, should_include_version_context
from backend.services.normative_quality_service import (
    INDEX_VERSION,
    active_markdown_files,
    apply_quality_gate,
    backup_file_count,
    evaluate_normative_request,
    is_citation_eligible,
    redact_unsupported_normative_units,
    source_signature,
    validate_normative_output,
)
from backend.services.prompt_service import render_prompt, validate_minimum_output

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_ROOT = ROOT / "data" / "conocimiento_normativo"
CLIENTES_ROOT = ROOT / "data" / "clientes"
RAG_INDEX_PATH = ROOT / "data" / "rag" / "normativo_index.json"
METADATA_FILTER_KEYS = {
    "norma",
    "tipo",
    "activo",
    "marco",
    "areas_aplicables",
    "afirmaciones_relacionadas",
    "etapas",
    "temas",
    "ultima_actualizacion",
    "tipo_contenido",
    "estado_revision",
    "autoridad",
    "version",
    "vigente_desde",
    "vigente_hasta",
    "jurisdiccion",
    "url_oficial",
    "localizador",
    "licencia",
    "aplicacion_local",
}

# Web search fallback thresholds
# If the best local chunk scores below this, web search is triggered.
_WEB_SEARCH_SCORE_THRESHOLD = 2.5
# If fewer than this many chunks are retrieved, web search is also triggered.
_WEB_SEARCH_MIN_CHUNKS = 2


def _rag_index_signature() -> str:
    try:
        stat = RAG_INDEX_PATH.stat()
        return f"{int(stat.st_mtime)}:{int(stat.st_size)}"
    except Exception:
        return "missing"


@dataclass
class RetrievedChunk:
    source: str
    excerpt: str
    score: float
    metadata: dict[str, Any]


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^\w]+", text.lower(), flags=re.UNICODE) if len(t) > 2]


def _expand_query_tokens(query: str, tokens: set[str]) -> set[str]:
    q = str(query or "").lower()
    expanded = set(tokens)
    if "cuentas por cobrar" in q or "cxc" in q:
        expanded.update(
            {
                "cartera",
                "incobrables",
                "deterioro",
                "deudor",
                "deudores",
                "instrumentos",
                "financieros",
                "basicos",
                "amortizado",
            }
        )
    if "impuesto diferido" in q:
        expanded.update({"temporarias", "diferencias", "deducibles", "imponibles"})
    return expanded


def _semantic_similarity(query_tokens: set[str], chunk_tokens: set[str], *, query: str, chunk_text: str) -> float:
    if not query_tokens:
        return 0.0
    intersect = query_tokens.intersection(chunk_tokens)
    base = min(1.0, len(intersect) / max(len(query_tokens), 1))
    q = str(query or "").lower()
    c = str(chunk_text or "").lower()
    phrase_boost = 0.0
    if "cuentas por cobrar" in q and "cuentas por cobrar" in c:
        phrase_boost += 0.35
    if "valuacion" in q and ("deterioro" in c or "incobrable" in c):
        phrase_boost += 0.20
    return min(1.0, base + phrase_boost)


def _parse_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    text = markdown.strip()
    if not text.startswith("---"):
        return {}, markdown
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, markdown
    raw_meta = parts[1]
    body = parts[2].lstrip()
    try:
        loaded = yaml.safe_load(raw_meta) or {}
        if isinstance(loaded, dict):
            return loaded, body
    except Exception:
        pass
    return {}, markdown


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        out = []
        for item in value:
            txt = str(item).strip()
            if txt:
                out.append(txt)
        return out
    if isinstance(value, tuple):
        return _as_str_list(list(value))
    txt = str(value or "").strip()
    return [txt] if txt else []


def _as_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    txt = str(value).strip().lower()
    if txt in {"true", "1", "si", "sí", "yes", "y"}:
        return True
    if txt in {"false", "0", "no", "n"}:
        return False
    return default


def _default_metadata(relative_source: str, file_path: Path) -> dict[str, Any]:
    lower = relative_source.lower().replace("\\", "/")
    if "/nias/" in lower:
        norma = Path(relative_source).stem.upper()
        tipo = "NIA"
        marco = "ambos"
    elif "/niif_pymes/" in lower:
        norma = Path(relative_source).stem.upper()
        tipo = "NIIF_PYMES"
        marco = "niif_pymes"
    elif "/niif_completas/" in lower:
        norma = Path(relative_source).stem.upper()
        tipo = "NIIF_COMPLETA"
        marco = "niif_completas"
    else:
        norma = Path(relative_source).stem
        tipo = "OTRO"
        marco = "ambos"

    updated = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).date().isoformat()
    return {
        "norma": norma,
        "ultima_actualizacion": updated,
        "tipo": tipo,
        "activo": True,
        "marco": marco,
        "areas_aplicables": [],
        "afirmaciones_relacionadas": [],
        "etapas": [],
        "temas": [],
    }


def _normalize_metadata(relative_source: str, file_path: Path, raw_meta: dict[str, Any]) -> dict[str, Any]:
    meta = _default_metadata(relative_source, file_path)
    if not isinstance(raw_meta, dict):
        raw_meta = {}

    for key in [
        "norma", "tipo", "marco", "ultima_actualizacion", "tipo_contenido",
        "estado_revision", "autoridad", "version", "edicion", "vigente_desde",
        "vigente_hasta", "jurisdiccion", "url_oficial", "localizador", "licencia",
        "aplicacion_local", "modo_ingesta", "origen_contenido", "regla_uso",
        "autor_interpretacion", "revisado_por", "rol_revisor",
        "fecha_revision", "alcance_revision", "evidencia_revision",
    ]:
        value = str(raw_meta.get(key, "")).strip()
        if value:
            meta[key] = value

    meta["activo"] = _as_bool(raw_meta.get("activo"), default=True)
    for list_key in ["areas_aplicables", "afirmaciones_relacionadas", "etapas", "temas"]:
        meta[list_key] = _as_str_list(raw_meta.get(list_key))

    source_name = Path(relative_source).name
    meta["fuente"] = f"{source_name} | {meta.get('norma', source_name)}"
    return apply_quality_gate(meta, relative_source)


def _metadata_only_text(metadata: dict[str, Any]) -> str:
    topics = ", ".join(_as_str_list(metadata.get("temas"))) or "sin temas declarados"
    return (
        f"Referencia normativa: {metadata.get('norma', 'sin identificar')}. "
        f"Autoridad: {metadata.get('autoridad', 'no declarada')}. "
        f"Version: {metadata.get('version', 'no declarada')}. "
        f"Vigente desde: {metadata.get('vigente_desde', 'no declarado')}. "
        f"Aplicacion local: {metadata.get('aplicacion_local', 'no confirmada')}. "
        f"Temas: {topics}. URL oficial: {metadata.get('url_oficial', 'no declarada')}. "
        "El cuerpo del documento fue excluido del indice por restricciones de licencia."
    )


def _ingestion_text(metadata: dict[str, Any], body: str, relative_source: str = "") -> str:
    mode = str(metadata.get("modo_ingesta") or "").strip().lower()
    content_origin = str(metadata.get("origen_contenido") or "").strip().lower()
    license_text = str(metadata.get("licencia") or "").strip().lower()
    restricted_without_permission = any(
        marker in license_text
        for marker in ("pendiente", "permiso escrito", "licencia comercial", "copyright ifac", "copyright ifrs")
    )
    normalized_source = relative_source.lower().replace("\\", "/")
    international_standard_source = any(
        folder in normalized_source
        for folder in ("/nias/", "/niif_completas/", "/niif_pymes/")
    )
    explicit_ai_permission = any(
        marker in license_text
        for marker in ("permiso_otorgado_para_ia", "licensed_for_ai_product", "licencia_producto_otorgada")
    )
    professional_interpretation = (
        mode == "interpretacion_profesional"
        and content_origin == "interpretacion_profesional_interna"
    )
    if professional_interpretation:
        metadata["modo_ingesta"] = "interpretacion_profesional"
        return (
            "[INTERPRETACION PROFESIONAL INTERNA - ORIENTACION, NO CITA NORMATIVA]\n"
            "Recomendar siempre el cotejo con la norma oficial vigente antes de concluir.\n\n"
            f"{body}"
        )
    if mode == "metadata_only" or restricted_without_permission or (
        international_standard_source and not explicit_ai_permission
    ):
        metadata["modo_ingesta"] = "metadata_only"
        return _metadata_only_text(metadata)
    metadata["modo_ingesta"] = mode or "full_text"
    return body


def _load_markdown_sources() -> list[tuple[str, str, dict[str, Any], bool]]:
    out: list[tuple[str, str, dict[str, Any], bool]] = []
    if not KNOWLEDGE_ROOT.exists():
        return out
    for path in active_markdown_files(KNOWLEDGE_ROOT):
        try:
            raw_text = path.read_text(encoding="utf-8")
        except Exception:
            print(f"[WARN] No se pudo leer {path}")
            continue
        raw_meta, text = _parse_frontmatter(raw_text)
        text = text.strip()
        if not text:
            continue
        rel = str(path.relative_to(ROOT))
        metadata = _normalize_metadata(rel, path, raw_meta)
        text = _ingestion_text(metadata, text, rel)
        has_valid_frontmatter = bool(raw_meta)
        if not has_valid_frontmatter:
            print(f"[WARN] Frontmatter inválido o ausente: {rel}. Se indexará sin filtros avanzados.")
        out.append((rel, text, metadata, has_valid_frontmatter))
    return out


def _load_client_context(cliente_id: str) -> list[tuple[str, str, dict[str, Any]]]:
    out: list[tuple[str, str, dict[str, Any]]] = []
    perfil_path = CLIENTES_ROOT / cliente_id / "perfil.yaml"
    hallazgos_path = CLIENTES_ROOT / cliente_id / "hallazgos.md"
    docs_text_dir = CLIENTES_ROOT / cliente_id / "documentos_text"
    entity_profile_path = CLIENTES_ROOT / cliente_id / "entity_profile_draft.json"
    active_year = ""

    base_meta: dict[str, Any] = {
        "norma": "Contexto cliente",
        "ultima_actualizacion": "",
        "tipo": "CLIENTE",
        "activo": True,
        "marco": "ambos",
        "areas_aplicables": [],
        "afirmaciones_relacionadas": [],
        "etapas": [],
        "temas": [],
    }

    if perfil_path.exists():
        try:
            data = yaml.safe_load(perfil_path.read_text(encoding="utf-8")) or {}
            engagement = data.get("encargo", {}) if isinstance(data.get("encargo"), dict) else {}
            active_year = str(engagement.get("anio_activo") or "").strip()
            rel = str(perfil_path.relative_to(ROOT))
            meta = dict(base_meta)
            meta["ultima_actualizacion"] = datetime.fromtimestamp(perfil_path.stat().st_mtime, tz=timezone.utc).date().isoformat()
            meta["fuente"] = f"{perfil_path.name} | Contexto cliente"
            out.append((rel, yaml.safe_dump(data, allow_unicode=True, sort_keys=False), meta))
        except Exception:
            pass
    if hallazgos_path.exists():
        try:
            text = hallazgos_path.read_text(encoding="utf-8").strip()
            if text:
                rel = str(hallazgos_path.relative_to(ROOT))
                meta = dict(base_meta)
                meta["ultima_actualizacion"] = datetime.fromtimestamp(hallazgos_path.stat().st_mtime, tz=timezone.utc).date().isoformat()
                meta["fuente"] = f"{hallazgos_path.name} | Contexto cliente"
                out.append((rel, text, meta))
        except Exception:
            pass
    if entity_profile_path.exists():
        try:
            draft = json.loads(entity_profile_path.read_text(encoding="utf-8"))
            answers = draft.get("answers") if isinstance(draft, dict) and isinstance(draft.get("answers"), dict) else {}
            questions = draft.get("questions") if isinstance(draft, dict) and isinstance(draft.get("questions"), list) else []
            labels = {
                str(item.get("id") or ""): str(item.get("text") or "")
                for item in questions
                if isinstance(item, dict)
            }
            facts = draft.get("facts") if isinstance(draft, dict) and isinstance(draft.get("facts"), list) else []
            fact_lines = [
                f"- {item.get('label')}: {item.get('value')} (fuente: {item.get('source')})"
                for item in facts
                if isinstance(item, dict) and item.get("value") not in (None, "")
            ]
            answer_lines = [
                f"Pregunta: {labels.get(str(key), str(key))}\nRespuesta confirmada por el auditor: {value}"
                for key, value in answers.items()
                if str(value or "").strip()
            ]
            analysis = draft.get("analysis") if isinstance(draft, dict) and isinstance(draft.get("analysis"), dict) else {}
            analysis_lines: list[str] = []
            summary = analysis.get("entity_summary") if isinstance(analysis.get("entity_summary"), dict) else {}
            if summary:
                analysis_lines.append(
                    "Resumen asistido validable: actividad={activity}; ingresos={revenue}; regulacion={regulation}".format(
                        activity=str(summary.get("activity") or "N/D"),
                        revenue=str(summary.get("revenue_model") or "N/D"),
                        regulation=str(summary.get("regulatory_context") or "N/D"),
                    )
                )
            for key, label in (
                ("risk_hypotheses", "Hipotesis de riesgo"),
                ("estimate_hypotheses", "Estimacion por comprender"),
                ("prior_findings", "Hallazgo anterior por verificar"),
            ):
                rows = analysis.get(key) if isinstance(analysis.get(key), list) else []
                analysis_lines.extend(
                    f"- {label}: {str(row.get('title') or '').strip()}"
                    for row in rows
                    if isinstance(row, dict) and str(row.get("title") or "").strip()
                )
            text = (
                "HECHOS DEL PERFIL\n" + "\n".join(fact_lines)
                + "\n\nRESPUESTAS DEL AUDITOR\n" + "\n\n".join(answer_lines)
                + ("\n\nLECTURA ASISTIDA PENDIENTE DE VALIDACION\n" + "\n".join(analysis_lines) if analysis_lines else "")
            )
            meta = dict(base_meta)
            meta["norma"] = "Perfil confirmado por el auditor"
            meta["ultima_actualizacion"] = datetime.fromtimestamp(entity_profile_path.stat().st_mtime, tz=timezone.utc).date().isoformat()
            meta["fuente"] = "entity_profile_draft.json | Contexto confirmado"
            out.append((str(entity_profile_path.relative_to(ROOT)), text, meta))
        except Exception:
            pass
    if docs_text_dir.exists():
        seen_documents: set[str] = set()
        for path in sorted(docs_text_dir.glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8").strip()
            except Exception:
                continue
            if not text:
                continue
            header_fields = {
                key: (match.group(1).strip() if match else "")
                for key in ("document_type", "document_label", "document_period", "original_name")
                for match in [re.search(rf"(?mi)^{key}:\s*(.+)$", text)]
            }
            identity = "|".join(
                header_fields.get(key, "").lower()
                for key in ("document_type", "document_period", "original_name")
            )
            if identity.strip("|") and identity in seen_documents:
                continue
            if identity.strip("|"):
                seen_documents.add(identity)

            document_period = header_fields.get("document_period", "")
            temporal_status = (
                "periodo_actual"
                if active_year and document_period == active_year
                else "antecedente_periodo_anterior"
                if active_year and document_period and document_period != active_year
                else "periodo_no_confirmado"
            )
            temporal_marker = (
                f"[DOCUMENTO CLIENTE | PERIODO {document_period or 'NO CONFIRMADO'} | {temporal_status.upper()}]"
            )
            rel = str(path.relative_to(ROOT))
            meta = dict(base_meta)
            meta["norma"] = "Documentacion cliente"
            meta["ultima_actualizacion"] = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date().isoformat()
            meta["fuente"] = f"{path.name} | Documentacion cliente"
            meta["document_period"] = document_period
            meta["temporal_status"] = temporal_status
            meta["document_type"] = header_fields.get("document_type", "")
            out.append((rel, f"{temporal_marker}\n{text}", meta))
    return out


def _split_chunks(source: str, text: str, metadata: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    chunks: list[tuple[str, str, dict[str, Any]]] = []
    parts = re.split(r"\n\s*\n", text)
    for index, part in enumerate(parts, start=1):
        cleaned = part.strip()
        if len(cleaned) < 40:
            continue
        if str(metadata.get("tipo") or "").upper() == "CLIENTE" and metadata.get("temporal_status"):
            temporal_marker = (
                f"[DOCUMENTO CLIENTE | PERIODO {metadata.get('document_period') or 'NO CONFIRMADO'} | "
                f"{str(metadata.get('temporal_status')).upper()}]"
            )
            if temporal_marker not in cleaned:
                cleaned = f"{temporal_marker}\n{cleaned}"
        if str(metadata.get("modo_ingesta") or "").lower() == "interpretacion_profesional":
            marker = "[INTERPRETACION PROFESIONAL INTERNA - ORIENTACION, NO CITA NORMATIVA]"
            if marker not in cleaned:
                cleaned = f"{marker}\n{cleaned}"
        if len(cleaned) > 1100:
            cleaned = cleaned[:1100]
        chunk_metadata = dict(metadata)
        # File-level diagnostics live in the quality report, not in every chunk.
        chunk_metadata.pop("quality_issues", None)
        chunk_metadata["chunk_id"] = f"{source}#fragmento-{index}"
        chunks.append((source, cleaned, chunk_metadata))
    return chunks


def _build_normative_index(*, force: bool = False) -> dict[str, Any]:
    current_signature = source_signature(KNOWLEDGE_ROOT)
    if RAG_INDEX_PATH.exists() and not force:
        try:
            existing = json.loads(RAG_INDEX_PATH.read_text(encoding="utf-8"))
            if (
                existing.get("index_version") == INDEX_VERSION
                and existing.get("source_signature") == current_signature
            ):
                return existing
        except Exception:
            pass

    indexed_files = 0
    skipped_files = 0
    warnings = 0
    verified_files = 0
    citation_eligible_files = 0
    pending_files = 0
    quality_issues: dict[str, list[str]] = {}
    chunks: list[dict[str, Any]] = []

    for source, text, metadata, has_valid_frontmatter in _load_markdown_sources():
        if not has_valid_frontmatter:
            warnings += 1
        if not _as_bool(metadata.get("activo"), default=True):
            skipped_files += 1
            print(f"[SKIP] {source} (activo=false)")
            continue
        indexed_files += 1
        if str(metadata.get("estado_revision") or "") == "verificado":
            verified_files += 1
        else:
            pending_files += 1
        if is_citation_eligible(metadata):
            citation_eligible_files += 1
        issues = metadata.get("quality_issues")
        if isinstance(issues, list) and issues:
            quality_issues[source] = [str(issue) for issue in issues]
        print(f"[INDEX] {source}")
        for chunk_source, chunk, chunk_meta in _split_chunks(source, text, metadata):
            chunks.append(
                {
                    "source": chunk_source,
                    "excerpt": chunk,
                    "metadata": chunk_meta,
                    "tokens": _tokenize(chunk),
                }
            )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "index_version": INDEX_VERSION,
        "source_signature": current_signature,
        "indexed_files": indexed_files,
        "skipped_files": skipped_files,
        "warnings": warnings,
        "quality": {
            "verified_files": verified_files,
            "pending_files": pending_files,
            "citation_eligible_files": citation_eligible_files,
            "excluded_backup_files": backup_file_count(KNOWLEDGE_ROOT),
            "issues_by_source": quality_issues,
        },
        "chunks": chunks,
    }
    RAG_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = RAG_INDEX_PATH.with_suffix(f"{RAG_INDEX_PATH.suffix}.tmp")
    temporary_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary_path, RAG_INDEX_PATH)
    print(
        f"[OK] Índice normativo generado en {RAG_INDEX_PATH} | "
        f"files indexados={indexed_files}, saltados={skipped_files}, warnings={warnings}, chunks={len(chunks)}"
    )
    return payload


def rebuild_rag_index(*, force: bool = True) -> dict[str, Any]:
    return _build_normative_index(force=force)


def _load_normative_chunks() -> list[dict[str, Any]]:
    payload = _build_normative_index(force=False)
    chunks = payload.get("chunks")
    if isinstance(chunks, list):
        return [c for c in chunks if isinstance(c, dict)]
    return []


def _meta_contains(value: Any, expected: str) -> bool:
    exp = str(expected or "").strip().lower()
    if not exp:
        return False
    if isinstance(value, list):
        return any(str(v).strip().lower() == exp for v in value)
    return str(value or "").strip().lower() == exp


def _calculate_filter_match(
    metadata: dict[str, Any],
    *,
    marco: str | None = None,
    etapa: str | None = None,
    afirmacion: str | None = None,
    tipo: str | None = None,
    temas: str | list[str] | None = None,
) -> tuple[int, float]:
    strict_hits = 0
    soft_boost = 0.0
    marco_filter = str(marco or "").strip().lower()
    if marco_filter:
        chunk_marco = str(metadata.get("marco") or "").strip().lower()
        if marco_filter == "ambos":
            strict_hits += 1
            soft_boost += 0.5
        elif chunk_marco == marco_filter:
            strict_hits += 1
            soft_boost += 1.0
        elif chunk_marco == "ambos":
            soft_boost += 0.5
    if tipo and _meta_contains(metadata.get("tipo"), tipo):
        strict_hits += 1
    if etapa and _meta_contains(metadata.get("etapas"), etapa):
        strict_hits += 1
    if afirmacion and _meta_contains(metadata.get("afirmaciones_relacionadas"), afirmacion):
        strict_hits += 1
    if temas:
        temas_filters = [temas] if isinstance(temas, str) else list(temas)
        topic_hits = 0
        for item in temas_filters:
            if _meta_contains(metadata.get("temas"), str(item)):
                topic_hits += 1
        if topic_hits > 0:
            strict_hits += 1
            soft_boost += topic_hits * 0.4
    return strict_hits, soft_boost


def _needs_web_search(chunks: list[RetrievedChunk]) -> bool:
    """Return True when local RAG results are too thin to answer reliably."""
    if not chunks or len(chunks) < _WEB_SEARCH_MIN_CHUNKS:
        return True
    return max(c.score for c in chunks) < _WEB_SEARCH_SCORE_THRESHOLD


def _web_fallback_enabled() -> bool:
    return _as_bool(os.getenv("ENABLE_AUDIT_WEB_FALLBACK"), default=False)


def build_verified_citations(chunks: list[RetrievedChunk] | list[dict[str, Any]], *, limit: int = 8) -> list[dict[str, str]]:
    citations: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in chunks:
        if isinstance(item, RetrievedChunk):
            source, excerpt, meta = item.source, item.excerpt, item.metadata or {}
        elif isinstance(item, dict):
            source = str(item.get("source") or item.get("referencia") or "")
            excerpt = str(item.get("excerpt") or item.get("texto") or "")
            meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        else:
            continue
        if not is_citation_eligible(meta):
            continue
        locator = str(meta.get("localizador") or "")
        identity = f"{source}|{locator}"
        if not source or identity in seen:
            continue
        seen.add(identity)
        citations.append(
            {
                "source": source,
                "excerpt": excerpt[:220],
                "norma": str(meta.get("norma") or ""),
                "version": str(meta.get("version") or ""),
                "vigente_desde": str(meta.get("vigente_desde") or ""),
                "ultima_actualizacion": str(meta.get("ultima_actualizacion") or ""),
                "jurisdiccion": str(meta.get("jurisdiccion") or ""),
                "autoridad": str(meta.get("autoridad") or ""),
                "url_oficial": str(meta.get("url_oficial") or ""),
                "localizador": locator,
                "estado_revision": str(meta.get("estado_revision") or ""),
                "tipo_contenido": str(meta.get("tipo_contenido") or ""),
            }
        )
        if len(citations) >= limit:
            break
    return citations


def build_citations_used_in_answer(
    answer: str,
    chunks: list[RetrievedChunk] | list[dict[str, Any]],
) -> list[dict[str, str]]:
    referenced_indexes = {
        int(match)
        for match in re.findall(r"\[FUENTE\s+(\d+)\]", str(answer or ""), flags=re.IGNORECASE)
    }
    referenced_chunks = [
        chunk
        for index, chunk in enumerate(chunks[:6], start=1)
        if index in referenced_indexes
    ]
    return build_verified_citations(referenced_chunks)


def _citations_used_in_answer(answer: str, chunks: list[RetrievedChunk]) -> list[dict[str, str]]:
    return build_citations_used_in_answer(answer, chunks)


def _source_key(chunk: RetrievedChunk) -> str:
    return str(chunk.source or "").replace("/", "\\").lower()


def _diversify_chunks(candidates: list[RetrievedChunk], limit: int) -> list[RetrievedChunk]:
    """Prioritize distinct documents, then fill any remaining context slots."""
    if limit <= 0:
        return []

    selected: list[RetrievedChunk] = []
    seen_sources: set[str] = set()
    for chunk in candidates:
        source = _source_key(chunk)
        if source in seen_sources:
            continue
        selected.append(chunk)
        seen_sources.add(source)
        if len(selected) >= limit:
            return selected

    for chunk in candidates:
        if chunk in selected:
            continue
        selected.append(chunk)
        if len(selected) >= limit:
            break
    return selected


def _pilot_source_patterns(cliente_id: str, query: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", str(query or "").lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    has_income = any(term in normalized for term in ("ingreso", "venta", "facturacion"))
    has_receivables = any(term in normalized for term in ("cuentas por cobrar", "cxc", "cartera", "deudor"))
    if not has_income and not has_receivables:
        return []

    framework = ""
    try:
        profile = read_perfil(cliente_id) or {}
        engagement = profile.get("encargo", {}) if isinstance(profile.get("encargo"), dict) else {}
        framework = str(
            engagement.get("marco_referencial")
            or engagement.get("marco_informacion_financiera")
            or profile.get("marco_referencial")
            or ""
        ).lower()
    except Exception:
        framework = ""
    is_sme = "pyme" in framework

    patterns: list[str] = []
    if has_income:
        patterns.extend(("nia_240.md", "nia_315.md", "seccion_23.md" if is_sme else "niif_15.md"))
    if has_receivables:
        if "nia_315.md" not in patterns:
            patterns.append("nia_315.md")
        patterns.append("seccion_11.md" if is_sme else "niif_9.md")
    return patterns


def _select_pilot_coverage(
    candidates: list[RetrievedChunk],
    *,
    cliente_id: str,
    query: str,
    limit: int,
) -> list[RetrievedChunk]:
    selected: list[RetrievedChunk] = []
    for pattern in _pilot_source_patterns(cliente_id, query):
        match = next(
            (chunk for chunk in candidates if pattern in _source_key(chunk) and chunk not in selected),
            None,
        )
        if match is not None:
            selected.append(match)
        if len(selected) >= limit:
            break
    return selected


def _retrieve_chunks(
    cliente_id: str,
    query: str,
    *,
    top_k: int = 5,
    marco: str | None = None,
    etapa: str | None = None,
    afirmacion: str | None = None,
    tipo: str | None = None,
    temas: str | list[str] | None = None,
) -> list[RetrievedChunk]:
    query_tokens = set(_tokenize(query))
    query_tokens = _expand_query_tokens(query, query_tokens)
    if not query_tokens:
        return []

    normative_chunks = _load_normative_chunks()
    raw_docs = _load_client_context(cliente_id)
    candidates: list[RetrievedChunk] = []
    required_filter_count = len([x for x in [marco, etapa, afirmacion, tipo, temas] if x])

    for item in normative_chunks:
        source = str(item.get("source") or "")
        excerpt = str(item.get("excerpt") or "")
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        tokens_raw = item.get("tokens")
        tokens = set(tokens_raw) if isinstance(tokens_raw, list) else set(_tokenize(excerpt))
        semantic_similarity = _semantic_similarity(query_tokens, tokens, query=query, chunk_text=excerpt)
        if semantic_similarity <= 0:
            continue
        strict_hits, soft_boost = _calculate_filter_match(
            metadata,
            marco=marco,
            etapa=etapa,
            afirmacion=afirmacion,
            tipo=tipo,
            temas=temas,
        )
        metadata_match_ratio = 0.0
        if required_filter_count > 0:
            metadata_match_ratio = min(1.0, (strict_hits + soft_boost) / required_filter_count)
        # Regla pedida: score final = (similitud_semantica * 10) + (match_metadatos * 5)
        weighted_score = (semantic_similarity * 10.0) + (metadata_match_ratio * 5.0)
        candidates.append(RetrievedChunk(source=source, excerpt=excerpt, score=weighted_score, metadata=metadata))

    # Contexto de cliente se mantiene como complemento (sin filtros normativos duros).
    for source, text, metadata in raw_docs:
        for chunk_source, chunk, chunk_meta in _split_chunks(source, text, metadata):
            tokens = set(_tokenize(chunk))
            semantic_similarity = _semantic_similarity(query_tokens, tokens, query=query, chunk_text=chunk)
            if semantic_similarity <= 0:
                continue
            candidates.append(
                RetrievedChunk(source=chunk_source, excerpt=chunk, score=semantic_similarity * 10.0, metadata=chunk_meta)
            )

    candidates.sort(key=lambda x: x.score, reverse=True)
    if required_filter_count <= 0:
        # En preguntas aplicadas a un cliente, su perfil y evidencia deben
        # ocupar parte del contexto. De otro modo la biblioteca normativa
        # desplaza los hechos confirmados y el modelo rellena vacios con
        # generalizaciones sectoriales.
        client_candidates = [c for c in candidates if str((c.metadata or {}).get("tipo") or "").upper() == "CLIENTE"]
        client_slots = min(2, max(1, top_k // 4))
        reserved = _diversify_chunks(client_candidates, min(client_slots, top_k))
        normative_candidates = [
            c
            for c in candidates
            if str((c.metadata or {}).get("tipo") or "").upper() != "CLIENTE"
        ]
        normative_slots = max(0, top_k - len(reserved))
        pilot_coverage = _select_pilot_coverage(
            normative_candidates,
            cliente_id=cliente_id,
            query=query,
            limit=normative_slots,
        )
        remaining = [c for c in normative_candidates if c not in pilot_coverage]
        selected_normative = _diversify_chunks(pilot_coverage + remaining, normative_slots)
        mixed = reserved + selected_normative
        return mixed[:top_k]

    strict_candidates = [
        c
        for c in candidates
        if _calculate_filter_match(
            c.metadata,
            marco=marco,
            etapa=etapa,
            afirmacion=afirmacion,
            tipo=tipo,
            temas=temas,
        )[0]
        >= max(1, required_filter_count - 1)
    ]
    if len(strict_candidates) >= max(2, top_k // 2):
        return strict_candidates[:top_k]

    partial_candidates = [
        c
        for c in candidates
        if _calculate_filter_match(
            c.metadata,
            marco=marco,
            etapa=etapa,
            afirmacion=afirmacion,
            tipo=tipo,
            temas=temas,
        )[0]
        > 0
    ]
    mixed = partial_candidates + [c for c in candidates if c not in partial_candidates]
    return mixed[:top_k]


def retrieve_context_chunks(
    cliente_id: str,
    query: str,
    *,
    top_k: int = 6,
    marco: str | None = None,
    etapa: str | None = None,
    afirmacion: str | None = None,
    tipo: str | None = None,
    temas: str | list[str] | None = None,
) -> list[dict[str, Any]]:
    cache_key = build_rag_cache_key(
        cliente_id=cliente_id,
        query=query,
        top_k=top_k,
        marco=marco,
        etapa=etapa,
        afirmacion=afirmacion,
        tipo=tipo,
        temas=temas,
        index_signature=_rag_index_signature(),
    )
    cached = get_cached_chunks(cache_key)
    if isinstance(cached, list):
        return cached

    chunks = _retrieve_chunks(
        cliente_id,
        query,
        top_k=top_k,
        marco=marco,
        etapa=etapa,
        afirmacion=afirmacion,
        tipo=tipo,
        temas=temas,
    )
    out: list[dict[str, Any]] = []
    for c in chunks:
        out.append(
            {
                "source": c.source,
                "excerpt": c.excerpt,
                "score": c.score,
                "metadata": dict(c.metadata or {}),
            }
        )
    set_cached_chunks(cache_key, out)
    return out


def _is_greeting(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    # Si la frase ya contiene intencion de analisis, no tratar como saludo.
    if _is_risk_question(q) or _is_data_inventory_question(q) or _is_provider_question(q):
        return False
    greetings = {
        "hola",
        "buenas",
        "buen dia",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "hello",
        "hi",
        "hey",
    }
    if q in greetings:
        return True
    cleaned = re.sub(r"[^a-zA-Z0-9\s]+", " ", q)
    tokens = [t for t in cleaned.split() if t]
    if len(tokens) <= 2 and " ".join(tokens) in greetings:
        return True
    return False


def _is_provider_question(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    hints = ["deepseek", "deepsekk", "openai", "modelo", "model", "ia eres", "que modelo", "provider"]
    return any(h in q for h in hints)


def _resolved_provider() -> tuple[str, str]:
    explicit = (os.getenv("AI_PROVIDER") or "").strip().lower()
    deepseek_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()

    def _is_placeholder(key: str) -> bool:
        normalized = str(key or "").strip().lower()
        if not normalized:
            return True
        placeholders = {
            "sk-your_key_here",
            "your_key_here",
            "change_me",
            "your-openai-key",
            "your-deepseek-key",
        }
        return normalized in placeholders or "your_key" in normalized or "your-key" in normalized

    if _is_placeholder(deepseek_key):
        deepseek_key = ""
    if _is_placeholder(openai_key):
        openai_key = ""

    if explicit == "deepseek" and deepseek_key:
        return "deepseek", deepseek_key
    if explicit == "openai" and openai_key:
        return "openai", openai_key

    if deepseek_key:
        return "deepseek", deepseek_key
    if openai_key:
        return "openai", openai_key

    return ("deepseek", "") if explicit == "deepseek" else ("openai", "")


def _current_provider_label() -> str:
    provider, key = _resolved_provider()
    if not key:
        return "No configurado (define DEEPSEEK_API_KEY u OPENAI_API_KEY)"
    if provider == "deepseek":
        model = (os.getenv("DEEPSEEK_CHAT_MODEL") or "deepseek-chat").strip() or "deepseek-chat"
        return f"DeepSeek ({model})"
    model = (os.getenv("OPENAI_CHAT_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"
    return f"OpenAI ({model})"


def _query_normalized(text: str) -> str:
    value = unicodedata.normalize("NFD", str(text or "").strip().lower())
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")


def _strip_repair_preamble(text: str) -> str:
    value = str(text or "").strip()
    return re.sub(
        r"^(?:claro[,.:]?\s*)?(?:aquí|aqui)\s+tienes\s+(?:la\s+)?respuesta\s+reescrita\s*:\s*",
        "",
        value,
        count=1,
        flags=re.IGNORECASE,
    ).strip()


def _is_client_attention_question(query: str) -> bool:
    value = _query_normalized(query)
    return "cliente" in value and (
        "merece" in value
        or any(token in value for token in ("requiere atencion", "enfocar", "priorizar"))
    )


def _is_criterion_challenge(query: str) -> bool:
    value = _query_normalized(query)
    return any(token in value for token in ("desafia", "desafiar", "mi criterio", "cuestiona mi"))


def _detect_area_from_query(query: str) -> dict[str, str] | None:
    q_norm = _query_normalized(query)
    if not q_norm:
        return None

    manual_aliases = {
        "cxc": "130.1",
        "cuentas por cobrar": "130.1",
        "efectivo": "140",
        "bancos": "140",
        "inventarios": "110",
        "cuentas por pagar": "425",
        "patrimonio": "200",
        "ingresos": "1500",
    }
    for alias, area_code in manual_aliases.items():
        if alias in q_norm:
            return {"area_codigo": area_code, "area_nombre": ""}

    areas = list_areas_with_procedure_count()
    for area in areas:
        code = str(area.get("area_codigo") or "").strip()
        name = _query_normalized(str(area.get("area_nombre") or ""))
        if not code:
            continue
        if re.search(rf"(?<!\d){re.escape(code)}(?!\d)", q_norm):
            return {"area_codigo": code, "area_nombre": str(area.get("area_nombre") or "")}
        if name and len(name) >= 6 and name in q_norm:
            return {"area_codigo": code, "area_nombre": str(area.get("area_nombre") or "")}
    return None


def _build_area_procedures_block(area_payload: dict[str, Any]) -> str:
    area_code = str(area_payload.get("area_codigo") or "").strip()
    area_name = str(area_payload.get("area_nombre") or "").strip() or f"Area {area_code}"
    procedures = area_payload.get("procedimientos") if isinstance(area_payload.get("procedimientos"), list) else []
    risks = area_payload.get("riesgos_tipicos") if isinstance(area_payload.get("riesgos_tipicos"), list) else []
    tax_alerts = (
        area_payload.get("alertas_tributarias")
        if isinstance(area_payload.get("alertas_tributarias"), list)
        else []
    )

    lines: list[str] = [f"Area: {area_code} - {area_name}"]

    if procedures:
        lines.append("Procedimientos clave:")
        for proc in procedures[:12]:
            if not isinstance(proc, dict):
                continue
            obligation = "obligatorio" if bool(proc.get("obligatorio")) else "opcional"
            lines.append(
                f"- [{str(proc.get('id') or '').strip()}] {str(proc.get('descripcion') or '').strip()} "
                f"(tipo={str(proc.get('tipo') or '').strip()}, afirmacion={str(proc.get('afirmacion') or '').strip()}, "
                f"{obligation}, ref={str(proc.get('nia_ref') or 'NIA 500').strip()})"
            )

    if risks:
        lines.append("Riesgos tipicos por area:")
        for risk in risks[:10]:
            if not isinstance(risk, dict):
                continue
            lines.append(
                f"- [{str(risk.get('id') or '').strip()}] {str(risk.get('descripcion') or '').strip()} "
                f"(nivel={str(risk.get('nivel') or '').strip()}, afirmacion={str(risk.get('afirmacion') or '').strip()})"
            )

    if tax_alerts:
        lines.append("Alertas tributarias relacionadas:")
        for alert in tax_alerts[:10]:
            if not isinstance(alert, dict):
                continue
            lines.append(
                f"- [{str(alert.get('id') or '').strip()}] {str(alert.get('descripcion') or '').strip()} "
                f"(nivel={str(alert.get('nivel') or '').strip()}, norma={str(alert.get('norma') or '').strip()})"
            )

    return "\n".join(lines).strip()


def _enrich_context_with_area_procedures(area_codigo: str, context: str) -> str:
    payload = get_procedures_by_area(area_codigo)
    block = _build_area_procedures_block(payload)
    if not block:
        return context
    base = str(context or "").strip()
    if not base:
        return f"[PROCEDIMIENTOS POR ÁREA]\n{block}"
    return f"{base}\n\n[PROCEDIMIENTOS POR ÁREA]\n{block}"


def _enrich_context_with_expert_criteria(
    area_codigo: str, sector: str, context: str, query: str = ""
) -> tuple[str, bool]:
    base = str(context or "").strip()
    used = False
    blocks: list[str] = []

    if str(area_codigo or "").strip():
        by_area = get_expert_criteria_by_area(area_codigo)
        area_content = str(by_area.get("content") or "").strip()
        if area_content:
            if bool(by_area.get("found", False)):
                used = True
            blocks.append(
                "[CRITERIO EXPERTO - AREA]\n"
                f"Fuente: {str(by_area.get('source_path') or 'template')}\n"
                f"{area_content}"
            )

    if str(sector or "").strip():
        by_sector = get_expert_criteria_by_sector(sector)
        sector_content = str(by_sector.get("content") or "").strip()
        if sector_content:
            if bool(by_sector.get("found", False)):
                used = True
            blocks.append(
                "[CRITERIO EXPERTO - SECTOR]\n"
                f"Fuente: {str(by_sector.get('source_path') or 'template')}\n"
                f"{sector_content}"
            )

    # Criterio por grupo del balance (normas + matriz + vínculos cruzados).
    # Se resuelve desde el código de área o desde el texto de la pregunta.
    grupo = resolve_grupo(area_codigo=area_codigo, area_nombre=query)
    if grupo:
        grupo_block = build_grupo_context_block(grupo, compact=True)
        if grupo_block:
            used = True
            blocks.append(f"[CRITERIO EXPERTO - GRUPO DEL BALANCE]\n{grupo_block}")

    if not blocks:
        return base, used
    merged = "\n\n".join(blocks)
    if not base:
        return merged, used
    return f"{base}\n\n{merged}", used


def _procedural_fallback_hint(query: str) -> str:
    q = _query_normalized(query)
    if "efectivo" in q or "banco" in q:
        return (
            "Pruebas sugeridas para efectivo:\n"
            "1) Conciliar bancos al corte y recálculo de partidas en tránsito.\n"
            "2) Confirmaciones bancarias directas para cuentas principales.\n"
            "3) Prueba de corte: últimos y primeros 5 movimientos alrededor del cierre.\n"
            "4) Revisar restricciones, gravámenes y cuentas no registradas."
        )
    if "cobrar" in q or "cxc" in q:
        return (
            "Pruebas sugeridas para cuentas por cobrar:\n"
            "1) Confirmación externa positiva sobre saldos materiales.\n"
            "2) Recobros posteriores para validar existencia y valuación.\n"
            "3) Prueba de deterioro por antigüedad y análisis individual.\n"
            "4) Corte de ventas y notas de crédito de cierre."
        )
    if "ingreso" in q or "venta" in q:
        return (
            "Pruebas sugeridas para ingresos:\n"
            "1) Corte de ingresos cerca del cierre con soporte documental.\n"
            "2) Revisión de devoluciones y notas de crédito posteriores.\n"
            "3) Prueba de ocurrencia con muestra dirigida a mayor riesgo.\n"
            "4) Analíticos por tendencia, margen y cliente significativo."
        )
    return ""


def _is_data_inventory_question(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    hints = [
        "que datos tienes",
        "que informacion tienes",
        "que sabes",
        "que info tienes",
        "informacion tienes",
        "datos tienes",
        "what data",
        "what info",
        "what do you know",
    ]
    if any(h in q for h in hints):
        return True
    return ("informa" in q or "dato" in q) and ("tienes" in q or "sabes" in q)


def _is_risk_question(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    risk_hints = [
        "riesgo",
        "riesgos",
        "exposicion",
        "area critica",
        "top area",
        "que riesgo tiene",
        "nivel de riesgo",
    ]
    return any(h in q for h in risk_hints)


def _is_pilot_area_guidance_question(query: str) -> bool:
    q = _query_normalized(query)
    pilot_area = any(term in q for term in ("ingreso", "venta", "cuentas por cobrar", "cxc", "cartera"))
    guidance = any(
        term in q
        for term in ("riesgo", "aseveracion", "informacion", "evidencia", "documentar", "procedimiento")
    )
    return pilot_area and guidance


def _is_risk_why_question(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    why_hints = ["porque", "por que", "por qué", "why", "motivo", "razon", "razón"]
    return _is_risk_question(q) and any(h in q for h in why_hints)


def _is_next_steps_question(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    hints = [
        "que hacemos primero",
        "que sigue",
        "siguiente paso",
        "por donde empiezo",
        "dame un plan",
        "como arrancamos",
        "que hago primero",
    ]
    return any(h in q for h in hints)


def _is_payroll_question(query: str) -> bool:
    q = _query_normalized(query)
    if not q:
        return False
    hints = [
        "nomina",
        "rol de pagos",
        "rol pagos",
        "sueldos",
        "salarios",
        "beneficios sociales",
        "iess",
    ]
    return any(h in q for h in hints)


def _payroll_tests_answer(cliente_id: str) -> dict[str, Any]:
    perfil = read_perfil(cliente_id) or {}
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    cliente_nombre = str(cliente.get("nombre_legal") or cliente_id)
    answer = (
        f"Para `{cliente_nombre}`, estas son **pruebas clave de nomina** (priorizadas):\n\n"
        "1. **Recalculo de rol de pagos (muestra):** valida sueldo base, horas extra, decimos, provisiones y descuentos.\n"
        "2. **Novedades vs autorizaciones:** altas/bajas/cambios salariales contra contratos, adendas y aprobacion.\n"
        "3. **Conciliacion contable:** gasto de nomina y provisiones vs mayor y estados financieros.\n"
        "4. **Pago y existencia:** cruza transferencias bancarias con empleados activos y detecta duplicados.\n"
        "5. **Aportes y retenciones:** verifica IESS/impuestos/retenidos, calculo y pago oportuno.\n"
        "6. **Corte de periodo:** confirma devengado al cierre (nomina por pagar, vacaciones, beneficios).\n\n"
        "Si quieres, te armo un programa de trabajo listo para ejecutar en Papeles con muestra sugerida."
    )
    return {
        "answer": answer,
        "citations": [],
        "context_sources": ["Contexto cliente"],
        "confidence": 0.78,
        "prompt_meta": {"prompt_id": "payroll_fastpath", "prompt_version": "v1"},
        "mode_used": "chat_fastpath_payroll",
    }


def _risk_answer(cliente_id: str, query: str = "") -> dict[str, Any]:
    perfil = read_perfil(cliente_id) or {}
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    riesgo_global = perfil.get("riesgo_global", {}) if isinstance(perfil.get("riesgo_global"), dict) else {}
    nivel_global = str(riesgo_global.get("nivel") or "MEDIO").upper()

    top_lines: list[str] = []
    top_rows: list[dict[str, Any]] = []
    try:
        from analysis.ranking_areas import calcular_ranking_areas

        ranking = calcular_ranking_areas(cliente_id)
        if ranking is not None and not ranking.empty:
            vis = ranking.copy()
            if "con_saldo" in vis.columns:
                vis = vis[vis["con_saldo"] == True]  # noqa: E712
            for _, row in vis.head(3).iterrows():
                area = str(row.get("area") or "")
                nombre = str(row.get("nombre") or f"Area {area}")
                score = float(row.get("score_riesgo") or 0.0)
                prioridad = str(row.get("prioridad") or "media").upper()
                top_lines.append(f"- {area} {nombre}: {score:.1f}% ({prioridad})")
                top_rows.append({"area": area, "nombre": nombre, "score": score, "prioridad": prioridad})
    except Exception:
        top_lines = []
        top_rows = []

    cliente_nombre = str(cliente.get("nombre_legal") or cliente_id)
    justificacion = str(riesgo_global.get("justificacion_corta") or "").strip()

    def _driver_hint(area_name: str) -> str:
        n = area_name.lower()
        if "inversion" in n:
            return "valuacion de inversiones, VPP y revelaciones asociadas"
        if "patrimonio" in n:
            return "movimientos de capital, resultados acumulados y revelacion"
        if "gasto" in n:
            return "clasificacion del gasto y riesgo tributario de deducibilidad"
        if "cuentas por cobrar" in n:
            return "existencia, recuperabilidad y corte de cartera"
        if "efectivo" in n:
            return "integridad de tesoreria y conciliaciones bancarias"
        return "consistencia contable y soporte de saldos"

    explain_mode = _is_risk_why_question(query)
    if not top_lines:
        answer = (
            f"Riesgo actual del cliente `{cliente_nombre}`: **{nivel_global}**.\n\n"
            "Aun no tengo ranking de areas con saldo suficiente para priorizar. "
            "Siguiente paso: valida que el TB este cargado y luego te devuelvo top 3 areas criticas con score."
        )
        confidence = 0.62
    elif explain_mode:
        top = top_rows[0] if top_rows else {}
        top_name = str(top.get("nombre") or "area principal")
        top_score = float(top.get("score") or 0.0)
        reason_lines: list[str] = []
        if justificacion:
            reason_lines.append(f"- Contexto de encargo: {justificacion}")
        reason_lines.append(f"- Mayor concentracion de exposicion en `{top_name}` (score {top_score:.1f}%).")

        if len(top_rows) > 1 and float(top_rows[1].get("score") or 0.0) >= 45:
            reason_lines.append(
                f"- Segunda area con peso relevante `{top_rows[1].get('nombre')}` (score {float(top_rows[1].get('score') or 0.0):.1f}%)."
            )

        unique_drivers = []
        for row in top_rows[:3]:
            hint = _driver_hint(str(row.get("nombre") or ""))
            if hint not in unique_drivers:
                unique_drivers.append(hint)
        for hint in unique_drivers[:3]:
            reason_lines.append(f"- Driver tecnico: {hint}.")

        answer = (
            f"Buena pregunta. El riesgo global de `{cliente_nombre}` esta en **{nivel_global}** "
            "porque la exposicion no esta totalmente dispersa, sino concentrada en areas sensibles de juicio.\n\n"
            "Fundamento:\n"
            + "\n".join(reason_lines)
            + "\n\nEn resumen: no esta en BAJO porque hay concentracion y juicio tecnico; "
            "no lo llevo a MUY ALTO porque el resto de areas no muestran deterioro extremo al mismo nivel."
        )
        confidence = 0.9
    else:
        answer = (
            f"Riesgo global actual de la holding `{cliente_nombre}`: **{nivel_global}**.\n\n"
            "Top areas por riesgo en este momento:\n"
            + "\n".join(top_lines)
            + "\n\nSi quieres, te explico el por que tecnico de ese nivel y que pruebas ejecutar primero."
        )
        confidence = 0.86

    return {
        "answer": answer,
        "citations": [
            {
                "source": f"data/clientes/{cliente_id}/perfil.yaml",
                "excerpt": "Riesgo global y contexto del cliente",
                "norma": "Contexto cliente",
                "version": "v1",
                "vigente_desde": "",
                "ultima_actualizacion": "",
                "jurisdiccion": "Interna",
            },
        ],
        "context_sources": [f"data/clientes/{cliente_id}/perfil.yaml"],
        "confidence": confidence,
        "provider": "deterministic",
        "model": "risk_snapshot_v1",
        "prompt_meta": {"prompt_id": "risk_snapshot", "prompt_version": "v1"},
        "mode_used": "risk_snapshot",
    }


def _pilot_area_guidance_answer(cliente_id: str, query: str) -> dict[str, Any]:
    perfil = read_perfil(cliente_id) or {}
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}
    cliente_nombre = str(cliente.get("nombre_legal") or cliente_id)
    sector = str(cliente.get("sector") or "no confirmado")
    framework = str(encargo.get("marco_referencial") or "no confirmado")
    period = str(encargo.get("fecha_inicio_periodo") or encargo.get("anio_activo") or "no confirmado")

    answer = (
        f"Para `{cliente_nombre}` no registraria todavia un riesgo como conclusion. Partiria de estos hechos: "
        f"sector `{sector}`, marco `{framework}` y periodo iniciado `{period}`.\n\n"
        "**Riesgos candidatos que debes contrastar**\n"
        "1. Ingresos registrados sin que el servicio se haya prestado o sin soporte suficiente. Aseveraciones: ocurrencia y exactitud.\n"
        "2. Ingresos o notas de credito registrados en un periodo incorrecto. Aseveracion: corte.\n"
        "3. Servicios prestados pendientes de facturar o registrar. Aseveracion: integridad.\n"
        "4. Cuentas por cobrar inexistentes, discutidas o sin derecho exigible. Aseveraciones: existencia y derechos.\n"
        "5. Cartera cuyo deterioro no refleja mora, disputas, cobros posteriores o capacidad de pago. Aseveracion: valuacion.\n\n"
        "**Informacion que pediria**\n"
        "- Contratos, cartas de encargo y condiciones de facturacion.\n"
        "- Detalle de facturas, notas de credito y cobros alrededor del cierre.\n"
        "- Reportes de horas, entregables, hitos o evidencia de prestacion del servicio.\n"
        "- Auxiliar de cartera conciliado con mayor, antiguedad, cobros posteriores y saldos en disputa.\n"
        "- Politica contable aplicada y explicacion de cambios o excepciones.\n\n"
        "**Como documentar el razonamiento**\n"
        "Registra la cadena `hecho -> alerta -> riesgo candidato -> aseveracion -> evidencia requerida -> procedimiento -> resultado -> conclusion del responsable`. "
        "Si falta un eslabon, no presentes el riesgo ni el tratamiento como definitivo.\n\n"
        "**Preguntas para decidir**\n"
        "- Que hecho concreto aumenta la probabilidad de incorreccion y que magnitud podria tener?\n"
        "- Es una alerta general o afecta una aseveracion y poblacion identificables?\n"
        "- Que evidencia podria confirmar o contradecir la hipotesis?\n"
        "- Quien revisara y aprobara la conclusion?\n\n"
        "Limite actual: la biblioteca recupera interpretacion profesional propia, no el texto oficial. Coteja siempre la NIA o NIIF vigente antes de aprobar la conclusion."
    )
    return {
        "answer": answer,
        "citations": [],
        "context_sources": [
            f"data/clientes/{cliente_id}/perfil.yaml",
            "data/conocimiento_normativo/metodologia/aseveraciones.md",
        ],
        "confidence": 0.84,
        "provider": "deterministic",
        "model": "pilot_guidance_v1",
        "prompt_meta": {"prompt_id": "pilot_area_guidance", "prompt_version": "v1"},
        "mode_used": "pilot_area_guidance",
        "expert_criteria_used": True,
    }


def _next_steps_answer(cliente_id: str) -> dict[str, Any]:
    perfil = read_perfil(cliente_id) or {}
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    cliente_nombre = str(cliente.get("nombre_legal") or cliente_id)

    lines: list[str] = []
    try:
        from analysis.ranking_areas import calcular_ranking_areas

        ranking = calcular_ranking_areas(cliente_id)
        if ranking is not None and not ranking.empty:
            vis = ranking.copy()
            if "con_saldo" in vis.columns:
                vis = vis[vis["con_saldo"] == True]  # noqa: E712
            for _, row in vis.head(3).iterrows():
                area = str(row.get("area") or "")
                nombre = str(row.get("nombre") or f"Area {area}")
                score = float(row.get("score_riesgo") or 0.0)
                lines.append(f"{area} {nombre} ({score:.1f}%)")
    except Exception:
        lines = []

    if not lines:
        answer = (
            f"Vamos en este orden para `{cliente_nombre}`:\n\n"
            "1) Confirmar que TB y mayor esten cargados y vigentes.\n"
            "2) Definir materialidad final del encargo.\n"
            "3) Abrir papeles de trabajo y ejecutar pruebas en areas criticas.\n\n"
            "Si quieres, te doy ese plan ya en checklist de trabajo."
        )
        confidence = 0.64
    else:
        answer = (
            f"Perfecto. Para `{cliente_nombre}`, arranquemos asi:\n\n"
            f"1) Prioriza `{lines[0]}` y ejecuta pruebas sustantivas de entrada.\n"
            f"2) Continua con `{lines[1] if len(lines) > 1 else lines[0]}` y valida soportes de cierre.\n"
            f"3) Cierra con `{lines[2] if len(lines) > 2 else lines[-1]}` y documenta conclusion tecnica.\n\n"
            "Si quieres, te lo convierto ahora en tareas concretas de Papeles de Trabajo."
        )
        confidence = 0.84

    return {
        "answer": answer,
        "citations": [
            {
                "source": f"data/clientes/{cliente_id}/perfil.yaml",
                "excerpt": "Contexto base del cliente",
                "norma": "Contexto cliente",
                "version": "v1",
                "vigente_desde": "",
                "ultima_actualizacion": "",
                "jurisdiccion": "Interna",
            },
        ],
        "context_sources": [f"data/clientes/{cliente_id}/perfil.yaml"],
        "confidence": confidence,
        "provider": "deterministic",
        "model": "next_steps_v1",
        "prompt_meta": {"prompt_id": "next_steps", "prompt_version": "v1"},
        "mode_used": "next_steps",
    }


def _inventory_answer(cliente_id: str) -> dict[str, Any]:
    perfil = read_perfil(cliente_id) or {}
    workflow = read_workflow(cliente_id) or {}
    hallazgos = read_hallazgos(cliente_id) or ""
    docs = list_documentos(cliente_id) or []

    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}
    materialidad = perfil.get("materialidad", {}) if isinstance(perfil.get("materialidad"), dict) else {}

    docs_names = [str(d.get("name") or "") for d in docs if isinstance(d, dict)]
    has_tb = "tb.xlsx" in docs_names
    has_mayor = "mayor.xlsx" in docs_names
    extra_docs = [n for n in docs_names if n not in {"tb.xlsx", "mayor.xlsx"}]
    hallazgos_count = len([x for x in hallazgos.splitlines() if x.strip().startswith("## ")])
    phase = str(encargo.get("fase_actual") or workflow.get("current_phase") or "no configurada").strip()

    mp = 0.0
    if isinstance(materialidad, dict):
        prelim = materialidad.get("preliminar", {}) if isinstance(materialidad.get("preliminar"), dict) else {}
        final = materialidad.get("final", {}) if isinstance(materialidad.get("final"), dict) else {}
        for key in ["materialidad_planeacion", "materialidad_global"]:
            if key in final and final.get(key):
                try:
                    mp = float(final.get(key))
                    break
                except Exception:
                    pass
            if key in prelim and prelim.get(key):
                try:
                    mp = float(prelim.get(key))
                    break
                except Exception:
                    pass

    answer = (
        f"Tengo este contexto activo del cliente `{cliente_id}`:\n\n"
        f"1) Perfil: nombre `{str(cliente.get('nombre_legal') or cliente_id)}`, sector `{str(cliente.get('sector') or 'N/D')}`, marco `{str(encargo.get('marco_referencial') or 'N/D')}`.\n"
        f"2) Datos financieros: TB {'si' if has_tb else 'no'} | Mayor {'si' if has_mayor else 'no'}.\n"
        f"3) Documentos adicionales: {len(extra_docs)} cargados.\n"
        f"4) Hallazgos registrados: {hallazgos_count}.\n"
        f"5) Fase de workflow: `{phase}`.\n"
        f"6) Materialidad de referencia: {'definida' if mp > 0 else 'no definida'}.\n\n"
        "Si quieres, te digo en 30 segundos que falta para pasar a la siguiente etapa."
    )

    return {
        "answer": answer,
        "citations": [
            {
                "source": f"data/clientes/{cliente_id}/perfil.yaml",
                "excerpt": "Perfil de cliente y encargo",
                "norma": "Contexto cliente",
                "version": "v1",
                "vigente_desde": "",
                "ultima_actualizacion": "",
                "jurisdiccion": "Interna",
            },
            {
                "source": f"data/clientes/{cliente_id}/workflow.yaml",
                "excerpt": "Estado de workflow y gates",
                "norma": "Contexto cliente",
                "version": "v1",
                "vigente_desde": "",
                "ultima_actualizacion": "",
                "jurisdiccion": "Interna",
            },
        ],
        "context_sources": [
            f"data/clientes/{cliente_id}/perfil.yaml",
            f"data/clientes/{cliente_id}/workflow.yaml",
        ],
        "confidence": 0.82,
        "provider": "inventory",
        "model": "deterministic",
        "prompt_meta": {"prompt_id": "inventory", "prompt_version": "v1"},
        "mode_used": "inventory",
    }


def _client_snapshot(cliente_id: str) -> str:
    perfil = read_perfil(cliente_id) or {}
    workflow = read_workflow(cliente_id) or {}
    hallazgos = read_hallazgos(cliente_id) or ""
    docs = list_documentos(cliente_id) or []
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}
    questionnaire = (
        perfil.get("cuestionario_auditoria", {})
        if isinstance(perfil.get("cuestionario_auditoria"), dict)
        else {}
    )
    docs_names = [str(d.get("name") or "") for d in docs if isinstance(d, dict)]
    has_tb = "tb.xlsx" in docs_names
    has_mayor = "mayor.xlsx" in docs_names
    hallazgos_count = len([x for x in hallazgos.splitlines() if x.strip().startswith("## ")])
    return (
        f"Cliente: {str(cliente.get('nombre_legal') or cliente_id)} | "
        f"Sector: {str(cliente.get('sector') or 'N/D')} | "
        f"Marco: {str(encargo.get('marco_referencial') or 'N/D')} | "
        f"Periodo activo: {str(encargo.get('anio_activo') or 'N/D')} | "
        f"Cierre: {str(encargo.get('fecha_cierre_periodo') or 'N/D')} | "
        f"Fase configurada por el auditor: {str(encargo.get('fase_actual') or workflow.get('current_phase') or 'no configurada')} | "
        f"TB: {'si' if has_tb else 'no'} | Mayor: {'si' if has_mayor else 'no'} | "
        f"Docs extra: {len([x for x in docs_names if x not in {'tb.xlsx', 'mayor.xlsx'}])} | "
        f"Hallazgos: {hallazgos_count} | "
        f"Presion por resultados confirmada: {'si' if questionnaire.get('presion_resultados') is True else 'no'} | "
        f"Partes relacionadas confirmadas: {'si' if questionnaire.get('partes_relacionadas') is True else 'no'} | "
        f"Ingresos complejos confirmados: {'si' if questionnaire.get('ingresos_complejos') is True else 'no'}"
    )


def _risk_snapshot(cliente_id: str) -> str:
    lines: list[str] = []
    try:
        from analysis.ranking_areas import calcular_ranking_areas

        ranking = calcular_ranking_areas(cliente_id)
        if ranking is None or ranking.empty:
            return ""
        vis = ranking.copy()
        if "con_saldo" in vis.columns:
            vis = vis[vis["con_saldo"] == True]  # noqa: E712
        if vis.empty:
            return ""
        lines.append("Top areas por riesgo (motor Python):")
        for _, row in vis.head(5).iterrows():
            area = str(row.get("area") or "")
            nombre = str(row.get("nombre") or "")
            score = float(row.get("score_riesgo") or 0.0)
            prioridad = str(row.get("prioridad") or "media")
            drivers: list[str] = []
            raw_drivers = row.get("drivers")
            if isinstance(raw_drivers, list):
                drivers = [str(x) for x in raw_drivers if str(x).strip()]
            driver_txt = f" | drivers: {', '.join(drivers[:3])}" if drivers else ""
            lines.append(f"- {area} {nombre}: score={score:.2f}, prioridad={prioridad}{driver_txt}")
    except Exception:
        return ""
    return "\n".join(lines)


def _parse_iso_date(raw_value: str) -> date | None:
    value = str(raw_value or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except Exception:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            print(f"[WARN] Formato de fecha invalido en ultima_actualizacion: {value}")
            return None


def _build_staleness_warning(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return ""
    today = datetime.now(timezone.utc).date()
    warnings: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        metadata = chunk.metadata or {}
        norma = str(metadata.get("norma") or "Norma sin identificar").strip()
        last_update_raw = str(metadata.get("ultima_actualizacion") or "").strip()
        if not last_update_raw:
            continue
        last_update = _parse_iso_date(last_update_raw)
        if not last_update:
            continue
        if (today - last_update).days <= 365:
            continue
        key = f"{norma}|{last_update.isoformat()}"
        if key in seen:
            continue
        seen.add(key)
        warnings.append(
            f"⚠️ Verificar vigencia: {norma} fue indexada el {last_update.isoformat()}.\n"
            "   Confirma que no hay actualizaciones normativas recientes."
        )
    return "\n".join(warnings)


def _build_pending_review_warning(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return ""
    pending = get_pending_normative_changes()
    if not pending:
        return ""

    def _norm_key(text: str) -> str:
        return "".join(ch for ch in str(text or "").upper() if ch.isalnum())

    chunk_norms = {_norm_key(str((c.metadata or {}).get("norma") or "")) for c in chunks}
    chunk_norms = {x for x in chunk_norms if x}
    if not chunk_norms:
        return ""

    lines: list[str] = []
    seen: set[str] = set()
    for row in pending:
        norma = str(row.get("norma") or "").strip()
        key = _norm_key(norma)
        if not key:
            continue
        if not any(key in cn or cn in key for cn in chunk_norms):
            continue
        if norma in seen:
            continue
        seen.add(norma)
        lines.append(
            f"⚠️ Verificar vigencia: {norma} tiene cambio detectado pendiente de revision."
        )
    return "\n".join(lines)


def _append_staleness_warning(answer: str, chunks: list[RetrievedChunk]) -> str:
    warning = _build_staleness_warning(chunks)
    pending_warning = _build_pending_review_warning(chunks)
    pending_quality_sources = {
        chunk.source
        for chunk in chunks
        if "conocimiento_normativo" in chunk.source.replace("\\", "/")
        and not is_citation_eligible(chunk.metadata)
    }


    quality_warning = ""
    if pending_quality_sources:
        quality_warning = (
            "Aviso de calidad: el contexto incluye "
            f"{len(pending_quality_sources)} fuente(s) interna(s) pendiente(s) de verificacion. "
            "Se usan solo como orientacion y no se presentan como citas normativas."
        )
    all_warnings = "\n".join(
        [w for w in [warning, pending_warning, quality_warning] if w.strip()]
    ).strip()
    if not all_warnings:
        return answer
    return f"{answer.rstrip()}\n\n{all_warnings}"


def _normative_guard_response(
    action: str,
    reason: str,
    chunks: list[RetrievedChunk],
) -> dict[str, Any]:
    if action == "block_unverified_citation":
        answer = (
            "Cita normativa bloqueada. No puedo proporcionar ni atribuir el parrafo, articulo o referencia "
            "solicitada porque la fuente recuperada aun no esta verificada para citas. "
            "Puedo orientar el analisis y senalar que texto oficial debe cotejarse, pero no inventar el localizador."
        )
    else:
        answer = (
            "Conclusion automatica bloqueada. No ejecutare esa instruccion como un veredicto de auditoria. "
            "Puedo convertirla en una hipotesis, identificar la evidencia que falta y explicar los factores "
            "que el auditor responsable debe documentar antes de concluir."
        )
    return {
        "answer": _append_staleness_warning(f"{answer}\n\nMotivo: {reason}", chunks),
        "citations": [],
        "context_sources": [chunk.source for chunk in chunks],
        "confidence": 0.98,
        "prompt_meta": {"prompt_id": "normative_guard", "prompt_version": "v1"},
        "mode_used": action,
        "expert_criteria_used": False,
    }


def _blocked_normative_output(
    issues: tuple[str, ...],
    chunks: list[RetrievedChunk],
    *,
    provider: str,
    model: str,
    mode: str,
    expert_criteria_used: bool,
) -> dict[str, Any]:
    answer = (
        "Respuesta normativa bloqueada. La salida generada contenia una atribucion normativa "
        "sin una fuente verificada e identificada inmediatamente despues de la afirmacion. "
        "No se mostrara ese contenido ni se intentara completar el localizador. Puedes reformular "
        "la consulta como orientacion o esperar a que la fuente correspondiente sea validada."
    )
    return {
        "answer": _append_staleness_warning(answer, chunks),
        "citations": [],
        "context_sources": [chunk.source for chunk in chunks],
        "confidence": 0.98,
        "web_search_used": False,
        "provider": provider,
        "model": model,
        "prompt_meta": {"prompt_id": "normative_output_guard", "prompt_version": "v1"},
        "mode_used": f"{mode}_output_blocked",
        "expert_criteria_used": expert_criteria_used,
        "quality_flags": list(issues),
    }


def _blocked_grounding_output(
    issues: tuple[str, ...],
    chunks: list[RetrievedChunk],
    *,
    provider: str,
    model: str,
    mode: str,
    expert_criteria_used: bool,
) -> dict[str, Any]:
    answer = (
        "Respuesta retenida por el verificador de hechos. El borrador mezclaba hechos confirmados, "
        "antecedentes o supuestos no documentados en el expediente. El contenido inseguro no se mostrara. "
        "Puedes volver a consultar: SocioAI mantendra los supuestos como hipotesis pendientes de validacion."
    )
    return {
        "answer": _append_staleness_warning(answer, chunks),
        "citations": [],
        "context_sources": [chunk.source for chunk in chunks],
        "confidence": 0.98,
        "web_search_used": False,
        "provider": provider,
        "model": model,
        "prompt_meta": {"prompt_id": "claim_grounding_guard", "prompt_version": "v1"},
        "mode_used": f"{mode}_grounding_blocked",
        "expert_criteria_used": expert_criteria_used,
        "quality_flags": list(issues),
    }


def _fallback_answer(
    query: str,
    cliente_id: str,
    chunks: list[RetrievedChunk],
    *,
    mode: str = "chat",
    area_context: str = "",
    expert_criteria_used: bool = False,
) -> dict[str, Any]:
    sources = [c.source for c in chunks]
    first_context = chunks[0].excerpt[:240] if chunks else "Sin contexto recuperado."
    citations: list[dict[str, str]] = []
    if mode == "chat":
        if _is_greeting(query):
            snapshot = _client_snapshot(cliente_id)
            answer = (
                f"Hola. Estoy contigo en el cliente `{cliente_id}`.\n\n"
                f"Contexto rapido:\n{snapshot}\n\n"
                "Dime que quieres resolver primero y lo trabajamos en modo auditor."
            )
            confidence = 0.72
        elif _is_provider_question(query):
            provider_label = _current_provider_label()
            answer = (
                f"Si. En este backend estoy configurado para usar `{provider_label}`.\n\n"
                "Importante:\n"
                "1) Python calcula numeros, materialidad y gates.\n"
                "2) La AI aplica juicio profesional y recomendaciones.\n"
                "3) Si falla el proveedor, activo fallback controlado."
            )
            confidence = 0.7
        elif _is_data_inventory_question(query):
            return _inventory_answer(cliente_id)
        elif _is_next_steps_question(query):
            return _next_steps_answer(cliente_id)
        else:
            snapshot = _client_snapshot(cliente_id)
            risk_snapshot = _risk_snapshot(cliente_id)
            provider_label = _current_provider_label()
            procedure_hint = _procedural_fallback_hint(query)
            area_hint = area_context.strip()
            answer = (
                "Estoy respondiendo en modo de respaldo porque no hay LLM generativo activo.\n"
                f"Proveedor detectado: `{provider_label}`.\n\n"
                f"Consulta: `{query}`\n\n"
                f"{procedure_hint + chr(10) + chr(10) if procedure_hint else ''}"
                f"{area_hint + chr(10) + chr(10) if area_hint else ''}"
                f"Contexto actual:\n{snapshot}\n\n"
                f"{risk_snapshot if risk_snapshot else 'Aún no tengo ranking con saldo para priorizar áreas.'}\n\n"
                "Si configuras la API key, paso a respuesta conversacional con razonamiento completo y normativa citada."
            )
            confidence = 0.68 if chunks else 0.55
    else:
        answer = (
            f"No se pudo completar la recuperacion normativa para `{query}` en modo `{mode}`. "
            "Se recomienda validar manualmente NIA/NIIF aplicables y evidencia de soporte."
            f"\n\nContexto clave: {first_context}"
        )
        confidence = 0.30 if chunks else 0.15

    return {
        "answer": _append_staleness_warning(answer, chunks),
        "citations": citations,
        "context_sources": sources,
        "confidence": confidence,
        "prompt_meta": {"prompt_id": "fallback", "prompt_version": "v1"},
        "mode_used": f"{mode}_fallback",
        "expert_criteria_used": expert_criteria_used,
    }


def _has_llm_credentials() -> bool:
    _provider, key = _resolved_provider()
    return bool(key)


def _llm_answer(
    query: str,
    chunks: list[RetrievedChunk],
    *,
    mode: str = "chat",
    cliente_id: str = "",
    memory_summary: str = "",
    recent_history: list[dict[str, str]] | None = None,
    web_results: list[dict[str, str]] | None = None,
    area_context: str = "",
    expert_criteria_used: bool = False,
    learning_role: str = "semi",
) -> dict[str, Any]:
    provider, api_key = _resolved_provider()
    from openai import OpenAI
    timeout_seconds_raw = float(os.getenv("LLM_TIMEOUT_SECONDS", "45"))
    timeout_seconds = max(10.0, min(timeout_seconds_raw, 120.0))
    max_tokens_raw = int(os.getenv("LLM_CHAT_MAX_TOKENS", "1000"))
    max_tokens = max(300, min(max_tokens_raw, 1600))

    if provider == "deepseek":
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY no configurada")
        model = os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat").strip() or "deepseek-chat"
        base_url = (os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").strip()
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_seconds, max_retries=0)
    else:
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY no configurada")
        model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        client = OpenAI(api_key=api_key, timeout=timeout_seconds, max_retries=0)

    joined_context = "\n\n".join(
        [
            f"[{'FUENTE' if is_citation_eligible(c.metadata) else 'ORIENTACION'} {index}] "
            f"[{c.source}] ({(c.metadata or {}).get('norma', 'N/A')} | "
            f"calidad: {'CITA VERIFICADA' if is_citation_eligible(c.metadata) else 'ORIENTACION NO VERIFICADA'} | "
            f"periodo documento: {(c.metadata or {}).get('document_period', 'N/D')} | "
            f"estado temporal: {(c.metadata or {}).get('temporal_status', 'N/D')} | "
            f"vigente: {(c.metadata or {}).get('vigente_desde', 'N/D')} | "
            f"actualizacion: {(c.metadata or {}).get('ultima_actualizacion', 'N/D')}) {c.excerpt}"
            for index, c in enumerate(chunks[:6], start=1)
        ]
    )
    snapshot = _client_snapshot(cliente_id) if cliente_id else ""
    risk_snapshot = _risk_snapshot(cliente_id) if cliente_id else ""
    if snapshot:
        joined_context = f"[SNAPSHOT CLIENTE]\n{snapshot}\n\n{joined_context}".strip()
    if risk_snapshot:
        joined_context = f"{joined_context}\n\n[SNAPSHOT RIESGO]\n{risk_snapshot}".strip()
    if area_context:
        joined_context = f"{joined_context}\n\n{area_context}".strip()
    if cliente_id and should_include_version_context(query):
        try:
            version_context = build_profile_version_context(read_perfil(cliente_id) or {})
            joined_context = f"{joined_context}\n\n{version_context}".strip()
        except Exception:
            pass
    if web_results:
        web_block = "\n\n".join(
            f"[WEB: {r['title']}] {r['url']}\n{r['content']}"
            for r in web_results
        )
        joined_context = f"{joined_context}\n\n[FUENTES WEB — criterio externo]\n{web_block}".strip()
    instruction, prompt_meta = render_prompt(mode, query=query, context=joined_context)

    reasoning_hint = ""
    if _is_criterion_challenge(query):
        reasoning_hint = (
            "\nEsta consulta está en modo desafío. No digas que estás reescribiendo la respuesta y no entregues "
            "una conclusión cerrada como primera reacción. Identifica la afirmación o supuesto del auditor, separa "
            "cuenta contable de riesgo de incorrección material y cuestiona causa, aseveración, evidencia y explicación "
            "alternativa. Si el auditor no expuso todavía su razonamiento, formula preguntas guiadas y pídele que proponga "
            "su hipótesis antes de evaluarla. Solo califica una respuesta cuando el auditor haya aportado una respuesta "
            "propia; en ese caso indica qué está bien, qué falta y cuál sería el siguiente paso para fortalecerla."
        )
    elif _is_risk_why_question(query):
        reasoning_hint = (
            "\nAdemas: explica explicitamente por que ese nivel de riesgo es razonable, "
            "incluyendo causa, impacto y que evidencia faltaria para subir o bajar el nivel."
        )
    elif _is_risk_question(query):
        reasoning_hint = (
            "\nAdemas: no repitas solo el ranking; interpreta los datos y concluye con criterio auditor."
        )

    # Adaptar mensaje según learning_role del auditor
    learning_role_instruction = ""
    if learning_role == "junior":
        learning_role_instruction = (
            "\n\nNOTA SOBRE TU NIVEL (Junior): Explica PASO A PASO. "
            "Incluye el PORQUÉ de cada cosa, no solo el QUÉ. "
            "Define términos técnicos. Sugiere dónde aprender más."
        )
    elif learning_role == "semi":
        learning_role_instruction = (
            "\n\nNOTA SOBRE TU NIVEL (Semi-Senior): Sé conciso pero técnico. "
            "Explica el razonamiento detrás de cada procedimiento. "
            "Señala casos especiales o excepciones."
        )
    elif learning_role == "senior":
        learning_role_instruction = (
            "\n\nNOTA SOBRE TU NIVEL (Senior): Ve al grano. "
            "Asume conocimiento de normas y procedimientos. "
            "Enfócate en excepciones, riesgos complejos y criterio profesional."
        )
    elif learning_role == "socio":
        learning_role_instruction = (
            "\n\nNOTA SOBRE TU NIVEL (Socio): Resumen ejecutivo. "
            "Implicaciones de negocio, riesgos y recomendaciones. "
            "Criterio estratégico, no procedimientos."
        )

    orientation_only_rules = ""
    if not any(is_citation_eligible(chunk.metadata) for chunk in chunks[:6]):
        orientation_only_rules = (
            "Todas las fichas normativas recuperadas son orientacion interna no habilitada para citas. No uses [FUENTE n] ni frases como "
            "'segun la NIA', 'la NIA establece', 'la NIIF exige' o equivalentes. Si necesitas identificar la base, usa la formula "
            "'la interpretacion profesional interna asociada a [norma] orienta a considerar...' y aclara que debe cotejarse con el texto oficial. "
        )

    common_output_rules = (
        "Cierra la respuesta completa y prioriza completitud sobre detalle. "
        "Separa siempre hechos documentados de hipotesis: redacta causas no confirmadas con 'podria' o 'debe investigarse'. "
        "No afirmes presion por resultados, metas, intencion de la gerencia, partes relacionadas, reversiones ni fallas de control si el contexto no las confirma. "
        "No describas los ingresos como complejos si el perfil indica que esa condicion no esta confirmada. "
        "En ese caso tampoco escribas que el corte o el reconocimiento de ingresos es 'inherentemente complejo'; limita la respuesta a decir que debe comprenderse y probarse. "
        "Una ficha que enumera factores de riesgo aporta candidatos generales, no demuestra que existan en este cliente. "
        "Un documento marcado ANTECEDENTE_PERIODO_ANTERIOR solo permite formular seguimiento; no presentes sus importes ni hallazgos como hechos del periodo activo. "
        "Para pruebas de corte usa exclusivamente el periodo activo y la fecha de cierre del snapshot del cliente. "
        "No concluyas que una provision es suficiente solo porque hubo cobros posteriores, ni que debe aumentarse solo porque no los hubo; "
        "presenta los cobros como una evidencia que debe evaluarse junto con antiguedad, disputas, historial y demas datos disponibles. "
        "No inventes tamanos de muestra, cantidades a seleccionar, porcentajes ni umbrales: indicalos como decisiones pendientes "
        "hasta conocer poblacion, materialidad y objetivo del procedimiento. "
        "Esta prohibido escribir cantidades como 'ultimas 10 facturas', 'primeras 10', 'muestra de 5' o cualquier numero de elementos a revisar. "
        "Limita el analisis al ciclo de Ingresos y Cuentas por cobrar solicitado; no agregues asuntos tributarios, de consolidacion "
        "u otras areas salvo que la consulta los pida y el contexto recuperado los sustente. "
        "No atribuyas una afirmacion a una norma si su contexto esta marcado ORIENTACION NO VERIFICADA; presentala como "
        "interpretacion profesional interna y recomienda cotejarla con la fuente oficial. "
        "Cuando uses una fuente verificada, coloca su identificador exacto [FUENTE n] inmediatamente despues de la afirmacion que respalda."
        + orientation_only_rules
    )
    user_content = (
        f"Consulta:\n{query}\n\n"
        "Responde de forma conversacional, concreta y accionable para un auditor, en un maximo de 450 palabras. "
        "No inventes modelos de facturación, composición de cuentas, uso de controles, porcentajes de enfoque ni procedimientos ya ejecutados. "
        "Un ranking cuantitativo prioriza revisión, pero no confirma riesgo ni reemplaza el juicio. Formula las recomendaciones condicionalmente cuando falte evidencia. "
        + common_output_rules
        + reasoning_hint
        + learning_role_instruction
        if mode == "chat"
        else (
            f"Consulta:\n{query}\n\n"
            "Devuelve recomendacion accionable con criterio, pasos y evidencia. "
            + common_output_rules
            + learning_role_instruction
        )
    )

    # Construir lista de mensajes con memoria inyectada
    system_content = instruction
    if memory_summary:
        system_content = f"{instruction}\n\n{memory_summary}"

    messages_for_llm: list[dict[str, str]] = [{"role": "system", "content": system_content}]

    # Inyectar historial reciente antes de la pregunta actual
    if recent_history:
        messages_for_llm.extend(recent_history)

    messages_for_llm.append({"role": "user", "content": user_content})

    response = client.chat.completions.create(
        model=model,
        messages=messages_for_llm,
        temperature=0.2,
        max_tokens=max_tokens,
    )

    text = ""
    if response.choices and response.choices[0].message:
        text = str(response.choices[0].message.content or "").strip()
    if not text.strip():
        text = "No se obtuvo respuesta del modelo."

    normative_metadata = [chunk.metadata for chunk in chunks[:6]]
    output_validation = validate_normative_output(text, normative_metadata)
    try:
        grounding_profile = read_perfil(cliente_id) or {} if cliente_id else {}
    except Exception:
        grounding_profile = {}
    grounding_validation = validate_client_grounding(text, grounding_profile, chunks[:6])
    quality_repair_used = False
    if not output_validation.allowed or not grounding_validation.allowed:
        repair_issues = [f"normativa:{issue}" for issue in output_validation.issues]
        repair_issues.extend(f"hechos:{issue}" for issue in grounding_validation.issues)
        repair_messages = messages_for_llm + [
            {"role": "assistant", "content": text},
            {
                "role": "user",
                "content": (
                    "Reescribe la respuesta completa porque los verificadores detectaron estos problemas: "
                    f"{', '.join(repair_issues)}. "
                    "No repitas el borrador. Conserva como hechos solo lo confirmado por el expediente; marca el resto como hipotesis "
                    "en la misma oracion y etiqueta todo dato de un periodo anterior como antecedente. No inventes procesos del cliente. "
                    "No atribuyas obligaciones a NIA o NIIF ni uses [FUENTE n] cuando la orientacion no esta verificada; identifica cualquier "
                    "base solo como interpretacion profesional interna que debe cotejarse con el texto oficial. Entrega directamente la respuesta "
                    "final: no menciones el borrador, los verificadores, la correccion ni que estas reescribiendo."
                ),
            },
        ]
        repaired_response = client.chat.completions.create(
            model=model,
            messages=repair_messages,
            temperature=0.1,
            max_tokens=max_tokens,
        )
        repaired_text = ""
        if repaired_response.choices and repaired_response.choices[0].message:
            repaired_text = _strip_repair_preamble(repaired_response.choices[0].message.content or "")
        repaired_normative_validation = validate_normative_output(repaired_text, normative_metadata)
        normative_redaction_used = False
        if not repaired_normative_validation.allowed:
            redacted_text = redact_unsupported_normative_units(
                repaired_text,
                repaired_normative_validation.issues,
            )
            redacted_validation = validate_normative_output(redacted_text, normative_metadata)
            if not redacted_text or not redacted_validation.allowed:
                return _blocked_normative_output(
                    repaired_normative_validation.issues,
                    chunks,
                    provider=provider,
                    model=model,
                    mode=mode,
                    expert_criteria_used=expert_criteria_used,
                )
            repaired_text = (
                f"{redacted_text}\n\n"
                "Nota de control: se retiro una atribucion normativa que no podia respaldarse como cita verificada."
            )
            normative_redaction_used = True
        repaired_grounding_validation = validate_client_grounding(
            repaired_text,
            grounding_profile,
            chunks[:6],
        )
        grounding_redaction_used = False
        if not repaired_text or not repaired_grounding_validation.allowed:
            claim_redacted_text = redact_unsupported_claim_units(
                repaired_text,
                repaired_grounding_validation.issues,
            )
            claim_redacted_validation = validate_client_grounding(
                claim_redacted_text,
                grounding_profile,
                chunks[:6],
            )
            claim_redacted_normative_validation = validate_normative_output(
                claim_redacted_text,
                normative_metadata,
            )
            if (
                not claim_redacted_text
                or not claim_redacted_validation.allowed
                or not claim_redacted_normative_validation.allowed
            ):
                return _blocked_grounding_output(
                    repaired_grounding_validation.issues or grounding_validation.issues,
                    chunks,
                    provider=provider,
                    model=model,
                    mode=mode,
                    expert_criteria_used=expert_criteria_used,
                )
            repaired_text = (
                f"{claim_redacted_text}\n\n"
                "Nota de control: se retiro una afirmacion sobre el cliente que no estaba respaldada por el expediente."
            )
            grounding_redaction_used = True
        text = repaired_text
        quality_repair_used = True
    else:
        normative_redaction_used = False
        grounding_redaction_used = False

    ok_min_output, missing = validate_minimum_output(text, mode=mode)
    if not ok_min_output:
        text = (
            f"{text.strip()}\n\n"
            "Nota de control de calidad: la respuesta no cumplio todos los componentes minimos esperados "
            f"({', '.join(missing)})."
        )

    citations = _citations_used_in_answer(text, chunks)

    confidence = (
        0.72 if chunks and not web_results
        else 0.65 if chunks and web_results
        else 0.55 if web_results
        else 0.35
    )

    return {
        "answer": _append_staleness_warning(text.strip(), chunks),
        "citations": citations,
        "context_sources": [c.source for c in chunks] + [r["url"] for r in (web_results or [])],
        "confidence": confidence,
        "web_search_used": bool(web_results),
        "provider": provider,
        "model": model,
        "prompt_meta": prompt_meta,
        "mode_used": mode,
        "expert_criteria_used": expert_criteria_used,
        "quality_repair_used": quality_repair_used,
        "normative_repair_used": quality_repair_used and not output_validation.allowed,
        "grounding_repair_used": quality_repair_used and not grounding_validation.allowed,
        "normative_redaction_used": normative_redaction_used,
        "grounding_redaction_used": grounding_redaction_used,
    }


def _cache_response_with_ttl(response: dict[str, Any], cache_key: str, ttl_only_success: bool = True) -> dict[str, Any]:
    """Guarda respuesta en caché si es exitosa (sin cached flag)."""
    if response and not response.get("cached"):
        # Solo cachear si fue exitosa (tiene answer o text)
        if response.get("answer") or response.get("text"):
            set_cached_response(cache_key, response)
    return response


def generate_chat_response(
    cliente_id: str,
    query: str,
    *,
    user_sub: str = "",
    user_display_name: str = "",
    user_role: str = "",
    learning_role: str = "semi",
    conversation_id: str = "",
) -> dict[str, Any]:
    # Respuestas de alto valor y baja latencia, siempre contextuales.
    # Verificar caché de respuesta (FASE 5: Caché RAG)
    signature_parts: list[str] = []
    for context_name in ("perfil.yaml", "entity_profile_draft.json"):
        context_path = CLIENTES_ROOT / cliente_id / context_name
        if context_path.exists():
            stat = context_path.stat()
            signature_parts.append(f"{context_name}:{stat.st_mtime_ns}:{stat.st_size}")
    response_cache_key = build_response_cache_key(
        cliente_id,
        query,
        mode="chat",
        learning_role=learning_role,
        context_signature="|".join(signature_parts),
        conversation_id=conversation_id,
    )
    cached_response = get_cached_response(response_cache_key)
    if cached_response is not None:
        cached_response["cached"] = True
        return cached_response

    if _is_data_inventory_question(query):
        return _inventory_answer(cliente_id)
    if _is_next_steps_question(query):
        return _next_steps_answer(cliente_id)
    if _is_payroll_question(query):
        return _payroll_tests_answer(cliente_id)

    attention_question = _is_client_attention_question(query)
    criterion_challenge = _is_criterion_challenge(query)
    client_first_question = attention_question or criterion_challenge
    chunks = _retrieve_chunks(cliente_id, query, top_k=12 if client_first_question else 6)
    if client_first_question:
        client_chunks = [
            chunk for chunk in chunks
            if str((chunk.metadata or {}).get("tipo") or "").upper() == "CLIENTE"
        ]
        if client_chunks:
            chunks = client_chunks[:6]
    area_match = _detect_area_from_query(query)
    area_code = str((area_match or {}).get("area_codigo") or "").strip()
    area_context = ""
    if area_code:
        area_context = _enrich_context_with_area_procedures(area_code, "")

    normative_decision = evaluate_normative_request(query, [chunk.metadata for chunk in chunks])
    if normative_decision.blocked:
        result = _normative_guard_response(
            normative_decision.action,
            normative_decision.reason,
            chunks,
        )
        set_cached_response(response_cache_key, result)
        return result

    sector = ""
    try:
        perfil = read_perfil(cliente_id) or {}
        cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
        sector_candidates = [
            cliente.get("sector"),
            cliente.get("sector_actividad"),
            perfil.get("sector"),
            perfil.get("industria"),
        ]
        for candidate in sector_candidates:
            value = str(candidate or "").strip()
            if value:
                sector = value
                break
    except Exception:
        sector = ""

    expert_criteria_used = False
    area_context, expert_criteria_used = _enrich_context_with_expert_criteria(
        area_code, sector, area_context, query=query
    )

    # Construir contexto de memoria (resúmenes + mensajes recientes)
    memory_summary: str = ""
    recent_history: list[dict[str, str]] = []
    try:
        from backend.services.memory_service import build_memory_context
        memory_summary, recent_history = build_memory_context(cliente_id, conversation_id=conversation_id)
    except Exception:
        pass

    # Web search fallback: si los chunks locales son insuficientes, buscar en la web
    web_results: list[dict[str, str]] = []
    if _web_fallback_enabled() and _needs_web_search(chunks):
        try:
            from backend.services.web_search_service import search_web
            web_results = search_web(query, max_results=3)
        except Exception:
            pass

    if not _has_llm_credentials():
        if _is_pilot_area_guidance_question(query):
            result = _pilot_area_guidance_answer(cliente_id, query)
        elif _is_risk_question(query):
            result = _risk_answer(cliente_id, query)
            result["expert_criteria_used"] = expert_criteria_used
        else:
            result = _fallback_answer(
                query,
                cliente_id,
                chunks,
                mode="chat",
                area_context=area_context,
                expert_criteria_used=expert_criteria_used,
            )
        set_cached_response(response_cache_key, result)
        return result

    try:
        # El chat del mentor explica el razonamiento de riesgo en lenguaje natural.
        # El JSON de judgement_risk queda reservado para generate_judgement_response.
        result = _llm_answer(
            query, chunks, mode="chat", cliente_id=cliente_id,
            memory_summary=memory_summary, recent_history=recent_history,
            web_results=web_results or None,
            area_context=area_context,
            expert_criteria_used=expert_criteria_used,
            learning_role=learning_role,
        )
        set_cached_response(response_cache_key, result)
        return result
    except Exception:
        if _is_risk_question(query):
            result = _risk_answer(cliente_id, query)
            result["expert_criteria_used"] = expert_criteria_used
        else:
            result = _fallback_answer(
                query,
                cliente_id,
                chunks,
                mode="chat",
                area_context=area_context,
                expert_criteria_used=expert_criteria_used,
            )
        set_cached_response(response_cache_key, result)
        return result


def generate_metodologia_response(cliente_id: str, area: str) -> dict[str, Any]:
    query = f"Metodologia de auditoria para area {area}. Indica riesgos, pruebas y norma aplicable."
    chunks = _retrieve_chunks(cliente_id, query, top_k=6)
    try:
        if chunks:
            return _llm_answer(query, chunks, mode="metodologia", cliente_id=cliente_id)
    except Exception:
        pass
    return _fallback_answer(query, cliente_id, chunks, mode="metodologia")


def generate_judgement_response(cliente_id: str, query: str, *, mode: str = "judgement_risk") -> dict[str, Any]:
    chunks = _retrieve_chunks(cliente_id, query, top_k=8)
    try:
        if chunks:
            return _llm_answer(query, chunks, mode=mode, cliente_id=cliente_id)
    except Exception:
        pass
    return _fallback_answer(query, cliente_id, chunks, mode=mode)

