from __future__ import annotations

import os
from typing import Any

from fastapi import status

from backend.models.knowledge_entity import KnowledgeEntity
from backend.models.knowledge_event import KnowledgeEvent
from backend.models.knowledge_relation import KnowledgeRelation
from backend.services.knowledge_index_service import ask_knowledge, upsert_entity_chunk
from backend.utils.api_errors import raise_api_error

VALID_ENTITY_TYPES = {
    "client",
    "area",
    "risk",
    "finding",
    "working_paper",
    "evidence",
    "document",
    "ledger_movement",
    "trial_balance_account",
    "note",
    "decision",
    "standard",
    "report_section",
    "chat_insight",
}

VALID_RELATION_TYPES = {
    "supports",
    "contradicts",
    "explains",
    "belongs_to",
    "evidences",
    "references",
    "derived_from",
    "related_to",
    "impacts",
    "mitigates",
    "requires_followup",
}


def knowledge_core_enabled() -> bool:
    raw = str(os.getenv("KNOWLEDGE_CORE_ENABLED") or "0").strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def ensure_knowledge_core_enabled() -> None:
    if knowledge_core_enabled():
        return
    raise_api_error(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="KNOWLEDGE_CORE_DISABLED",
        message="Knowledge Core está desactivado en este entorno.",
        action_hint="Activa KNOWLEDGE_CORE_ENABLED=1 para habilitar estos endpoints.",
        retryable=False,
        details={"enabled": False},
    )


def _clean_text(value: Any, *, max_len: int = 10000) -> str:
    text = str(value or "").strip()
    if len(text) > max_len:
        return text[:max_len]
    return text


