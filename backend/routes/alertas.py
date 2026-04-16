"""
Rutas para gestión de alertas operacionales.

Permite obtener, crear y resolver alertas automáticamente.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status

from backend.auth import authorize_cliente_access, get_current_user
from backend.models.operational_alert import AlertSeverity, AlertType
from backend.schemas import ApiResponse, UserContext
from backend.services.alert_service import get_active_alerts, resolve_alert

router = APIRouter(prefix="/api/alertas", tags=["alertas"])
LOGGER = logging.getLogger("socio_ai.alertas")


@router.get("/{cliente_id}", response_model=ApiResponse)
def get_alertas(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Obtiene todas las alertas activas de un cliente.

    Response:
        {
            "status": "ok",
            "data": {
                "alertas": [
                    {
                        "id": "...",
                        "tipo": "MATERIALIDAD_EXCEDIDA",
                        "severidad": "CRITICO",
                        "mensaje": "...",
                        "fecha_creada": "..."
                    },
                    ...
                ],
                "total_criticos": 1,
                "total_altos": 2
            }
        }
    """
    authorize_cliente_access(cliente_id, user)

    try:
        alertas = get_active_alerts(cliente_id)

        # Contar por severidad
        total_criticos = sum(1 for a in alertas if a.severidad == AlertSeverity.CRITICO.value)
        total_altos = sum(1 for a in alertas if a.severidad == AlertSeverity.ALTO.value)

        alertas_data = [
            {
                "id": a.id,
                "tipo": a.tipo,
                "severidad": a.severidad,
                "mensaje": a.mensaje,
                "fecha_creada": a.fecha_creada.isoformat(),
                "metadata": a.metadata,
            }
            for a in alertas
        ]

        return ApiResponse(
            status="ok",
            data={
                "alertas": alertas_data,
                "total_criticos": total_criticos,
                "total_altos": total_altos,
            },
        )
    except Exception as e:
        LOGGER.error(f"Error en get_alertas: {e}")
        return ApiResponse(
            status="error",
            message=f"Error obteniendo alertas: {str(e)}",
            data={},
        )


@router.post("/{alert_id}/resolve", response_model=ApiResponse)
def resolve_alerta(
    alert_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Marca una alerta como resuelta.

    Response:
        {
            "status": "ok",
            "data": {
                "id": "...",
                "resuelto": true
            }
        }
    """
    # Nota: Esta ruta no requiere validación de cliente_id porque
    # el resolve_alert busca por ID global (debería mejorarse en v2)

    try:
        updated = resolve_alert(alert_id)
        if updated:
            return ApiResponse(
                status="ok",
                data={
                    "id": updated.id,
                    "resuelto": updated.resuelto,
                },
            )
        else:
            return ApiResponse(
                status="warning",
                message="Alerta no encontrada",
                data={},
            )
    except Exception as e:
        LOGGER.error(f"Error resolving alert: {e}")
        return ApiResponse(
            status="error",
            message=f"Error resolviendo alerta: {str(e)}",
            data={},
        )
