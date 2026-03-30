from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from backend.services.prompt_service import render_prompt, validate_minimum_output

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_ROOT = ROOT / "data" / "conocimiento_normativo"
CLIENTES_ROOT = ROOT / "data" / "clientes"


@dataclass
class RetrievedChunk:
    source: str
    excerpt: str
    score: int
    metadata: dict[str, str]


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if len(t) > 2]


def _parse_frontmatter(markdown: str) -> tuple[dict[str, str], str]:
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
            meta = {str(k): str(v) for k, v in loaded.items() if v is not None}
            return meta, body
    except Exception:
        pass
    return {}, markdown


def _default_metadata(relative_source: str, file_path: Path) -> dict[str, str]:
    lower = relative_source.lower()
    if "/nias/" in lower:
        norma = "NIA"
        jurisdiccion = "Internacional"
    elif "/niif_pymes/" in lower:
        norma = "NIIF PYMES"
        jurisdiccion = "Internacional"
    elif "/niif_completas/" in lower:
        norma = "NIIF"
        jurisdiccion = "Internacional"
    elif "/tributario_ec/" in lower:
        norma = "Tributario"
        jurisdiccion = "Ecuador"
    elif "/supercias/" in lower:
        norma = "SUPERCIAS"
        jurisdiccion = "Ecuador"
    else:
        norma = "Metodologia"
        jurisdiccion = "Interna"

    updated = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).date().isoformat()
    return {
        "norma": norma,
        "version": "v1",
        "vigente_desde": "",
        "ultima_actualizacion": updated,
        "reemplaza_a": "",
        "jurisdiccion": jurisdiccion,
    }


def _normalize_metadata(relative_source: str, file_path: Path, raw_meta: dict[str, str]) -> dict[str, str]:
    meta = _default_metadata(relative_source, file_path)
    for key in ["norma", "version", "vigente_desde", "ultima_actualizacion", "reemplaza_a", "jurisdiccion"]:
        value = str(raw_meta.get(key, "")).strip() if isinstance(raw_meta, dict) else ""
        if value:
            meta[key] = value
    return meta


def _load_markdown_sources() -> list[tuple[str, str, dict[str, str]]]:
    out: list[tuple[str, str, dict[str, str]]] = []
    if not KNOWLEDGE_ROOT.exists():
        return out
    for path in KNOWLEDGE_ROOT.rglob("*.md"):
        try:
            raw_text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        raw_meta, text = _parse_frontmatter(raw_text)
        text = text.strip()
        if not text:
            continue
        rel = str(path.relative_to(ROOT))
        metadata = _normalize_metadata(rel, path, raw_meta)
        out.append((rel, text, metadata))
    return out


def _load_client_context(cliente_id: str) -> list[tuple[str, str, dict[str, str]]]:
    out: list[tuple[str, str, dict[str, str]]] = []
    perfil_path = CLIENTES_ROOT / cliente_id / "perfil.yaml"
    hallazgos_path = CLIENTES_ROOT / cliente_id / "hallazgos.md"
    docs_text_dir = CLIENTES_ROOT / cliente_id / "documentos_text"

    base_meta = {
        "norma": "Contexto cliente",
        "version": "v1",
        "vigente_desde": "",
        "ultima_actualizacion": "",
        "reemplaza_a": "",
        "jurisdiccion": "Interna",
    }

    if perfil_path.exists():
        try:
            data = yaml.safe_load(perfil_path.read_text(encoding="utf-8")) or {}
            rel = str(perfil_path.relative_to(ROOT))
            meta = dict(base_meta)
            meta["ultima_actualizacion"] = datetime.fromtimestamp(perfil_path.stat().st_mtime, tz=timezone.utc).date().isoformat()
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
            out.append((rel, text, meta))
    return out


def _split_chunks(source: str, text: str, metadata: dict[str, str]) -> list[tuple[str, str, dict[str, str]]]:
    chunks: list[tuple[str, str, dict[str, str]]] = []
    parts = re.split(r"\n\s*\n", text)
    for part in parts:
        cleaned = part.strip()
        if len(cleaned) < 40:
            continue
        if len(cleaned) > 1100:
            cleaned = cleaned[:1100]
        chunks.append((source, cleaned, metadata))
    return chunks


