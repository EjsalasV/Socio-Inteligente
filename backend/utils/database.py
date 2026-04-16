"""Database utilities for backend"""

from typing import Generator, Optional

# Dummy session function - retorna None para pruebas
# En producción, conectar a PostgreSQL/SQLite real
def get_session() -> Optional[object]:
    """
    Dependency para inyectar sesión de base de datos en rutas.
    
    En esta versión de prueba, retorna None.
    En producción, debería retornar sesión SQLAlchemy real.
    """
    try:
        # TODO: Conectar a BD real
        session = None
        yield session
    finally:
        if session:
            session.close()
