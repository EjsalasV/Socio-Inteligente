from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from core.configuracion import obtener_logging_config


def configurar_logging() -> logging.Logger:
    """
    Configura el sistema de logging según config.yaml.

    Returns:
        Logger configurado para uso global en la aplicación.
    """
    config_log = obtener_logging_config()

    logger = logging.getLogger("socio_ai")
    nivel = config_log.get("nivel", "INFO").upper()
    logger.setLevel(getattr(logging, nivel, logging.INFO))

    # Evitar duplicar handlers si ya fue configurado
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt=config_log.get("timestamp_format", "%Y-%m-%d %H:%M:%S"),
    )

    # Handler de consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler de archivo rotativo
    archivo = config_log.get("archivo")
    if archivo:
        ruta_log = Path(archivo)
        ruta_log.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(ruta_log),
            maxBytes=config_log.get("max_bytes", 10_485_760),  # 10 MB
            backupCount=config_log.get("backup_count", 5),
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger


def obtener_logger() -> logging.Logger:
    """
    Obtiene el logger de SocioAI ya configurado.

    Returns:
        Logger principal del sistema.
    """
    logger = logging.getLogger("socio_ai")
    if not logger.handlers:
        configurar_logging()
    return logger


def registrar_ejecucion(
    accion: str,
    cliente: str | None = None,
    resultado: str = "exito",
    detalles: Dict[str, Any] | None = None,
    nivel_log: str = "INFO",
) -> None:
    """
    Registra una ejecución o acción del sistema con contexto.

    Args:
        accion: Acción realizada (ej: 'cargar_perfil', 'ranking_areas').
        cliente: Nombre del cliente, si aplica.
        resultado: Estado del resultado ('exito', 'error', 'advertencia').
        detalles: Información adicional útil para trazabilidad.
        nivel_log: Nivel del log (DEBUG, INFO, WARNING, ERROR).
    """
    logger = obtener_logger()

    registro = {
        "timestamp": datetime.now().isoformat(),
        "accion": accion,
        "cliente": cliente or "N/A",
        "resultado": resultado,
        "detalles": detalles or {},
    }

    nivel = getattr(logging, nivel_log.upper(), logging.INFO)
    mensaje = json.dumps(registro, ensure_ascii=False)

    logger.log(nivel, mensaje)


def registrar_error(
    accion: str,
    error: Exception,
    cliente: str | None = None,
    detalles: Dict[str, Any] | None = None,
) -> None:
    """
    Registra un error del sistema con contexto.

    Args:
        accion: Acción en la que ocurrió el error.
        error: Excepción capturada.
        cliente: Nombre del cliente, si aplica.
        detalles: Información adicional útil.
    """
    logger = obtener_logger()

    registro = {
        "timestamp": datetime.now().isoformat(),
        "accion": accion,
        "cliente": cliente or "N/A",
        "resultado": "error",
        "tipo_error": type(error).__name__,
        "mensaje_error": str(error),
        "detalles": detalles or {},
    }

    mensaje = json.dumps(registro, ensure_ascii=False)
    logger.error(mensaje)


def registrar_cambio_datos(
    cliente: str,
    tipo_dato: str,
    accion: str,
    cambios: Dict[str, Any],
) -> None:
    """
    Registra cambios en datos del sistema para trazabilidad interna.

    Args:
        cliente: Nombre del cliente.
        tipo_dato: Tipo de dato modificado ('perfil', 'materialidad', 'hallazgos', etc.).
        accion: Acción ejecutada ('creado', 'actualizado', 'eliminado').
        cambios: Diccionario describiendo qué cambió.
    """
    logger = obtener_logger()

    registro = {
        "timestamp": datetime.now().isoformat(),
        "cliente": cliente,
        "tipo_dato": tipo_dato,
        "accion": accion,
        "cambios": cambios,
    }

    mensaje = json.dumps(registro, ensure_ascii=False)
    logger.info(f"CAMBIO_DE_DATOS: {mensaje}")


def registrar_advertencia(
    accion: str,
    mensaje: str,
    cliente: str | None = None,
    detalles: Dict[str, Any] | None = None,
) -> None:
    """
    Registra advertencias no críticas del sistema.

    Args:
        accion: Acción donde se detectó la advertencia.
        mensaje: Mensaje descriptivo.
        cliente: Nombre del cliente, si aplica.
        detalles: Información adicional.
    """
    logger = obtener_logger()

    registro = {
        "timestamp": datetime.now().isoformat(),
        "accion": accion,
        "cliente": cliente or "N/A",
        "resultado": "advertencia",
        "mensaje": mensaje,
        "detalles": detalles or {},
    }

    logger.warning(json.dumps(registro, ensure_ascii=False))
