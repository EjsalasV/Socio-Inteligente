"""
Database configuration and session management
Conecta a PostgreSQL en Railway (producción) o local SQLite (desarrollo)
"""

import os
from typing import Generator, Optional
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

# Obtener DATABASE_URL de variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("[WARNING] DATABASE_URL not configured.")
    print("    Configure in Vercel -> Settings -> Environment Variables")
    print("    Copy from Railway -> Postgres -> Connect")
    DATABASE_URL = "sqlite:///./test.db"  # Fallback a SQLite local para testing
    print(f"    Using fallback: {DATABASE_URL}")
else:
    # Mostrar conexión (sin exponer password)
    print(f"[INFO] DATABASE_URL configured: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

# Crear engine SQLAlchemy
# Para PostgreSQL (Railway), usar conexión directa
if "postgresql" in DATABASE_URL or "postgres" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verificar conexión antes de usar
        pool_size=5,
        max_overflow=10,
        echo=False,  # Set to True para debug SQL
    )
else:
    # Fallback para SQLite local
    engine = create_engine(
        DATABASE_URL,
        echo=False,
    )

# Crear SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _is_sqlite_engine() -> bool:
    return engine.dialect.name == "sqlite"


def _table_has_serial_primary_key(connection: Session | any, table_name: str) -> bool:
    row = connection.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name = :name"),
        {"name": table_name},
    ).fetchone()
    if not row or not row[0]:
        return False
    return "SERIAL PRIMARY KEY" in str(row[0]).upper()


def _repair_sqlite_primary_key_tables() -> None:
    """
    SQLite no autoincrementa correctamente columnas declaradas como SERIAL PRIMARY KEY.
    Algunas migraciones históricas dejaron tablas con ids NULL en desarrollo local.
    Esta rutina reconstruye esas tablas con INTEGER PRIMARY KEY AUTOINCREMENT.
    """
    if not _is_sqlite_engine():
        return

    repair_sql = {
        "clients": """
            CREATE TABLE clients_repaired (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id VARCHAR(50) UNIQUE NOT NULL,
                nombre VARCHAR(255) NOT NULL,
                ruc VARCHAR(20),
                sector VARCHAR(100),
                tipo_entidad VARCHAR(50),
                contacto_nombre VARCHAR(100),
                contacto_email VARCHAR(100),
                contacto_telefono VARCHAR(20),
                moneda VARCHAR(10) DEFAULT 'COP',
                materialidad_general DECIMAL(15,2),
                materialidad_procedimiento DECIMAL(15,2),
                periodo_actual VARCHAR(10),
                fecha_cierre DATE,
                estado VARCHAR(20) DEFAULT 'ACTIVO',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                tamano VARCHAR(20),
                normativa VARCHAR(50) DEFAULT 'NIIF',
                tiene_mayor_2024 BOOLEAN DEFAULT 0,
                fecha_mayor_cargado TIMESTAMP
            );
            INSERT INTO clients_repaired (
                id, client_id, nombre, ruc, sector, tipo_entidad,
                contacto_nombre, contacto_email, contacto_telefono, moneda,
                materialidad_general, materialidad_procedimiento, periodo_actual,
                fecha_cierre, estado, created_at, updated_at, created_by,
                tamano, normativa, tiene_mayor_2024, fecha_mayor_cargado
            )
            SELECT
                COALESCE(id, rowid), client_id, nombre, ruc, sector, tipo_entidad,
                contacto_nombre, contacto_email, contacto_telefono, COALESCE(moneda, 'COP'),
                materialidad_general, materialidad_procedimiento, periodo_actual,
                fecha_cierre, COALESCE(estado, 'ACTIVO'), created_at, updated_at, created_by,
                tamano, COALESCE(normativa, 'NIIF'), COALESCE(tiene_mayor_2024, 0), fecha_mayor_cargado
            FROM clients;
            DROP TABLE clients;
            ALTER TABLE clients_repaired RENAME TO clients;
            CREATE UNIQUE INDEX IF NOT EXISTS idx_client_id ON clients(client_id);
            CREATE INDEX IF NOT EXISTS ix_clients_id ON clients(id);
            CREATE INDEX IF NOT EXISTS ix_clients_client_id ON clients(client_id);
        """,
        "audits": """
            CREATE TABLE audits_repaired (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                codigo_auditoria VARCHAR(50) UNIQUE NOT NULL,
                periodo VARCHAR(10) NOT NULL,
                socio_asignado VARCHAR(100),
                senior_asignado VARCHAR(100),
                semi_asignados TEXT,
                junior_asignados TEXT,
                estado VARCHAR(20) DEFAULT 'PLANEACIÓN',
                fecha_inicio DATE,
                fecha_fin DATE,
                fecha_emision DATE,
                hallazgos_total INTEGER DEFAULT 0,
                hallazgos_críticos INTEGER DEFAULT 0,
                hallazgos_observados INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            );
            INSERT INTO audits_repaired (
                id, client_id, codigo_auditoria, periodo, socio_asignado, senior_asignado,
                semi_asignados, junior_asignados, estado, fecha_inicio, fecha_fin, fecha_emision,
                hallazgos_total, hallazgos_críticos, hallazgos_observados, created_at, updated_at
            )
            SELECT
                COALESCE(id, rowid), client_id, codigo_auditoria, periodo, socio_asignado, senior_asignado,
                semi_asignados, junior_asignados, COALESCE(estado, 'PLANEACIÓN'),
                fecha_inicio, fecha_fin, fecha_emision,
                COALESCE(hallazgos_total, 0), COALESCE(hallazgos_críticos, 0),
                COALESCE(hallazgos_observados, 0), created_at, updated_at
            FROM audits;
            DROP TABLE audits;
            ALTER TABLE audits_repaired RENAME TO audits;
            CREATE UNIQUE INDEX IF NOT EXISTS idx_codigo_auditoria ON audits(codigo_auditoria);
        """,
        "cliente_configurations": """
            CREATE TABLE cliente_configurations_repaired (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                tipo_entidad VARCHAR(50) NOT NULL,
                respuestas JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                CONSTRAINT idx_client_config_unique UNIQUE (client_id, tipo_entidad)
            );
            INSERT INTO cliente_configurations_repaired (
                id, client_id, tipo_entidad, respuestas, created_at, updated_at, updated_by
            )
            SELECT
                COALESCE(id, rowid), client_id, tipo_entidad, respuestas, created_at, updated_at, updated_by
            FROM cliente_configurations;
            DROP TABLE cliente_configurations;
            ALTER TABLE cliente_configurations_repaired RENAME TO cliente_configurations;
            CREATE INDEX IF NOT EXISTS idx_cliente_configurations_client_id ON cliente_configurations(client_id);
            CREATE INDEX IF NOT EXISTS idx_cliente_configurations_tipo_entidad ON cliente_configurations(tipo_entidad);
        """,
    }

    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys=OFF"))
        for table_name, sql in repair_sql.items():
            if not _table_has_serial_primary_key(connection, table_name):
                continue

            print(f"[INFO] Repairing SQLite table schema: {table_name}")
            for statement in [stmt.strip() for stmt in sql.split(";") if stmt.strip()]:
                connection.exec_driver_sql(statement)
        connection.execute(text("PRAGMA foreign_keys=ON"))


