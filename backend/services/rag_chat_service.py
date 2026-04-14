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
from backend.services.rag_cache_service import build_rag_cache_key, get_cached_chunks, set_cached_chunks
from backend.services.normativa_monitor_service import get_pending_normative_changes
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
}


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

    for key in ["norma", "tipo", "marco", "ultima_actualizacion"]:
        value = str(raw_meta.get(key, "")).strip()
        if value:
            meta[key] = value

    meta["activo"] = _as_bool(raw_meta.get("activo"), default=True)
    for list_key in ["areas_aplicables", "afirmaciones_relacionadas", "etapas", "temas"]:
        meta[list_key] = _as_str_list(raw_meta.get(list_key))

    source_name = Path(relative_source).name
    meta["fuente"] = f"{source_name} | {meta.get('norma', source_name)}"
    return meta


def _load_markdown_sources() -> list[tuple[str, str, dict[str, Any], bool]]:
    out: list[tuple[str, str, dict[str, Any], bool]] = []
    if not KNOWLEDGE_ROOT.exists():
        return out
    for path in KNOWLEDGE_ROOT.rglob("*.md"):
        if "_backup" in str(path):
            continue
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
    if docs_text_dir.exists():
        for path in sorted(docs_text_dir.glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8").strip()
            except Exception:
                continue
            if not text:
                continue
            rel = str(path.relative_to(ROOT))
            meta = dict(base_meta)
            meta["norma"] = "Documentacion cliente"
            meta["ultima_actualizacion"] = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date().isoformat()
            meta["fuente"] = f"{path.name} | Documentacion cliente"
            out.append((rel, text, meta))
    return out


def _split_chunks(source: str, text: str, metadata: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    chunks: list[tuple[str, str, dict[str, Any]]] = []
    parts = re.split(r"\n\s*\n", text)
    for part in parts:
        cleaned = part.strip()
        if len(cleaned) < 40:
            continue
        if len(cleaned) > 1100:
            cleaned = cleaned[:1100]
        chunks.append((source, cleaned, metadata))
    return chunks


def _build_normative_index(*, force: bool = False) -> dict[str, Any]:
    if RAG_INDEX_PATH.exists() and not force:
        try:
            return json.loads(RAG_INDEX_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    indexed_files = 0
    skipped_files = 0
    warnings = 0
    chunks: list[dict[str, Any]] = []

    for source, text, metadata, has_valid_frontmatter in _load_markdown_sources():
        if not has_valid_frontmatter:
            warnings += 1
        if not _as_bool(metadata.get("activo"), default=True):
            skipped_files += 1
            print(f"[SKIP] {source} (activo=false)")
            continue
        indexed_files += 1
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
        "index_version": "v2_metadata_filters",
        "indexed_files": indexed_files,
        "skipped_files": skipped_files,
        "warnings": warnings,
        "chunks": chunks,
    }
    RAG_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAG_INDEX_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
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
        return candidates[:top_k]

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
        "que informacion",
        "que datos",
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
    phase = str(workflow.get("current_phase") or encargo.get("fase_actual") or "planificacion").strip()

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
    docs_names = [str(d.get("name") or "") for d in docs if isinstance(d, dict)]
    has_tb = "tb.xlsx" in docs_names
    has_mayor = "mayor.xlsx" in docs_names
    hallazgos_count = len([x for x in hallazgos.splitlines() if x.strip().startswith("## ")])
    return (
        f"Cliente: {str(cliente.get('nombre_legal') or cliente_id)} | "
        f"Sector: {str(cliente.get('sector') or 'N/D')} | "
        f"Marco: {str(encargo.get('marco_referencial') or 'N/D')} | "
        f"Fase: {str(workflow.get('current_phase') or encargo.get('fase_actual') or 'planificacion')} | "
        f"TB: {'si' if has_tb else 'no'} | Mayor: {'si' if has_mayor else 'no'} | "
        f"Docs extra: {len([x for x in docs_names if x not in {'tb.xlsx', 'mayor.xlsx'}])} | "
        f"Hallazgos: {hallazgos_count}"
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
    all_warnings = "\n".join([w for w in [warning, pending_warning] if w.strip()]).strip()
    if not all_warnings:
        return answer
    return f"{answer.rstrip()}\n\n{all_warnings}"


def _fallback_answer(query: str, cliente_id: str, chunks: list[RetrievedChunk], *, mode: str = "chat") -> dict[str, Any]:
    sources = [c.source for c in chunks]
    first_context = chunks[0].excerpt[:240] if chunks else "Sin contexto recuperado."
    citations: list[dict[str, str]] = []
    for c in chunks:
        meta = c.metadata or {}
        citations.append(
            {
                "source": c.source,
                "excerpt": c.excerpt[:220],
                "norma": str(meta.get("norma") or ""),
                "version": str(meta.get("version") or ""),
                "vigente_desde": str(meta.get("vigente_desde") or ""),
                "ultima_actualizacion": str(meta.get("ultima_actualizacion") or ""),
                "jurisdiccion": str(meta.get("jurisdiccion") or ""),
            }
        )
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
            answer = (
                "Estoy respondiendo en modo de respaldo porque no hay LLM generativo activo.\n"
                f"Proveedor detectado: `{provider_label}`.\n\n"
                f"Consulta: `{query}`\n\n"
                f"{procedure_hint + chr(10) + chr(10) if procedure_hint else ''}"
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
    }


def _has_llm_credentials() -> bool:
    _provider, key = _resolved_provider()
    return bool(key)


def _llm_answer(query: str, chunks: list[RetrievedChunk], *, mode: str = "chat", cliente_id: str = "") -> dict[str, Any]:
    provider, api_key = _resolved_provider()
    from openai import OpenAI
    timeout_seconds_raw = float(os.getenv("LLM_TIMEOUT_SECONDS", "12"))
    timeout_seconds = max(5.0, min(timeout_seconds_raw, 60.0))

    if provider == "deepseek":
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY no configurada")
        model = os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat").strip() or "deepseek-chat"
        base_url = (os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").strip()
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_seconds)
    else:
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY no configurada")
        model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        client = OpenAI(api_key=api_key, timeout=timeout_seconds)

    joined_context = "\n\n".join(
        [
            f"[{c.source}] ({(c.metadata or {}).get('norma', 'N/A')} | "
            f"vigente: {(c.metadata or {}).get('vigente_desde', 'N/D')} | "
            f"actualizacion: {(c.metadata or {}).get('ultima_actualizacion', 'N/D')}) {c.excerpt}"
            for c in chunks[:6]
        ]
    )
    snapshot = _client_snapshot(cliente_id) if cliente_id else ""
    risk_snapshot = _risk_snapshot(cliente_id) if cliente_id else ""
    if snapshot:
        joined_context = f"[SNAPSHOT CLIENTE]\n{snapshot}\n\n{joined_context}".strip()
    if risk_snapshot:
        joined_context = f"{joined_context}\n\n[SNAPSHOT RIESGO]\n{risk_snapshot}".strip()
    instruction, prompt_meta = render_prompt(mode, query=query, context=joined_context)

    reasoning_hint = ""
    if _is_risk_why_question(query):
        reasoning_hint = (
            "\nAdemas: explica explicitamente por que ese nivel de riesgo es razonable, "
            "incluyendo causa, impacto y que evidencia faltaria para subir o bajar el nivel."
        )
    elif _is_risk_question(query):
        reasoning_hint = (
            "\nAdemas: no repitas solo el ranking; interpreta los datos y concluye con criterio auditor."
        )

    user_content = (
        f"Consulta:\n{query}\n\n"
        "Responde de forma conversacional, concreta y accionable para un auditor."
        + reasoning_hint
        if mode == "chat"
        else (
            f"Consulta:\n{query}\n\n"
            "Devuelve recomendacion accionable con criterio, pasos y evidencia."
        )
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": user_content},
        ],
        temperature=0.35 if mode == "chat" else 0.2,
        max_tokens=900,
    )

    text = ""
    if response.choices and response.choices[0].message:
        text = str(response.choices[0].message.content or "").strip()
    if not text.strip():
        text = "No se obtuvo respuesta del modelo."

    ok_min_output, missing = validate_minimum_output(text, mode=mode)
    if not ok_min_output:
        text = (
            f"{text.strip()}\n\n"
            "Nota de control de calidad: la respuesta no cumplio todos los componentes minimos esperados "
            f"({', '.join(missing)})."
        )

    citations: list[dict[str, str]] = []
    for c in chunks:
        meta = c.metadata or {}
        citations.append(
            {
                "source": c.source,
                "excerpt": c.excerpt[:220],
                "norma": str(meta.get("norma") or ""),
                "version": str(meta.get("version") or ""),
                "vigente_desde": str(meta.get("vigente_desde") or ""),
                "ultima_actualizacion": str(meta.get("ultima_actualizacion") or ""),
                "jurisdiccion": str(meta.get("jurisdiccion") or ""),
            }
        )

    return {
        "answer": _append_staleness_warning(text.strip(), chunks),
        "citations": citations,
        "context_sources": [c.source for c in chunks],
        "confidence": 0.72 if chunks else 0.35,
        "provider": provider,
        "model": model,
        "prompt_meta": prompt_meta,
        "mode_used": mode,
    }


def generate_chat_response(cliente_id: str, query: str) -> dict[str, Any]:
    # Respuestas de alto valor y baja latencia, siempre contextuales.
    if _is_data_inventory_question(query):
        return _inventory_answer(cliente_id)
    if _is_next_steps_question(query):
        return _next_steps_answer(cliente_id)
    if _is_payroll_question(query):
        return _payroll_tests_answer(cliente_id)

    chunks = _retrieve_chunks(cliente_id, query, top_k=6)
    if not _has_llm_credentials():
        if _is_risk_question(query):
            return _risk_answer(cliente_id, query)
        return _fallback_answer(query, cliente_id, chunks, mode="chat")

    try:
        if _is_risk_question(query):
            return _llm_answer(query, chunks, mode="judgement_risk", cliente_id=cliente_id)
        # En chat general intentamos LLM aun sin chunks para mantener experiencia conversacional.
        return _llm_answer(query, chunks, mode="chat", cliente_id=cliente_id)
    except Exception:
        if _is_risk_question(query):
            return _risk_answer(cliente_id, query)
        return _fallback_answer(query, cliente_id, chunks, mode="chat")


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
