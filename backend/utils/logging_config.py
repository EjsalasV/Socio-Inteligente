"""
Configuración centralizada de logging para SocioAI
Escribe logs a archivo en tiempo real
"""

import logging
import os
from pathlib import Path
from datetime import datetime

# Crear carpeta de logs si no existe
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Archivo de log principal
LOG_FILE = LOG_DIR / f"socio_ai_{datetime.now().strftime('%Y%m%d')}.log"

# Formato de logs
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """Configura logging para toda la aplicación"""

    # Logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Handler para archivo
    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(file_formatter)

    # Handler para consola (solo INFO y arriba)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)

    # Agregar handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Log de inicio
    root_logger.info("=" * 80)
    root_logger.info("🚀 SocioAI Backend iniciado")
    root_logger.info(f"📝 Logs guardados en: {LOG_FILE}")
    root_logger.info("=" * 80)


def get_logger(name: str) -> logging.Logger:
    """Obtener logger para un módulo específico"""
    return logging.getLogger(name)
