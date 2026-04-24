-- Migration: Create knowledge core tables
-- Fecha: 2026-04-24
-- Descripcion: Nucleo Inteligente de Auditoria (Fase 1 base pasiva)

CREATE TABLE IF NOT EXISTS knowledge_entities (
    id SERIAL PRIMARY KEY,
    cliente_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    title VARCHAR(255),
    content TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    source_module VARCHAR(100) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    source_ref VARCHAR(512),
    metadata_json JSONB DEFAULT '{}'::jsonb,
    tags_json JSONB DEFAULT '[]'::jsonb,
    confidence DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    CONSTRAINT uq_knowledge_entities_upsert_key
        UNIQUE (cliente_id, entity_type, source_module, source_id)
);

CREATE TABLE IF NOT EXISTS knowledge_relations (
    id SERIAL PRIMARY KEY,
    cliente_id VARCHAR(255) NOT NULL,
    relation_type VARCHAR(64) NOT NULL,
    from_entity_id INTEGER NOT NULL,
    to_entity_id INTEGER NOT NULL,
    weight DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    metadata_json JSONB DEFAULT '{}'::jsonb,
    source_module VARCHAR(100),
    source_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    CONSTRAINT fk_knowledge_rel_from FOREIGN KEY (from_entity_id) REFERENCES knowledge_entities(id) ON DELETE CASCADE,
    CONSTRAINT fk_knowledge_rel_to FOREIGN KEY (to_entity_id) REFERENCES knowledge_entities(id) ON DELETE CASCADE,
    CONSTRAINT uq_knowledge_relations_source_key
        UNIQUE (cliente_id, relation_type, from_entity_id, to_entity_id, source_module, source_id)
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id SERIAL PRIMARY KEY,
    cliente_id VARCHAR(255) NOT NULL,
    entity_id INTEGER,
    chunk_type VARCHAR(64) NOT NULL DEFAULT 'entity_text',
    text_content TEXT NOT NULL,
    chunk_hash VARCHAR(64) NOT NULL,
    source_module VARCHAR(100),
    source_id VARCHAR(255),
    metadata_json JSONB DEFAULT '{}'::jsonb,
    embedding_model VARCHAR(128),
    embedding_vector TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_knowledge_chunks_entity FOREIGN KEY (entity_id) REFERENCES knowledge_entities(id) ON DELETE CASCADE,
    CONSTRAINT uq_knowledge_chunks_hash_source
        UNIQUE (cliente_id, chunk_hash, source_module, source_id)
);

CREATE TABLE IF NOT EXISTS knowledge_events (
    id SERIAL PRIMARY KEY,
    cliente_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    entity_id INTEGER,
    relation_id INTEGER,
    chunk_id INTEGER,
    source_module VARCHAR(100),
    source_id VARCHAR(255),
    payload_json JSONB DEFAULT '{}'::jsonb,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_knowledge_events_entity FOREIGN KEY (entity_id) REFERENCES knowledge_entities(id) ON DELETE SET NULL,
    CONSTRAINT fk_knowledge_events_relation FOREIGN KEY (relation_id) REFERENCES knowledge_relations(id) ON DELETE SET NULL,
    CONSTRAINT fk_knowledge_events_chunk FOREIGN KEY (chunk_id) REFERENCES knowledge_chunks(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_knowledge_entities_cliente ON knowledge_entities(cliente_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_type ON knowledge_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_source ON knowledge_entities(source_module, source_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_relations_cliente ON knowledge_relations(cliente_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_type ON knowledge_relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_from_to ON knowledge_relations(from_entity_id, to_entity_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_cliente ON knowledge_chunks(cliente_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_entity ON knowledge_chunks(entity_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_hash ON knowledge_chunks(chunk_hash);

CREATE INDEX IF NOT EXISTS idx_knowledge_events_cliente ON knowledge_events(cliente_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_events_type ON knowledge_events(event_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_events_created_at ON knowledge_events(created_at DESC);
