"""
Utilidades para acciones destructivas con logging de auditoría.

FASE 7: Confirmaciones destructivas - registra todas las eliminaciones/cambios irreversibles.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.models.audit_history import AuditHistory
from backend.services.audit_logger_service import log_change

LOGGER = logging.getLogger("socio_ai.destructive_actions")


def log_delete_action(
    cliente_id: str,
    entity_type: str,
    entity_id: str,
    usuario: str,
    data_before: dict[str, Any] | None = None,
) -> AuditHistory:
    """
    Registra una eliminación como acción destructiva.

    Args:
        cliente_id: ID del cliente afectado
        entity_type: Tipo de entidad (hallazgo, area, reporte, etc)
        entity_id: ID de la entidad eliminada
        usuario: Usuario que realizó la eliminación
        data_before: Datos antes de la eliminación (para auditoría)

    Returns:
        Registro de auditoría creado
    """
    tabla_map = {
        "hallazgo": "hallazgos",
        "area": "areas",
        "reporte": "reportes",
        "cliente": "clientes",
        "procedimiento": "procedimientos",
    }

    tabla = tabla_map.get(entity_type.lower(), entity_type)

    from datetime import datetime, timezone
    diff_data = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": "DELETE",
        "deleted_at": str(datetime.now(timezone.utc).isoformat()),
        "data_before": data_before or {},
    }

    LOGGER.warning(
        f"Destructive DELETE: cliente={cliente_id} entity={entity_type} id={entity_id} usuario={usuario}"
    )

    return log_change(
        cliente_id=cliente_id,
        tabla=tabla,
        accion="DELETE",
        usuario=usuario,
        diff_data=diff_data,
    )


def log_finalize_action(
    cliente_id: str,
    entity_type: str,
    entity_id: str,
    usuario: str,
    reason: str = "",
) -> AuditHistory:
    """
    Registra una finalización/cierre como acción irreversible.

    Args:
        cliente_id: ID del cliente
        entity_type: Tipo de entidad (area, reporte, cliente)
        entity_id: ID de la entidad
        usuario: Usuario que la finalizó
        reason: Razón de la finalización

    Returns:
        Registro de auditoría
    """
    tabla_map = {
        "area": "areas",
        "reporte": "reportes",
        "cliente": "clientes",
    }

    tabla = tabla_map.get(entity_type.lower(), entity_type)

    from datetime import datetime, timezone
    diff_data = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": "FINALIZE",
        "reason": reason,
        "finalized_at": str(datetime.now(timezone.utc).isoformat()),
    }

    LOGGER.info(
        f"Destructive FINALIZE: cliente={cliente_id} entity={entity_type} id={entity_id} usuario={usuario}"
    )

    return log_change(
        cliente_id=cliente_id,
        tabla=tabla,
        accion="UPDATE",
        usuario=usuario,
        diff_data=diff_data,
    )


def log_emit_action(
    cliente_id: str,
    reporte_id: str,
    usuario: str,
    version: str = "",
) -> AuditHistory:
    """
    Registra la emisión de un reporte (acción irreversible).

    Args:
        cliente_id: ID del cliente
        reporte_id: ID del reporte emitido
        usuario: Usuario que emitió
        version: Versión del reporte

    Returns:
        Registro de auditoría
    """
    from datetime import datetime, timezone
    diff_data = {
        "entity_type": "reporte",
        "entity_id": reporte_id,
        "action": "EMIT",
        "version": version,
        "emitted_at": str(datetime.now(timezone.utc).isoformat()),
    }

    LOGGER.info(
        f"Destructive EMIT: cliente={cliente_id} reporte={reporte_id} usuario={usuario}"
    )

    return log_change(
        cliente_id=cliente_id,
        tabla="reportes",
        accion="UPDATE",
        usuario=usuario,
        diff_data=diff_data,
    )