def _normalize_tags(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        txt = str(item or "").strip()
        if txt:
            out.append(txt)
    return out[:50]


def record_event(
    session: Any,
    *,
    cliente_id: str,
    event_type: str,
    entity_id: int | None = None,
    relation_id: int | None = None,
    chunk_id: int | None = None,
    source_module: str | None = None,
    source_id: str | None = None,
    payload_json: dict[str, Any] | None = None,
    created_by: str | None = None,
) -> KnowledgeEvent:
    event = KnowledgeEvent(
        cliente_id=cliente_id,
        event_type=_clean_text(event_type, max_len=64),
        entity_id=entity_id,
        relation_id=relation_id,
        chunk_id=chunk_id,
        source_module=_clean_text(source_module, max_len=100) if source_module else None,
        source_id=_clean_text(source_id, max_len=255) if source_id else None,
        payload_json=payload_json or {},
        created_by=_clean_text(created_by, max_len=255) if created_by else None,
    )
    session.add(event)
    session.flush()
    return event


def _entity_to_dict(entity: KnowledgeEntity) -> dict[str, Any]:
    return {
        "id": int(entity.id),
        "cliente_id": str(entity.cliente_id),
        "entity_type": str(entity.entity_type),
        "title": str(entity.title or ""),
        "content": str(entity.content or ""),
        "status": str(entity.status or "active"),
        "source_module": str(entity.source_module),
        "source_id": str(entity.source_id),
        "source_ref": str(entity.source_ref or ""),
        "metadata": entity.metadata_json if isinstance(entity.metadata_json, dict) else {},
        "tags": entity.tags_json if isinstance(entity.tags_json, list) else [],
        "confidence": float(entity.confidence) if entity.confidence is not None else None,
        "created_at": entity.created_at.isoformat() if entity.created_at else "",
        "updated_at": entity.updated_at.isoformat() if entity.updated_at else "",
    }


def upsert_entity(session: Any, payload: dict[str, Any], *, actor: str = "") -> dict[str, Any]:
    cliente_id = _clean_text(payload.get("cliente_id"), max_len=255)
    entity_type = _clean_text(payload.get("entity_type"), max_len=64)
    source_module = _clean_text(payload.get("source_module"), max_len=100)
    source_id = _clean_text(payload.get("source_id"), max_len=255)

    if not cliente_id:
        raise_api_error(code="VALIDATION_ERROR", message="cliente_id es obligatorio.")
    if entity_type not in VALID_ENTITY_TYPES:
        raise_api_error(code="VALIDATION_ERROR", message="entity_type no soportado.", details={"entity_type": entity_type})
    if not source_module or not source_id:
        raise_api_error(code="VALIDATION_ERROR", message="source_module y source_id son obligatorios.")

    existing = (
        session.query(KnowledgeEntity)
        .filter(
            KnowledgeEntity.cliente_id == cliente_id,
            KnowledgeEntity.entity_type == entity_type,
            KnowledgeEntity.source_module == source_module,
            KnowledgeEntity.source_id == source_id,
        )
        .first()
    )

    if existing:
        existing.title = _clean_text(payload.get("title"), max_len=255) or existing.title
        existing.content = _clean_text(payload.get("content"), max_len=20000)
        existing.status = _clean_text(payload.get("status"), max_len=32) or (existing.status or "active")
        existing.source_ref = _clean_text(payload.get("source_ref"), max_len=512)
        existing.metadata_json = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        existing.tags_json = _normalize_tags(payload.get("tags"))
        existing.confidence = float(payload.get("confidence")) if payload.get("confidence") is not None else None
        existing.updated_by = _clean_text(actor, max_len=255) if actor else None
        session.flush()

        chunk, chunk_created = upsert_entity_chunk(session, existing)
        record_event(
            session,
            cliente_id=cliente_id,
            event_type="entity_updated",
            entity_id=int(existing.id),
            chunk_id=int(chunk.id) if chunk else None,
            source_module=source_module,
            source_id=source_id,
            payload_json={"chunk_created": bool(chunk_created)},
            created_by=actor,
        )
        session.commit()
        return _entity_to_dict(existing)

    entity = KnowledgeEntity(
        cliente_id=cliente_id,
        entity_type=entity_type,
        title=_clean_text(payload.get("title"), max_len=255),
        content=_clean_text(payload.get("content"), max_len=20000),
        status=_clean_text(payload.get("status"), max_len=32) or "active",
        source_module=source_module,
        source_id=source_id,
        source_ref=_clean_text(payload.get("source_ref"), max_len=512),
        metadata_json=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        tags_json=_normalize_tags(payload.get("tags")),
        confidence=float(payload.get("confidence")) if payload.get("confidence") is not None else None,
        created_by=_clean_text(actor, max_len=255) if actor else None,
        updated_by=_clean_text(actor, max_len=255) if actor else None,
    )
    session.add(entity)
    session.flush()

    chunk, _chunk_created = upsert_entity_chunk(session, entity)
    record_event(
        session,
        cliente_id=cliente_id,
        event_type="entity_created",
        entity_id=int(entity.id),
        chunk_id=int(chunk.id) if chunk else None,
        source_module=source_module,
        source_id=source_id,
        payload_json={"entity_type": entity_type},
        created_by=actor,
    )
    session.commit()
    return _entity_to_dict(entity)


def list_entities(
    session: Any,
    *,
    cliente_id: str,
    entity_type: str | None = None,
    source_module: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    query = session.query(KnowledgeEntity).filter(KnowledgeEntity.cliente_id == cliente_id)

    if entity_type:
        query = query.filter(KnowledgeEntity.entity_type == entity_type)
    if source_module:
        query = query.filter(KnowledgeEntity.source_module == source_module)
    if q:
        term = f"%{str(q).strip()}%"
        query = query.filter((KnowledgeEntity.title.ilike(term)) | (KnowledgeEntity.content.ilike(term)))

    safe_page = max(1, int(page))
    safe_size = max(1, min(int(page_size), 200))

    total = int(query.count())
    items = (
        query.order_by(KnowledgeEntity.updated_at.desc())
        .offset((safe_page - 1) * safe_size)
        .limit(safe_size)
        .all()
    )
    total_pages = max(1, (total + safe_size - 1) // safe_size)

    return {
        "items": [_entity_to_dict(item) for item in items],
        "total": total,
        "page": safe_page,
        "page_size": safe_size,
        "total_pages": total_pages,
    }


def _relation_to_dict(relation: KnowledgeRelation) -> dict[str, Any]:
    return {
        "id": int(relation.id),
        "cliente_id": str(relation.cliente_id),
        "relation_type": str(relation.relation_type),
        "from_entity_id": int(relation.from_entity_id),
        "to_entity_id": int(relation.to_entity_id),
        "weight": float(relation.weight or 1.0),
        "metadata": relation.metadata_json if isinstance(relation.metadata_json, dict) else {},
        "source_module": str(relation.source_module or ""),
        "source_id": str(relation.source_id or ""),
        "created_at": relation.created_at.isoformat() if relation.created_at else "",
        "updated_at": relation.updated_at.isoformat() if relation.updated_at else "",
    }


def upsert_relation(session: Any, payload: dict[str, Any], *, actor: str = "") -> dict[str, Any]:
    cliente_id = _clean_text(payload.get("cliente_id"), max_len=255)
    relation_type = _clean_text(payload.get("relation_type"), max_len=64)

    if not cliente_id:
        raise_api_error(code="VALIDATION_ERROR", message="cliente_id es obligatorio.")
    if relation_type not in VALID_RELATION_TYPES:
        raise_api_error(code="VALIDATION_ERROR", message="relation_type no soportado.", details={"relation_type": relation_type})

    try:
        from_entity_id = int(payload.get("from_entity_id"))
        to_entity_id = int(payload.get("to_entity_id"))
    except Exception:
        raise_api_error(code="VALIDATION_ERROR", message="from_entity_id y to_entity_id deben ser enteros.")

    from_entity = session.query(KnowledgeEntity).filter(KnowledgeEntity.id == from_entity_id).first()
    to_entity = session.query(KnowledgeEntity).filter(KnowledgeEntity.id == to_entity_id).first()
    if not from_entity or not to_entity:
        raise_api_error(code="NOT_FOUND", message="Entidades origen/destino no encontradas.")
    if from_entity.cliente_id != cliente_id or to_entity.cliente_id != cliente_id:
        raise_api_error(code="VALIDATION_ERROR", message="Las entidades deben pertenecer al mismo cliente_id.")

    source_module = _clean_text(payload.get("source_module"), max_len=100)
    source_id = _clean_text(payload.get("source_id"), max_len=255)

    query = session.query(KnowledgeRelation).filter(
        KnowledgeRelation.cliente_id == cliente_id,
        KnowledgeRelation.relation_type == relation_type,
        KnowledgeRelation.from_entity_id == from_entity_id,
        KnowledgeRelation.to_entity_id == to_entity_id,
    )
    if source_module and source_id:
        query = query.filter(
            KnowledgeRelation.source_module == source_module,
            KnowledgeRelation.source_id == source_id,
        )
    existing = query.first()

    weight = float(payload.get("weight")) if payload.get("weight") is not None else 1.0
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}

    if existing:
        existing.weight = weight
        existing.metadata_json = metadata
        existing.source_module = source_module or existing.source_module
        existing.source_id = source_id or existing.source_id
        existing.updated_by = _clean_text(actor, max_len=255) if actor else None
        session.flush()
        record_event(
            session,
            cliente_id=cliente_id,
            event_type="relation_updated",
            relation_id=int(existing.id),
            source_module=existing.source_module,
            source_id=existing.source_id,
            payload_json={"from_entity_id": from_entity_id, "to_entity_id": to_entity_id},
            created_by=actor,
        )
        session.commit()
        return _relation_to_dict(existing)

    relation = KnowledgeRelation(
        cliente_id=cliente_id,
        relation_type=relation_type,
        from_entity_id=from_entity_id,
        to_entity_id=to_entity_id,
        weight=weight,
        metadata_json=metadata,
        source_module=source_module or None,
        source_id=source_id or None,
        created_by=_clean_text(actor, max_len=255) if actor else None,
        updated_by=_clean_text(actor, max_len=255) if actor else None,
    )
    session.add(relation)
    session.flush()
    record_event(
        session,
        cliente_id=cliente_id,
        event_type="relation_created",
        relation_id=int(relation.id),
        source_module=relation.source_module,
        source_id=relation.source_id,
        payload_json={"from_entity_id": from_entity_id, "to_entity_id": to_entity_id, "relation_type": relation_type},
        created_by=actor,
    )
    session.commit()
    return _relation_to_dict(relation)


def get_timeline(session: Any, *, cliente_id: str, limit: int = 100) -> dict[str, Any]:
    safe_limit = max(1, min(int(limit), 500))
    rows = (
        session.query(KnowledgeEvent)
        .filter(KnowledgeEvent.cliente_id == cliente_id)
        .order_by(KnowledgeEvent.created_at.desc())
        .limit(safe_limit)
        .all()
    )

    events = []
    for row in rows:
        events.append(
            {
                "id": int(row.id),
                "cliente_id": str(row.cliente_id),
                "event_type": str(row.event_type),
                "entity_id": int(row.entity_id) if row.entity_id is not None else None,
                "relation_id": int(row.relation_id) if row.relation_id is not None else None,
                "chunk_id": int(row.chunk_id) if row.chunk_id is not None else None,
                "source_module": str(row.source_module or ""),
                "source_id": str(row.source_id or ""),
                "payload": row.payload_json if isinstance(row.payload_json, dict) else {},
                "created_by": str(row.created_by or ""),
                "created_at": row.created_at.isoformat() if row.created_at else "",
            }
        )

    return {
        "items": events,
        "total": len(events),
    }


def ask_with_event(session: Any, *, cliente_id: str, query: str, actor: str = "", top_k: int = 5) -> dict[str, Any]:
    response = ask_knowledge(session, cliente_id, query, top_k=top_k)
    record_event(
        session,
        cliente_id=cliente_id,
        event_type="ask_query",
        payload_json={"query": query, "top_k": top_k, "sources_count": len(response.get("sources") or [])},
        created_by=actor,
    )
    session.commit()
    return response
