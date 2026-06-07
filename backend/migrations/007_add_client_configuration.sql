-- Migration: Add client configuration fields and table
-- Fecha: 2026-06-06
-- Descripcion: Agregar campos de configuracion industria, tamano, normativa y tabla de respuestas dinamicas

-- 1. Agregar columnas faltantes a tabla clients (si no existen)
ALTER TABLE clients ADD COLUMN IF NOT EXISTS tamano VARCHAR(20);              -- PyME, Mediana, Grande
ALTER TABLE clients ADD COLUMN IF NOT EXISTS normativa VARCHAR(50) DEFAULT 'NIIF';  -- NIIF, NIIF PYMES, USGAP
ALTER TABLE clients ADD COLUMN IF NOT EXISTS tiene_mayor_2024 BOOLEAN DEFAULT FALSE;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS fecha_mayor_cargado TIMESTAMP;

-- 2. Crear tabla de configuracion de clientes por industria
CREATE TABLE IF NOT EXISTS cliente_configurations (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,                         -- FK a clients.id
    tipo_entidad VARCHAR(50) NOT NULL,                  -- BANCO, RETAIL, SERVICIOS, MANUFACTURA, HOLDING, SALUD, EDUCACION
    respuestas JSON,                                    -- Respuestas a preguntas dinamicas en formato JSON

    -- TRAZABILIDAD
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),

    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT idx_client_config_unique UNIQUE (client_id, tipo_entidad)
);

-- 3. Crear indices para performance
CREATE INDEX IF NOT EXISTS idx_cliente_configurations_client_id ON cliente_configurations(client_id);
CREATE INDEX IF NOT EXISTS idx_cliente_configurations_tipo_entidad ON cliente_configurations(tipo_entidad);
