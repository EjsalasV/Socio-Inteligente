"""
Servicio de auditoría para registrar cambios en el sistema.

Registra todos los cambios (INSERT, UPDATE, DELETE) en tablas críticas
y genera alertas automáticas para eventos significativos.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from backend.models.audit_history import AuditHistory

LOGGER = logging.getLogger("socio_ai.audit_logger")


def log_change(
    cliente_id: str,
    tabla: str,
    accion: str,
    usuario: str,
    diff_data: dict[str, Any],
) -> AuditHistory:
    """
    Registra un cambio en audit_history.

    Args:
        cliente_id: ID del cliente
        tabla: Nombre de la tabla afectada
        accion: INSERT, UPDATE o DELETE
        usuario: Usuario que realizó el cambio
        diff_data: Datos del cambio (diff)

    Returns:
        AuditHistory registrado
    """
    # Validar acción
    accion_upper = str(accion).upper().strip()
    if accion_upper not in {"INSERT", "UPDATE", "DELETE"}:
        LOGGER.warning(f"Acción desconocida: {accion}")
        accion_upper = "OTRO"

    # Crear registro
    audit_record = AuditHistory(
        cliente_id=cliente_id,
        tabla_afectada=tabla,
        accion=accion_upper,
        usuario=usuario,
        diff_data=diff_data,
        timestamp=datetime.now(timezone.utc),
    )

    # Log
    LOGGER.info(
        f"audit_change cliente={cliente_id} tabla={tabla} accion={accion_upper} usuario={usuario} hash={audit_record.hash_cambio[:8]}"
    )

    # Persistir en repositorio (será manejado por history_repository)
    from backend.repositories.history_repository import append_audit_log

    append_audit_log(audit_record.to_dict())

    return audit_record


def track_procedure_execution(
    cliente_id: str,
    area_codigo: str,
    procedure_id: str,
    executed: bool,
    usuario: str = "system",
) -> None:
    """
    Registra la ejecución de un procedimiento.

    Si el procedimiento es obligatorio y NO fue ejecutado, crea una alerta.

    Args:
        cliente_id: ID del cliente
        area_codigo: Código del área
        procedure_id: ID del procedimiento
        executed: Si fue ejecutado
        usuario: Usuario que registra
    """
    diff_data = {
        "procedure_id": procedure_id,
        "area_codigo": area_codigo,
        "executed": executed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    log_change(
        cliente_id=cliente_id,
        tabla="procedimientos",
        accion="UPDATE" if executed else "SKIP",
        usuario=usuario,
        diff_data=diff_data,
    )

    # Si no fue ejecutado, crear alerta (será manejado por alert_service)
    if not executed:
        from backend.services.alert_service import create_alert
        from backend.models.operational_alert import AlertType, AlertSeverity

        create_alert(
            cliente_id=cliente_id,
            tipo=AlertType.PROCEDIMIENTO_FALTANTE,
            severidad=AlertSeverity.MEDIO,
            mensaje=f"Procedimiento {procedure_id} no ejecutado en área {area_codigo}",
            metadata={"procedure_id": procedure_id, "area_codigo": area_codigo},
        )

    LOGGER.info(f"procedure_tracking cliente={cliente_id} area={area_codigo} proc={procedure_id} executed={executed}")
