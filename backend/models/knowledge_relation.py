from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from backend.models import Base


class KnowledgeRelation(Base):
    __tablename__ = "knowledge_relations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(String(255), nullable=False, index=True)

    relation_type = Column(String(64), nullable=False, index=True)
    from_entity_id = Column(Integer, ForeignKey("knowledge_entities.id", ondelete="CASCADE"), nullable=False, index=True)
    to_entity_id = Column(Integer, ForeignKey("knowledge_entities.id", ondelete="CASCADE"), nullable=False, index=True)

    weight = Column(Float, nullable=False, default=1.0)
    metadata_json = Column(JSON, default=dict)

    source_module = Column(String(100), nullable=True, index=True)
    source_id = Column(String(255), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "cliente_id",
            "relation_type",
            "from_entity_id",
            "to_entity_id",
            "source_module",
            "source_id",
            name="uq_knowledge_relations_source_key",
        ),
    )
