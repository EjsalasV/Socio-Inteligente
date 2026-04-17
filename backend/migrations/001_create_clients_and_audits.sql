-- Migration: Create clients and audits tables
-- Fecha: 2026-04-17
-- Descripcion: Estructura base para persistencia de clientes y auditorías

-- Tabla de clientes (MEMORIA del sistema)
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) UNIQUE NOT NULL,              -- ID único del cliente (ej: bustamante_fabara_ip_cl)
    nombre VARCHAR(255) NOT NULL,                       -- Nombre del cliente
    ruc VARCHAR(20),                                    -- RUC/NIT
    sector VARCHAR(100),                                -- Sector (auditoría financiera, integral, etc)
    tipo_entidad VARCHAR(50),                           -- Tipo: SOCIEDAD COMERCIAL, ONG, PÚBLICA, etc

    -- CONTACTO
    contacto_nombre VARCHAR(100),
    contacto_email VARCHAR(100),
    contacto_telefono VARCHAR(20),

    -- AUDITORÍA CONFIG
    moneda VARCHAR(10) DEFAULT 'COP',                   -- Moneda operacional
    materialidad_general DECIMAL(15,2),                 -- Materialidad general en moneda
    materialidad_procedimiento DECIMAL(15,2),           -- Materialidad para procedimientos

    -- PERÍODO ACTUAL
    periodo_actual VARCHAR(10),                         -- Ej: "2025" o "2025-12"
    fecha_cierre DATE,                                  -- Fecha de cierre de período
    estado VARCHAR(20) DEFAULT 'ACTIVO',                -- ACTIVO, EN_AUDITORÍA, FINALIZADO, ARCHIVADO

    -- TRAZABILIDAD
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    CONSTRAINT idx_client_id UNIQUE (client_id)
);

-- Tabla de auditorías (por cliente, puede haber múltiples períodos)
CREATE TABLE IF NOT EXISTS audits (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,                         -- FK a clients
    codigo_auditoria VARCHAR(50) UNIQUE NOT NULL,       -- Ej: BUSTAMANTE_2025
    periodo VARCHAR(10) NOT NULL,                       -- Ej: "2025"

    -- EQUIPO DE AUDITORÍA
    socio_asignado VARCHAR(100),
    senior_asignado VARCHAR(100),
    semi_asignados TEXT,                                -- JSON array de nombres
    junior_asignados TEXT,                              -- JSON array de nombres

    -- ESTADO
    estado VARCHAR(20) DEFAULT 'PLANEACIÓN',            -- PLANEACIÓN, EJECUCIÓN, REPORTE, FINALIZADO, ARCHIVADO
    fecha_inicio DATE,
    fecha_fin DATE,
    fecha_emision DATE,

    -- RESULTADOS
    hallazgos_total INTEGER DEFAULT 0,
    hallazgos_críticos INTEGER DEFAULT 0,
    hallazgos_observados INTEGER DEFAULT 0,

    -- TRAZABILIDAD
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT idx_codigo_auditoria UNIQUE (codigo_auditoria)
);

-- Tabla de estados financieros capturados (snapshot por período)
CREATE TABLE IF NOT EXISTS financial_snapshots (
    id SERIAL PRIMARY KEY,
    audit_id INTEGER NOT NULL,                          -- FK a audits
    periodo VARCHAR(10) NOT NULL,

    -- BALANCE GENERAL
    activos_corrientes DECIMAL(15,2),
    activos_no_corrientes DECIMAL(15,2),
    total_activos DECIMAL(15,2),

    pasivos_corrientes DECIMAL(15,2),
    pasivos_no_corrientes DECIMAL(15,2),
    total_pasivos DECIMAL(15,2),

    patrimonio DECIMAL(15,2),

    -- ESTADO DE RESULTADOS
    ingresos DECIMAL(15,2),
    costo_ventas DECIMAL(15,2),
    gastos_operacionales DECIMAL(15,2),
    resultado_operacional DECIMAL(15,2),
    resultado_neto DECIMAL(15,2),

    -- ÍNDICES CLAVE
    liquidezcorriente DECIMAL(10,4),
    deuda_capital DECIMAL(10,4),
    margen_bruto DECIMAL(10,4),
    margen_operacional DECIMAL(10,4),
    margen_neto DECIMAL(10,4),

    -- TRAZABILIDAD
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    captured_by VARCHAR(100),

    FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE
);

-- Crear índices para performance
CREATE INDEX IF NOT EXISTS idx_clients_client_id ON clients(client_id);
CREATE INDEX IF NOT EXISTS idx_clients_estado ON clients(estado);
CREATE INDEX IF NOT EXISTS idx_audits_client_id ON audits(client_id);
CREATE INDEX IF NOT EXISTS idx_audits_estado ON audits(estado);
CREATE INDEX IF NOT EXISTS idx_audits_periodo ON audits(periodo);
CREATE INDEX IF NOT EXISTS idx_financial_snapshots_audit_id ON financial_snapshots(audit_id);
