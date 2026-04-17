-- Migration: Create workpapers_templates table
-- Fecha: 2026-04-16
-- Descripcion: Tabla de papeles de trabajo clasificados por aseveración, importancia y línea de cuenta

CREATE TABLE IF NOT EXISTS workpapers_templates (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE NOT NULL,
    numero VARCHAR(5) NOT NULL,
    ls INTEGER NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    aseveracion VARCHAR(50) NOT NULL,
    importancia VARCHAR(20) NOT NULL,
    obligatorio VARCHAR(20) NOT NULL,
    descripcion TEXT,
    archivo_original VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ls ON workpapers_templates(ls);
CREATE INDEX IF NOT EXISTS idx_aseveracion ON workpapers_templates(aseveracion);
CREATE INDEX IF NOT EXISTS idx_importancia ON workpapers_templates(importancia);
CREATE INDEX IF NOT EXISTS idx_ls_importancia ON workpapers_templates(ls, importancia, codigo);
