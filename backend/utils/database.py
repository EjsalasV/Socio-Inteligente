"""
Database configuration and session management
Conecta a PostgreSQL en Railway (producción) o local SQLite (desarrollo)
"""

import os
from typing import Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

# Obtener DATABASE_URL de variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("⚠️  DATABASE_URL no está configurada.")
    print("    Configúrala en Vercel → Settings → Environment Variables")
    print("    Copia de Railway → Postgres → Connect")
    DATABASE_URL = "sqlite:///./test.db"  # Fallback a SQLite local para testing
    print(f"    Usando fallback: {DATABASE_URL}")
else:
    # Mostrar conexión (sin exponer password)
    print(f"📡 DATABASE_URL configurada: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

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
        print(f"❌ Database error: {e}")
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
        from backend.models.workpapers_template import WorkpapersTemplate
        from backend.models.workpapers_observation import WorkpapersObservation
        from backend.models.audit_history import AuditHistory
        from backend.models.operational_alert import OperationalAlert
        from backend.models.period_snapshot import PeriodSnapshot
        from backend.models.report_template import ReportTemplate
        from backend.models.webhook import Webhook
        from backend.models.workpapers_files import WorkpapersFiles

        # Importar Base de cualquiera de los modelos
        from backend.models.client import Base

        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("✅ Base de datos inicializada (tablas creadas si no existen)")

    except Exception as e:
        print(f"⚠️  Error inicializando BD: {e}")
        raise


# Event listener para verificar conexión al startup
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Verificar que la conexión a BD está activa"""
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        print("✅ Conexión a base de datos verificada")
    except Exception as e:
        print(f"❌ Error verificando conexión: {e}")
