"""
Servicio de validación cruzada.

Verifica integridad de datos y detecta procedimientos faltantes.
"""

from __future__ import annotations

import logging
from typing import Any

LOGGER = logging.getLogger("socio_ai.validation_service")


def check_missing_procedures(cliente_id: str, area_codigo: str) -> list[dict[str, Any]]:
    """
    Retorna lista de procedimientos obligatorios que no fueron ejecutados.

    Args:
        cliente_id: ID del cliente
        area_codigo: Código del área

    Returns:
        Lista de procedimientos faltantes con estructura:
        {procedure_id, procedure_name, obligatorio, executed, status}
    """
    from backend.repositories.file_repository import FileRepository

    repo = FileRepository()
    cliente_dir = repo._resolve_cliente_dir(cliente_id)

    # Leer archivo de procedimientos del área
    area_procedures_file = cliente_dir / "procedimientos" / f"{area_codigo}_procedures.yaml"
    if not area_procedures_file.exists():
        LOGGER.warning(f"No se encontró archivo de procedimientos para {area_codigo}")
        return []

    import yaml

    try:
        procedures_data = yaml.safe_load(area_procedures_file.read_text(encoding="utf-8"))
    except Exception as e:
        LOGGER.error(f"Error leyendo procedimientos de {area_codigo}: {e}")
        return []

    if not isinstance(procedures_data, dict):
        return []

    procedures_list = procedures_data.get("procedimientos", [])
    if not isinstance(procedures_list, list):
        return []

    # Filtrar procedimientos obligatorios sin ejecutar
    missing = []
    for proc in procedures_list:
        if not isinstance(proc, dict):
            continue

        is_obligatorio = bool(proc.get("obligatorio", False))
        is_executed = bool(proc.get("status") == "ejecutado")

        if is_obligatorio and not is_executed:
            missing.append(
                {
                    "procedure_id": str(proc.get("id") or proc.get("procedure_id") or "UNKNOWN"),
                    "procedure_name": str(proc.get("nombre") or proc.get("name") or ""),
                    "obligatorio": is_obligatorio,
                    "executed": is_executed,
                    "status": str(proc.get("status") or "pendiente"),
                }
            )

    if missing:
        LOGGER.info(f"missing_procedures cliente={cliente_id} area={area_codigo} count={len(missing)}")

    return missing


def validate_hallazgos_integrity(cliente_id: str, hallazgo_data: dict[str, Any]) -> dict[str, Any]:
    """
    Valida integridad de datos de un hallazgo.

    Args:
        cliente_id: ID del cliente
        hallazgo_data: Datos del hallazgo

    Returns:
        {valid: bool, errors: [str], warnings: [str]}
    """
    errors = []
    warnings = []

    # Validaciones básicas
    if not str(hallazgo_data.get("descripcion") or "").strip():
        errors.append("Hallazgo debe tener descripción")

    if not str(hallazgo_data.get("area_codigo") or "").strip():
        errors.append("Hallazgo debe estar asociado a un área")

    # Validaciones opcionales
    if not hallazgo_data.get("normas_activadas"):
        warnings.append("Hallazgo no tiene normas asociadas")

    impacto = float(hallazgo_data.get("impacto") or 0.0)
    if impacto < 0:
        errors.append("Impacto no puede ser negativo")
    elif impacto > 1e10:
        warnings.append("Impacto parece ser muy alto, verifica")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def validate_area_closure(cliente_id: str, area_codigo: str) -> dict[str, Any]:
    """
    Valida si un área puede ser cerrada.

    Args:
        cliente_id: ID del cliente
        area_codigo: Código del área

    Returns:
        {can_close: bool, missing_procedures: [...], warnings: [...]}
    """
    # Verificar procedimientos faltantes
    missing = check_missing_procedures(cliente_id, area_codigo)

    warnings = []
    if missing:
        warnings.append(f"Hay {len(missing)} procedimientos obligatorios sin ejecutar")

    return {
        "can_close": True,  # Permitir cierre con advertencia
        "missing_procedures": missing,
        "warnings": warnings,
    }
