from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String

from backend.models import Base


class KnowledgeEvent(Base):
    __tablename__ = "knowledge_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(String(255), nullable=False, index=True)

    event_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(Integer, ForeignKey("knowledge_entities.id", ondelete="SET NULL"), nullable=True, index=True)
    relation_id = Column(Integer, ForeignKey("knowledge_relations.id", ondelete="SET NULL"), nullable=True, index=True)
    chunk_id = Column(Integer, ForeignKey("knowledge_chunks.id", ondelete="SET NULL"), nullable=True, index=True)

    source_module = Column(String(100), nullable=True, index=True)
    source_id = Column(String(255), nullable=True, index=True)
    payload_json = Column(JSON, default=dict)

    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
