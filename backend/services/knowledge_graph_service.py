from __future__ import annotations

from typing import Any

from backend.models.knowledge_entity import KnowledgeEntity
from backend.models.knowledge_relation import KnowledgeRelation


def build_graph(session: Any, cliente_id: str, *, max_entities: int = 500, max_relations: int = 1000) -> dict[str, Any]:
    entities = (
        session.query(KnowledgeEntity)
        .filter(KnowledgeEntity.cliente_id == cliente_id)
        .order_by(KnowledgeEntity.updated_at.desc())
        .limit(max(1, min(int(max_entities), 2000)))
        .all()
    )
    entity_ids = [int(e.id) for e in entities]

    if entity_ids:
        relations = (
            session.query(KnowledgeRelation)
            .filter(KnowledgeRelation.cliente_id == cliente_id)
            .filter(KnowledgeRelation.from_entity_id.in_(entity_ids))
            .filter(KnowledgeRelation.to_entity_id.in_(entity_ids))
            .order_by(KnowledgeRelation.updated_at.desc())
            .limit(max(1, min(int(max_relations), 5000)))
            .all()
        )
    else:
        relations = []

    nodes = [
        {
            "id": int(e.id),
            "entity_type": str(e.entity_type),
            "title": str(e.title or ""),
            "status": str(e.status or "active"),
            "source_module": str(e.source_module),
            "source_id": str(e.source_id),
            "updated_at": e.updated_at.isoformat() if e.updated_at else "",
        }
        for e in entities
    ]

    edges = [
        {
            "id": int(r.id),
            "relation_type": str(r.relation_type),
            "from_entity_id": int(r.from_entity_id),
            "to_entity_id": int(r.to_entity_id),
            "weight": float(r.weight or 1.0),
            "source_module": str(r.source_module or ""),
            "source_id": str(r.source_id or ""),
            "updated_at": r.updated_at.isoformat() if r.updated_at else "",
        }
        for r in relations
    ]

    return {
        "cliente_id": cliente_id,
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        },
    }
