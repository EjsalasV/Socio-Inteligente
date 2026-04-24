from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, UniqueConstraint

from backend.models import Base


class KnowledgeEntity(Base):
    __tablename__ = "knowledge_entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)

    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="active")

    source_module = Column(String(100), nullable=False, index=True)
    source_id = Column(String(255), nullable=False, index=True)
    source_ref = Column(String(512), nullable=True)

    metadata_json = Column(JSON, default=dict)
    tags_json = Column(JSON, default=list)
    confidence = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "cliente_id",
            "entity_type",
            "source_module",
            "source_id",
            name="uq_knowledge_entities_upsert_key",
        ),
    )
