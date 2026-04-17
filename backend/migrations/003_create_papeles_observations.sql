-- Migration: Create workpapers_observations table
-- Fecha: 2026-04-16
-- Descripcion: Tabla para observaciones por papel (Junior, Senior, Socio) con historial completo

CREATE TABLE IF NOT EXISTS workpapers_observations (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL,                      -- FK a workpapers_files
    codigo_papel VARCHAR(10) NOT NULL,             -- ej: 130.03 (qué papel)

    -- OBSERVACIÓN JUNIOR
    junior_observation TEXT,                       -- Lo que encontró
    junior_by VARCHAR(100),                        -- Usuario
    junior_at TIMESTAMP,                           -- Cuándo escribió
    junior_status VARCHAR(20),                     -- PENDIENTE, ESCRITO, etc.

    -- REVISIÓN SENIOR
    senior_review VARCHAR(50),                     -- APROBADO, RECHAZADO, PENDIENTE_ACLARACION, NO_APLICA
    senior_comment TEXT,                           -- Por qué rechaza/quita/modifica
    senior_by VARCHAR(100),                        -- Usuario
    senior_at TIMESTAMP,                           -- Cuándo revisó

    -- REVISIÓN SOCIO
    socio_review VARCHAR(50),                      -- FINALIZADO, REVISAR, NO_APLICA
    socio_comment TEXT,                            -- Faltó esto, resuelto aquí, etc.
    socio_by VARCHAR(100),                         -- Usuario
    socio_at TIMESTAMP,                            -- Cuándo finalizó

    -- ESTADO FINAL
    status VARCHAR(50) DEFAULT 'PENDIENTE',        -- PENDIENTE, APROBADO, RECHAZADO, NO_APLICA, FINALIZADO

    -- TRAZABILIDAD
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (file_id) REFERENCES workpapers_files(id) ON DELETE CASCADE,
    INDEX idx_file_id (file_id),
    INDEX idx_codigo_papel (codigo_papel),
    INDEX idx_status (status)
);

-- Historial de cambios de observaciones
CREATE TABLE IF NOT EXISTS workpapers_observation_history (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER NOT NULL,               -- FK a workpapers_observations
    rol VARCHAR(20) NOT NULL,                      -- junior, senior, socio
    accion VARCHAR(100) NOT NULL,                  -- escribio, aprobó, rechazó, comentó, finalizó
    contenido_anterior TEXT,                       -- Qué había antes
    contenido_nuevo TEXT,                          -- Qué hay ahora
    usuario VARCHAR(100) NOT NULL,                 -- Quién hizo el cambio
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (observation_id) REFERENCES workpapers_observations(id) ON DELETE CASCADE,
    INDEX idx_observation_id (observation_id),
    INDEX idx_rol_accion (rol, accion)
);
