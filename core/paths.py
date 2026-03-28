"""
Gestión centralizada de rutas del proyecto SocioAI.
Todas las rutas se calculan relativas a la raíz del proyecto.
"""
from __future__ import annotations

from pathlib import Path


# Raíz del proyecto (dos niveles arriba de core/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Directorios principales
DATA_ROOT       = PROJECT_ROOT / "data"
CLIENTES_DIR    = DATA_ROOT / "clientes"
CATALOGOS_DIR   = DATA_ROOT / "catalogos"
EXPORTS_DIR     = DATA_ROOT / "exports"
UPLOADS_DIR     = DATA_ROOT / "uploads"
LOGS_DIR        = PROJECT_ROOT / "logs"
TESTS_DIR       = PROJECT_ROOT / "tests"

# Catálogos específicos
AREAS_YAML          = CATALOGOS_DIR / "areas.yaml"
CORRESPONDENCIA_YAML = CATALOGOS_DIR / "correspondencia.yaml"
REGLAS_MAT_YAML     = CATALOGOS_DIR / "reglas_materialidad.yaml"
METODOLOGIA_YAML    = CATALOGOS_DIR / "metodologia_calidad.yaml"
ASEVERACIONES_YAML  = CATALOGOS_DIR / "aseveraciones_guia_ls.yaml"


def ruta_cliente(nombre_cliente: str) -> Path:
    """Retorna la ruta base del cliente."""
    return CLIENTES_DIR / nombre_cliente


def ruta_perfil(nombre_cliente: str) -> Path:
    """Retorna la ruta del perfil YAML del cliente."""
    return ruta_cliente(nombre_cliente) / "perfil.yaml"


def ruta_tb(nombre_cliente: str) -> Path:
    """Retorna la ruta del Trial Balance del cliente."""
    return ruta_cliente(nombre_cliente) / "tb.xlsx"


def ruta_materialidad(nombre_cliente: str) -> Path:
    """Retorna la ruta del archivo de materialidad del cliente."""
    return ruta_cliente(nombre_cliente) / "materialidad.yaml"


def ruta_area(nombre_cliente: str, codigo_ls: str) -> Path:
    """Retorna la ruta del YAML de estado de un área."""
    return ruta_cliente(nombre_cliente) / "areas" / f"{codigo_ls}.yaml"


def ruta_historial_area(nombre_cliente: str, codigo_ls: str) -> Path:
    """Retorna la ruta del historial de un área."""
    return ruta_cliente(nombre_cliente) / "areas" / f"{codigo_ls}_historial.yaml"


def ruta_hallazgos_gestion(nombre_cliente: str) -> Path:
    """Retorna la ruta del archivo de hallazgos de gestión."""
    return ruta_cliente(nombre_cliente) / "hallazgos_gestion.yaml"


def ruta_export(nombre_cliente: str, filename: str) -> Path:
    """Retorna la ruta de un archivo de exportación."""
    return EXPORTS_DIR / nombre_cliente / filename


def cliente_existe(nombre_cliente: str) -> bool:
    """Verifica si el cliente existe en el repositorio."""
    return ruta_cliente(nombre_cliente).exists()


def listar_clientes() -> list[str]:
    """Lista todos los clientes disponibles."""
    if not CLIENTES_DIR.exists():
        return []
    return sorted([
        d.name for d in CLIENTES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])
