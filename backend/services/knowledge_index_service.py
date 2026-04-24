from __future__ import annotations

import hashlib
import re
from typing import Any

from sqlalchemy import or_

from backend.models.knowledge_chunk import KnowledgeChunk
from backend.models.knowledge_entity import KnowledgeEntity


def _tokenize(text: str) -> list[str]:
    clean = re.sub(r"[^\w\s]+", " ", str(text or "").lower())
    tokens = [t for t in clean.split() if len(t) >= 2]
    return tokens[:30]


def build_chunk_hash(*, cliente_id: str, entity_id: int | None, text_content: str, source_module: str, source_id: str) -> str:
    raw = "|".join([
        str(cliente_id or ""),
        str(entity_id or ""),
        str(source_module or ""),
        str(source_id or ""),
        str(text_content or ""),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _entity_text_payload(entity: KnowledgeEntity) -> str:
    bits: list[str] = []
    if entity.title:
        bits.append(str(entity.title))
    if entity.content:
        bits.append(str(entity.content))
    if isinstance(entity.tags_json, list) and entity.tags_json:
        bits.append("tags: " + ", ".join([str(x) for x in entity.tags_json if str(x).strip()]))
    if isinstance(entity.metadata_json, dict) and entity.metadata_json:
        meta_pairs = [f"{k}={v}" for k, v in entity.metadata_json.items()]
        bits.append("metadata: " + "; ".join(meta_pairs))
    joined = "\n".join([b for b in bits if b.strip()])
    return joined.strip() or f"entity:{entity.entity_type}:{entity.id}"


def upsert_entity_chunk(session: Any, entity: KnowledgeEntity) -> tuple[KnowledgeChunk, bool]:
    text_content = _entity_text_payload(entity)
    chunk_hash = build_chunk_hash(
        cliente_id=entity.cliente_id,
        entity_id=entity.id,
        text_content=text_content,
        source_module=entity.source_module,
        source_id=entity.source_id,
    )

    existing = (
        session.query(KnowledgeChunk)
        .filter(
            KnowledgeChunk.cliente_id == entity.cliente_id,
            KnowledgeChunk.chunk_hash == chunk_hash,
            KnowledgeChunk.source_module == entity.source_module,
            KnowledgeChunk.source_id == entity.source_id,
        )
        .first()
    )
    if existing:
        existing.entity_id = entity.id
        existing.text_content = text_content
        existing.chunk_type = "entity_text"
        existing.metadata_json = {
            "entity_type": entity.entity_type,
            "entity_id": entity.id,
            "source_module": entity.source_module,
            "source_id": entity.source_id,
        }
        session.flush()
        return existing, False

    chunk = KnowledgeChunk(
        cliente_id=entity.cliente_id,
        entity_id=entity.id,
        chunk_type="entity_text",
        text_content=text_content,
        chunk_hash=chunk_hash,
        source_module=entity.source_module,
        source_id=entity.source_id,
        metadata_json={
            "entity_type": entity.entity_type,
            "entity_id": entity.id,
            "source_module": entity.source_module,
            "source_id": entity.source_id,
        },
        embedding_model=None,
        embedding_vector=None,
    )
    session.add(chunk)
    session.flush()
    return chunk, True


def search_chunks_text(session: Any, cliente_id: str, query: str, *, top_k: int = 8) -> list[dict[str, Any]]:
    q = str(query or "").strip()
    if not q:
        return []

    tokens = _tokenize(q)
    if not tokens:
        return []

    conditions = [KnowledgeChunk.text_content.ilike(f"%{token}%") for token in tokens]
    rows = (
        session.query(KnowledgeChunk)
        .filter(KnowledgeChunk.cliente_id == cliente_id)
        .filter(or_(*conditions))
        .limit(500)
        .all()
    )

    ranked: list[dict[str, Any]] = []
    for row in rows:
        text = str(row.text_content or "").lower()
        score = 0.0
        for token in tokens:
            score += text.count(token) * 1.0
        if q.lower() in text:
            score += 2.5
        if score <= 0:
            continue
        ranked.append(
            {
                "chunk_id": int(row.id),
                "entity_id": int(row.entity_id) if row.entity_id is not None else None,
                "text": str(row.text_content or "")[:400],
                "source_module": str(row.source_module or ""),
                "source_id": str(row.source_id or ""),
                "score": float(score),
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[: max(1, min(int(top_k), 20))]


def ask_knowledge(session: Any, cliente_id: str, query: str, *, top_k: int = 5) -> dict[str, Any]:
    matches = search_chunks_text(session, cliente_id, query, top_k=top_k)
    if not matches:
        return {
            "query": query,
            "answer": "No encontré contexto relevante en Knowledge Core para esta consulta.",
            "sources": [],
            "matched_chunks": [],
        }

    entity_ids = [m["entity_id"] for m in matches if m.get("entity_id") is not None]
    entities: dict[int, KnowledgeEntity] = {}
    if entity_ids:
        rows = (
            session.query(KnowledgeEntity)
            .filter(KnowledgeEntity.cliente_id == cliente_id)
            .filter(KnowledgeEntity.id.in_(entity_ids))
            .all()
        )
        entities = {int(r.id): r for r in rows}

    sources: list[dict[str, Any]] = []
    for match in matches:
        ent = entities.get(int(match["entity_id"])) if match.get("entity_id") is not None else None
        sources.append(
            {
                "entity_id": int(ent.id) if ent else None,
                "entity_type": str(ent.entity_type) if ent else "",
                "title": str(ent.title or "") if ent else "",
                "source_module": str(match.get("source_module") or ""),
                "source_id": str(match.get("source_id") or ""),
                "score": float(match.get("score") or 0.0),
                "excerpt": str(match.get("text") or ""),
            }
        )

    headline = sources[0]
    answer = (
        "Encontré evidencia textual relacionada en Knowledge Core. "
        f"La fuente más relevante es `{headline.get('title') or headline.get('entity_type')}` "
        f"(módulo {headline.get('source_module')}, score {headline.get('score'):.2f})."
    )

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "matched_chunks": matches,
    }