def _retrieve_chunks(cliente_id: str, query: str, *, top_k: int = 5) -> list[RetrievedChunk]:
    query_tokens = set(_tokenize(query))
    if not query_tokens:
        return []

    raw_docs = _load_markdown_sources() + _load_client_context(cliente_id)
    candidates: list[RetrievedChunk] = []
    for source, text, metadata in raw_docs:
        for chunk_source, chunk, chunk_meta in _split_chunks(source, text, metadata):
            tokens = set(_tokenize(chunk))
            score = len(query_tokens.intersection(tokens))
            if score <= 0:
                continue
            candidates.append(RetrievedChunk(source=chunk_source, excerpt=chunk, score=score, metadata=chunk_meta))
    candidates.sort(key=lambda x: x.score, reverse=True)
    return candidates[:top_k]


def retrieve_context_chunks(cliente_id: str, query: str, *, top_k: int = 6) -> list[dict[str, Any]]:
    chunks = _retrieve_chunks(cliente_id, query, top_k=top_k)
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
    return out


def _fallback_answer(query: str, cliente_id: str, chunks: list[RetrievedChunk]) -> dict[str, Any]:
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
    return {
        "answer": (
            f"[Socio AI RAG - fallback] Consulta: '{query}'. "
            f"Cliente: {cliente_id}. Analiza la normativa aplicable y valida evidencia con base en fuentes recuperadas."
            f"\n\nContexto clave: {first_context}"
        ),
        "citations": citations,
        "context_sources": sources,
        "confidence": 0.42 if chunks else 0.18,
        "prompt_meta": {"prompt_id": "fallback", "prompt_version": "v1"},
    }


def _llm_answer(query: str, chunks: list[RetrievedChunk], *, mode: str = "chat") -> dict[str, Any]:
    provider = (os.getenv("AI_PROVIDER") or "openai").strip().lower()
    from openai import OpenAI

    if provider == "deepseek":
        api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY no configurada")
        model = os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat").strip() or "deepseek-chat"
        base_url = (os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").strip()
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY no configurada")
        model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        client = OpenAI(api_key=api_key)

    joined_context = "\n\n".join(
        [
            f"[{c.source}] ({c.metadata.get('norma', 'N/A')} | vigente: {c.metadata.get('vigente_desde', 'N/D')} | "
            f"actualizacion: {c.metadata.get('ultima_actualizacion', 'N/D')}) {c.excerpt}"
            for c in chunks[:6]
        ]
    )
    instruction, prompt_meta = render_prompt(mode, query=query, context=joined_context)

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": instruction},
            {
                "role": "user",
                "content": (
                    f"Consulta:\n{query}\n\n"
                    "Devuelve recomendacion accionable con criterio, pasos y evidencia."
                ),
            },
        ],
        temperature=0.2,
    )

    text = getattr(response, "output_text", "") or ""
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
        "answer": text.strip(),
        "citations": citations,
        "context_sources": [c.source for c in chunks],
        "confidence": 0.72 if chunks else 0.35,
        "provider": provider,
        "model": model,
        "prompt_meta": prompt_meta,
    }


def generate_chat_response(cliente_id: str, query: str) -> dict[str, Any]:
    chunks = _retrieve_chunks(cliente_id, query, top_k=6)
    try:
        if chunks:
            return _llm_answer(query, chunks, mode="chat")
    except Exception:
        pass
    return _fallback_answer(query, cliente_id, chunks)


def generate_metodologia_response(cliente_id: str, area: str) -> dict[str, Any]:
    query = f"Metodologia de auditoria para area {area}. Indica riesgos, pruebas y norma aplicable."
    chunks = _retrieve_chunks(cliente_id, query, top_k=6)
    try:
        if chunks:
            return _llm_answer(query, chunks, mode="metodologia")
    except Exception:
        pass
    return _fallback_answer(query, cliente_id, chunks)


def generate_judgement_response(cliente_id: str, query: str, *, mode: str = "judgement_risk") -> dict[str, Any]:
    chunks = _retrieve_chunks(cliente_id, query, top_k=8)
    try:
        if chunks:
            return _llm_answer(query, chunks, mode=mode)
    except Exception:
        pass
    return _fallback_answer(query, cliente_id, chunks)
