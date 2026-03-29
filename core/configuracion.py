from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

_CONFIG: Dict[str, Any] | None = None


def cargar_config() -> Dict[str, Any]:
    """
    Carga la configuración desde config.yaml.
    Se cachea la primera vez que se llama para evitar lecturas repetidas.

    Returns:
        Diccionario con toda la configuración

    Raises:
        FileNotFoundError: Si config.yaml no existe
        ValueError: Si el YAML es inválido
    """
    global _CONFIG

    if _CONFIG is not None:
        return _CONFIG

    ruta_config = Path(__file__).parent / "config.yaml"

    if not ruta_config.exists():
        raise FileNotFoundError(f"No existe archivo de configuración: {ruta_config}")

    with open(ruta_config, "r", encoding="utf-8") as archivo:
        config = yaml.safe_load(archivo)

    if config is None:
        raise ValueError(f"El archivo config.yaml está vacío: {ruta_config}")

    if not isinstance(config, dict):
        raise ValueError(f"El config.yaml no es un diccionario válido: {ruta_config}")

    _CONFIG = config
    return _CONFIG


def obtener_variaciones_config() -> Dict[str, Any]:
    """Obtiene configuración de variaciones."""
    return cargar_config().get("variaciones", {})


def obtener_scoring_config() -> Dict[str, Any]:
    """Obtiene configuración de scoring."""
    return cargar_config().get("scoring", {})


def obtener_riesgos_config() -> Dict[str, Any]:
    """Obtiene configuración de riesgos."""
    return cargar_config().get("riesgos", {})


def obtener_logging_config() -> Dict[str, Any]:
    """Obtiene configuración de logging."""
    return cargar_config().get("logging", {})


def obtener_validacion_config() -> Dict[str, Any]:
    """Obtiene configuración de validación."""
    return cargar_config().get("validacion", {})


def obtener_formato_config() -> Dict[str, Any]:
    """Obtiene configuración de formato."""
    return cargar_config().get("formato", {})
