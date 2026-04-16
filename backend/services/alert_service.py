"""
Servicio de alertas operacionales.

Crea, gestiona y resuelve alertas del sistema automáticamente.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.models.operational_alert import AlertSeverity, AlertType, OperationalAlert

LOGGER = logging.getLogger("socio_ai.alert_service")


def create_alert(
    cliente_id: str,
    tipo: str | AlertType,
    severidad: str | AlertSeverity,
    mensaje: str,
    metadata: dict[str, Any] | None = None,
) -> OperationalAlert:
    """
    Crea una alerta operacional.

    Args:
        cliente_id: ID del cliente
        tipo: Tipo de alerta
        severidad: Nivel de severidad
        mensaje: Mensaje descriptivo
        metadata: Datos adicionales

    Returns:
        OperationalAlert creada
    """
    alert = OperationalAlert(
        cliente_id=cliente_id,
        tipo=tipo,
        severidad=severidad,
        mensaje=mensaje,
        metadata=metadata or {},
    )

    LOGGER.info(f"alert_created cliente={cliente_id} tipo={alert.tipo} severidad={alert.severidad}")

    # Persistir en repositorio
    from backend.repositories.history_repository import append_alert

    append_alert(alert.to_dict())

    return alert


def get_active_alerts(cliente_id: str) -> list[OperationalAlert]:
    """
    Obtiene todas las alertas no resueltas de un cliente.

    Args:
        cliente_id: ID del cliente

    Returns:
        Lista de alertas activas
    """
    from backend.repositories.history_repository import get_alerts

    alerts_data = get_alerts(cliente_id, resolved_only=False)
    return [OperationalAlert.from_dict(data) for data in alerts_data]


def get_all_alerts(cliente_id: str, resolved_only: bool = False) -> list[OperationalAlert]:
    """
    Obtiene todas las alertas de un cliente.

    Args:
        cliente_id: ID del cliente
        resolved_only: Si solo retornar resueltas

    Returns:
        Lista de alertas
    """
    from backend.repositories.history_repository import get_alerts

    alerts_data = get_alerts(cliente_id, resolved_only=resolved_only)
    return [OperationalAlert.from_dict(data) for data in alerts_data]


def resolve_alert(alert_id: str) -> OperationalAlert | None:
    """
    Marca una alerta como resuelta.

    Args:
        alert_id: ID de la alerta

    Returns:
        Alerta resuelta o None si no existe
    """
    from backend.repositories.history_repository import update_alert_status

    updated_data = update_alert_status(alert_id, resolved=True)
    if updated_data:
        return OperationalAlert.from_dict(updated_data)
    return None


def check_materialidad_excedida(cliente_id: str, suma_hallazgos: float, materialidad: float) -> bool:
    """
    Verifica si la materialidad fue excedida.

    Args:
        cliente_id: ID del cliente
        suma_hallazgos: Suma de hallazgos
        materialidad: Límite de materialidad

    Returns:
        True si fue excedida
    """
    if suma_hallazgos > materialidad:
        create_alert(
            cliente_id=cliente_id,
            tipo=AlertType.MATERIALIDAD_EXCEDIDA,
            severidad=AlertSeverity.CRITICO,
            mensaje=f"Materialidad excedida: {suma_hallazgos:.2f} > {materialidad:.2f}",
            metadata={"suma_hallazgos": suma_hallazgos, "materialidad": materialidad},
        )
        LOGGER.warning(f"materialidad_excedida cliente={cliente_id} suma={suma_hallazgos} límite={materialidad}")
        return True
    return False


def check_gate_bloqueado(cliente_id: str, area_codigo: str, can_approve: bool) -> bool:
    """
    Verifica si un gate de calidad está bloqueado.

    Args:
        cliente_id: ID del cliente
        area_codigo: Código del área
        can_approve: Si se puede aprobar (False = bloqueado)

    Returns:
        True si está bloqueado
    """
    if not can_approve:
        create_alert(
            cliente_id=cliente_id,
            tipo=AlertType.GATE_BLOQUEADO,
            severidad=AlertSeverity.ALTO,
            mensaje=f"Gate de calidad bloqueado en área {area_codigo}",
            metadata={"area_codigo": area_codigo},
        )
        LOGGER.warning(f"gate_bloqueado cliente={cliente_id} area={area_codigo}")
        return True
    return False
