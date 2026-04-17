-- Migration: Create workpapers_templates table
-- Fecha: 2026-04-16
-- Descripcion: Tabla de papeles de trabajo clasificados por aseveración, importancia y línea de cuenta

CREATE TABLE IF NOT EXISTS workpapers_templates (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE NOT NULL,  -- ej: 130.03
    numero VARCHAR(5) NOT NULL,           -- ej: 03
    ls INTEGER NOT NULL,                  -- ej: 130 (línea de cuenta)
    nombre VARCHAR(255) NOT NULL,         -- ej: "Conciliación cuentas por cobrar"
    aseveracion VARCHAR(50) NOT NULL,     -- ej: EXISTENCIA, INTEGRIDAD, VALORACION, etc.
    importancia VARCHAR(20) NOT NULL,     -- ej: CRITICO, ALTO, MEDIO, BAJO
    obligatorio VARCHAR(20) NOT NULL,     -- ej: SÍ, NO, CONDICIONAL
    descripcion TEXT,                     -- POR QUÉ se realiza (para Junior)
    archivo_original VARCHAR(500),        -- Ruta original del Excel

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_ls (ls),
    INDEX idx_aseveracion (aseveracion),
    INDEX idx_importancia (importancia)
);

-- Insertar índice compuesto para búsquedas por LS + importancia
CREATE INDEX IF NOT EXISTS idx_ls_importancia
ON workpapers_templates(ls, importancia DESC, codigo);
