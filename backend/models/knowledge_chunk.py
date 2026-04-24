from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from backend.models import Base


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(String(255), nullable=False, index=True)
    entity_id = Column(Integer, ForeignKey("knowledge_entities.id", ondelete="CASCADE"), nullable=True, index=True)

    chunk_type = Column(String(64), nullable=False, default="entity_text")
    text_content = Column(Text, nullable=False)
    chunk_hash = Column(String(64), nullable=False, index=True)

    source_module = Column(String(100), nullable=True, index=True)
    source_id = Column(String(255), nullable=True, index=True)
    metadata_json = Column(JSON, default=dict)

    embedding_model = Column(String(128), nullable=True)
    embedding_vector = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "cliente_id",
            "chunk_hash",
            "source_module",
            "source_id",
            name="uq_knowledge_chunks_hash_source",
        ),
    )
