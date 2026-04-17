-- Migration: Link workpapers_observations to audits
-- Fecha: 2026-04-17
-- Descripcion: Vincula observaciones de papeles con auditorías específicas

-- Agregar columna audit_id a workpapers_observations (si no existe)
ALTER TABLE workpapers_observations
ADD COLUMN IF NOT EXISTS audit_id INTEGER;

-- Agregar foreign key a audits
ALTER TABLE workpapers_observations
ADD CONSTRAINT IF NOT EXISTS fk_observation_audit
FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE;

-- Crear índice para búsquedas rápidas por auditoría
CREATE INDEX IF NOT EXISTS idx_observations_audit_id ON workpapers_observations(audit_id);
