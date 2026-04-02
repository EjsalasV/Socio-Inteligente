from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
import yaml


_CONFIG: Dict[str, Any] | None = None


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    version: str
    environment: str = "development"
    debug: bool = False

    @field_validator("environment")
    @classmethod
    def _normalize_environment(cls, value: str) -> str:
        return str(value).strip().lower()


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    level: str = "INFO"
    format: str = "json"
    timestamp_format: str = "%Y-%m-%d %H:%M:%S"
    file: str = "logs/socio_ai.log"
    max_bytes: int = Field(default=10_485_760, ge=1)
    backup_count: int = Field(default=5, ge=1)

    @field_validator("level")
    @classmethod
    def _normalize_level(cls, value: str) -> str:
        return str(value).strip().upper()


class MaterialidadConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    minimum_threshold: float = Field(..., ge=0)


class AuditAreaConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    weight: float = Field(..., ge=0.0, le=1.0)

    @field_validator("code", "name")
    @classmethod
    def _strip_required_text(cls, value: str) -> str:
        text = str(value).strip()
        if not text:
            raise ValueError("must not be empty")
        return text


class RagConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    retrieval_method: str
    top_k: int = Field(..., ge=1)
    min_score: float = Field(..., ge=0.0, le=1.0)


class ConfigSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    app: AppConfig
    logging: LoggingConfig
    materialidad: MaterialidadConfig
    audit_areas: list[AuditAreaConfig]
    rag: RagConfig

    @model_validator(mode="after")
    def _validate_unique_area_codes(self) -> "ConfigSchema":
        seen: set[str] = set()
        duplicates: set[str] = set()
        for area in self.audit_areas:
            code = area.code
            if code in seen:
                duplicates.add(code)
            seen.add(code)
        if duplicates:
            dupes = ", ".join(sorted(duplicates))
            raise ValueError(f"audit_areas has duplicate code values: {dupes}")
        return self


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    raw = str(value).strip().lower()
    if raw in {"1", "true", "yes", "on", "si"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return None


def _resolver_ruta_config() -> Path:
    env_path = os.getenv("SOCIOAI_CONFIG")
    if env_path:
        return Path(env_path).expanduser().resolve()

    project_root = Path(__file__).resolve().parents[1]
    candidatos = [
        project_root / "config.yaml",
        Path(__file__).parent / "config.yaml",  # compatibilidad legacy
    ]
    for ruta in candidatos:
        if ruta.exists():
            return ruta
    return candidatos[0]


def _normalizar_logging_config(logging_cfg: Dict[str, Any]) -> Dict[str, Any]:
    cfg = dict(logging_cfg or {})
    level = cfg.get("level", cfg.get("nivel", "INFO"))
    file_path = cfg.get("file", cfg.get("archivo", "logs/socio_ai.log"))
    cfg["level"] = str(level).upper()
    cfg["file"] = file_path
    return cfg


def _normalizar_aliases(config: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(config)
    logging_cfg = out.get("logging", {})
    if isinstance(logging_cfg, dict):
        out["logging"] = _normalizar_logging_config(logging_cfg)
    return out


def _validar_config(config: Dict[str, Any], ruta_config: Path) -> Dict[str, Any]:
    try:
        validada = ConfigSchema.model_validate(config)
    except ValidationError as exc:
        raise ValueError(
            f"config.yaml inválido ({ruta_config}). "
            f"Detalles: {exc.errors()}"
        ) from exc
    except ValueError as exc:
        raise ValueError(
            f"config.yaml inválido ({ruta_config}). {exc}"
        ) from exc
    return validada.model_dump(mode="python")


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
    
    ruta_config = _resolver_ruta_config()
    
    if not ruta_config.exists():
        raise FileNotFoundError(f"No existe archivo de configuración: {ruta_config}")
    
    with open(ruta_config, "r", encoding="utf-8") as archivo:
        config = yaml.safe_load(archivo)
    
    if config is None:
        raise ValueError(f"El archivo config.yaml está vacío: {ruta_config}")
    
    if not isinstance(config, dict):
        raise ValueError(f"El config.yaml no es un diccionario válido: {ruta_config}")
    
    config_normalizada = _normalizar_aliases(config)
    _CONFIG = _validar_config(config_normalizada, ruta_config)
    return _CONFIG


def obtener_app_config() -> Dict[str, Any]:
    """Obtiene configuración de app con overrides seguros por entorno."""
    app_cfg = dict(cargar_config().get("app", {}))

    env_name = (
        os.getenv("SOCIOAI_ENV")
        or os.getenv("ENV")
        or app_cfg.get("environment")
        or "development"
    )
    environment = str(env_name).strip().lower()
    app_cfg["environment"] = environment

    debug_override = _to_bool(os.getenv("SOCIOAI_DEBUG"))
    cfg_debug = _to_bool(app_cfg.get("debug"))
    if cfg_debug is None:
        cfg_debug = environment != "production"

    if debug_override is not None:
        app_cfg["debug"] = debug_override
    elif environment == "production":
        app_cfg["debug"] = False
    else:
        app_cfg["debug"] = bool(cfg_debug)

    return app_cfg


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
    raw = cargar_config().get("logging", {})
    return raw if isinstance(raw, dict) else {}


def obtener_audit_areas_config() -> List[Dict[str, Any]]:
    """Obtiene áreas de auditoría configuradas (si existen)."""
    raw = cargar_config().get("audit_areas", [])
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(
                {
                    "code": str(item["code"]),
                    "name": str(item["name"]),
                    "weight": float(item["weight"]),
                }
            )
    return out


def obtener_validacion_config() -> Dict[str, Any]:
    """Obtiene configuración de validación."""
    return cargar_config().get("validacion", {})


def obtener_formato_config() -> Dict[str, Any]:
    """Obtiene configuración de formato."""
    return cargar_config().get("formato", {})


def obtener_materialidad_config() -> Dict[str, Any]:
    """Obtiene configuración de materialidad."""
    raw = cargar_config().get("materialidad", {})
    return raw if isinstance(raw, dict) else {}
