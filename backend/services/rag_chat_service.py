from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_ROOT = ROOT / "data" / "conocimiento_normativo"
CLIENTES_ROOT = ROOT / "data" / "clientes"


@dataclass
class RetrievedChunk:
    source: str
    excerpt: str
    score: int


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if len(t) > 2]


def _load_markdown_sources() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if not KNOWLEDGE_ROOT.exists():
        return out
    for path in KNOWLEDGE_ROOT.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8").strip()
        except Exception:
            continue
        if not text:
            continue
        out.append((str(path.relative_to(ROOT)), text))
    return out


def _load_client_context(cliente_id: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    perfil_path = CLIENTES_ROOT / cliente_id / "perfil.yaml"
    hallazgos_path = CLIENTES_ROOT / cliente_id / "hallazgos.md"

    if perfil_path.exists():
        try:
            data = yaml.safe_load(perfil_path.read_text(encoding="utf-8")) or {}
            out.append((str(perfil_path.relative_to(ROOT)), yaml.safe_dump(data, allow_unicode=True, sort_keys=False)))
        except Exception:
            pass
    if hallazgos_path.exists():
        try:
            text = hallazgos_path.read_text(encoding="utf-8").strip()
            if text:
                out.append((str(hallazgos_path.relative_to(ROOT)), text))
        except Exception:
            pass
    return out


def _split_chunks(source: str, text: str) -> list[tuple[str, str]]:
    chunks: list[tuple[str, str]] = []
    parts = re.split(r"\n\s*\n", text)
    for part in parts:
        cleaned = part.strip()
        if len(cleaned) < 40:
            continue
        if len(cleaned) > 1100:
            cleaned = cleaned[:1100]
        chunks.append((source, cleaned))
    return chunks


def _retrieve_chunks(cliente_id: str, query: str, *, top_k: int = 5) -> list[RetrievedChunk]:
    query_tokens = set(_tokenize(query))
    if not query_tokens:
        return []

    raw_docs = _load_markdown_sources() + _load_client_context(cliente_id)
    candidates: list[RetrievedChunk] = []
    for source, text in raw_docs:
        for chunk_source, chunk in _split_chunks(source, text):
            tokens = set(_tokenize(chunk))
            score = len(query_tokens.intersection(tokens))
            if score <= 0:
                continue
            candidates.append(RetrievedChunk(source=chunk_source, excerpt=chunk, score=score))
    candidates.sort(key=lambda x: x.score, reverse=True)
    return candidates[:top_k]


def _fallback_answer(query: str, cliente_id: str, chunks: list[RetrievedChunk]) -> dict[str, Any]:
    sources = [c.source for c in chunks]
    first_context = chunks[0].excerpt[:240] if chunks else "Sin contexto recuperado."
    return {
        "answer": (
            f"[Socio AI RAG - fallback] Consulta: '{query}'. "
            f"Cliente: {cliente_id}. Analiza la normativa aplicable y valida evidencia con base en fuentes recuperadas."
            f"\n\nContexto clave: {first_context}"
        ),
        "citations": [{"source": c.source, "excerpt": c.excerpt[:220]} for c in chunks],
        "context_sources": sources,
        "confidence": 0.42 if chunks else 0.18,
    }


def _openai_answer(query: str, chunks: list[RetrievedChunk], *, mode: str = "chat") -> dict[str, Any]:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no configurada")

    from openai import OpenAI

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    client = OpenAI(api_key=api_key)

    joined_context = "\n\n".join([f"[{c.source}] {c.excerpt}" for c in chunks[:6]])
    instruction = (
        "Eres Socio AI, asistente de auditoria NIIF/NIA. Responde en espanol tecnico y concreto."
        " Cita las fuentes por nombre de archivo cuando afirmes un criterio."
        " Si falta contexto, dilo claramente."
    )
    if mode == "metodologia":
        instruction += " Enfocate en metodologia de auditoria y procedimiento aplicable por area."

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": instruction},
            {
                "role": "user",
                "content": (
                    f"Consulta:\n{query}\n\n"
                    f"Contexto recuperado:\n{joined_context}\n\n"
                    "Devuelve recomendacion accionable y breve lista de evidencias a revisar."
                ),
            },
        ],
        temperature=0.2,
    )

    text = getattr(response, "output_text", "") or ""
    if not text.strip():
        text = "No se obtuvo respuesta del modelo."

    return {
        "answer": text.strip(),
        "citations": [{"source": c.source, "excerpt": c.excerpt[:220]} for c in chunks],
        "context_sources": [c.source for c in chunks],
        "confidence": 0.72 if chunks else 0.35,
    }


def generate_chat_response(cliente_id: str, query: str) -> dict[str, Any]:
    chunks = _retrieve_chunks(cliente_id, query, top_k=6)
    try:
        if chunks:
            return _openai_answer(query, chunks, mode="chat")
    except Exception:
        pass
    return _fallback_answer(query, cliente_id, chunks)


def generate_metodologia_response(cliente_id: str, area: str) -> dict[str, Any]:
    query = f"Metodologia de auditoria para area {area}. Indica riesgos, pruebas y norma aplicable."
    chunks = _retrieve_chunks(cliente_id, query, top_k=6)
    try:
        if chunks:
            return _openai_answer(query, chunks, mode="metodologia")
    except Exception:
        pass
    return _fallback_answer(query, cliente_id, chunks)