def get_session() -> Generator[Session, None, None]:
    """
    Dependency para inyectar sesión SQLAlchemy en rutas FastAPI

    Uso en endpoints:
    ```python
    async def my_endpoint(session: Session = Depends(get_session)):
        users = session.query(User).all()
    ```
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database error: {e}")
        raise
    finally:
        db.close()


def init_db():
    """
    Inicializar tablas de la base de datos
    Llama a esta función al startup del app
    """
    try:
        # Importar todos los modelos para que se registren en Base.metadata
        from backend.models.client import Client
        from backend.models.audit import Audit
        from backend.models.cliente_configuration import ClienteConfiguration
        from backend.models.workpapers_template import WorkpapersTemplate
        from backend.models.workpapers_observation import WorkpapersObservation
        from backend.models.workpapers_files import WorkpapersFile
        from backend.models.knowledge_entity import KnowledgeEntity
        from backend.models.knowledge_relation import KnowledgeRelation
        from backend.models.knowledge_event import KnowledgeEvent
        from backend.models.knowledge_chunk import KnowledgeChunk
        from backend.models.intelligent_analysis_history import IntelligentAnalysisHistory

        # Importar Base de la localización compartida
        from backend.models import Base

        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        _repair_sqlite_primary_key_tables()
        print("[OK] Database initialized (tables created if they did not exist)")

    except Exception as e:
        print(f"[ERROR] Error initializing database: {e}")
        raise


# Event listener para verificar conexión al startup
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Verificar que la conexión a BD está activa"""
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        print("[OK] Database connection verified")
    except Exception as e:
        print(f"[ERROR] Error verifying connection: {e}")
