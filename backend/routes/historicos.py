"""
Rutas para gestión de históricos y snapshots de períodos.

Permite cargar y comparar estados de períodos anteriores.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status

from backend.auth import authorize_cliente_access, get_current_user
from backend.models.period_snapshot import PeriodSnapshot
from backend.repositories.history_repository import (
    get_period_snapshot,
    get_periods,
    save_period_snapshot,
)
from backend.schemas import ApiResponse, UserContext

router = APIRouter(prefix="/api/clientes", tags=["historicos"])
LOGGER = logging.getLogger("socio_ai.historicos")


@router.get("/{cliente_id}/historicos", response_model=ApiResponse)
def get_historicos(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Obtiene lista de períodos disponibles con snapshots.

    Response:
        {
            "status": "ok",
            "data": {
                "periodos": [
                    {"periodo": "202501", "fecha": "2025-01-31T...", "snapshot_exists": true},
                    ...
                ]
            }
        }
    """
    authorize_cliente_access(cliente_id, user)

    try:
        periodos = get_periods(cliente_id)
        return ApiResponse(
            status="ok",
            data={"periodos": periodos},
        )
    except Exception as e:
        LOGGER.error(f"Error en get_historicos: {e}")
        return ApiResponse(
            status="error",
            message=f"Error obteniendo históricos: {str(e)}",
            data={},
        )


@router.post("/{cliente_id}/load-previous-period", response_model=ApiResponse)
def load_previous_period(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Carga snapshot del período anterior si existe.

    Response:
        {
            "status": "ok",
            "data": {
                "periodo_anterior": "202412",
                "snapshot_creado": true,
                "mensaje": "..."
            }
        }
    """
    authorize_cliente_access(cliente_id, user)

    try:
        # Obtener períodos disponibles
        periodos = get_periods(cliente_id)
        if not periodos:
            return ApiResponse(
                status="warning",
                message="No hay períodos anteriores disponibles",
                data={"snapshot_creado": False},
            )

        # El primer período en la lista es el más reciente
        periodo_anterior = periodos[0]["periodo"] if len(periodos) > 0 else None

        if not periodo_anterior:
            return ApiResponse(
                status="warning",
                message="No se pudo determinar período anterior",
                data={"snapshot_creado": False},
            )

        # Obtener snapshot del período anterior
        snapshot_data = get_period_snapshot(cliente_id, periodo_anterior)
        if snapshot_data:
            return ApiResponse(
                status="ok",
                data={
                    "periodo_anterior": periodo_anterior,
                    "snapshot_creado": True,
                    "snapshot": snapshot_data,
                },
            )
        else:
            return ApiResponse(
                status="warning",
                message=f"No se encontró snapshot para período {periodo_anterior}",
                data={"snapshot_creado": False},
            )

    except Exception as e:
        LOGGER.error(f"Error en load_previous_period: {e}")
        return ApiResponse(
            status="error",
            message=f"Error cargando período anterior: {str(e)}",
            data={},
        )


@router.post("/{cliente_id}/create-period-snapshot", response_model=ApiResponse)
def create_period_snapshot(
    cliente_id: str,
    periodo: str,
    activo: float = 0.0,
    pasivo: float = 0.0,
    patrimonio: float = 0.0,
    ingresos: float = 0.0,
    resultado_periodo: float = 0.0,
    ratio_values: dict = None,
    top_areas: list = None,
    hallazgos_count: int = 0,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Crea un snapshot completo de un período.

    Body:
        {
            "periodo": "202501",
            "activo": 1000000.0,
            "pasivo": 500000.0,
            ...
        }

    Response:
        {
            "status": "ok",
            "data": {
                "id": "...",
                "periodo": "202501",
                "fecha_snapshot": "..."
            }
        }
    """
    authorize_cliente_access(cliente_id, user)

    try:
        snapshot = PeriodSnapshot(
            cliente_id=cliente_id,
            periodo=periodo,
            activo=activo,
            pasivo=pasivo,
            patrimonio=patrimonio,
            ingresos=ingresos,
            resultado_periodo=resultado_periodo,
            ratio_values=ratio_values or {},
            top_areas=top_areas or [],
            hallazgos_count=hallazgos_count,
        )

        save_period_snapshot(cliente_id, periodo, snapshot.to_dict())

        LOGGER.info(f"period_snapshot created: {cliente_id} {periodo}")

        return ApiResponse(
            status="ok",
            data={
                "id": snapshot.id,
                "periodo": snapshot.periodo,
                "fecha_snapshot": snapshot.fecha_snapshot.isoformat(),
            },
        )
    except Exception as e:
        LOGGER.error(f"Error creating period snapshot: {e}")
        return ApiResponse(
            status="error",
            message=f"Error creando snapshot: {str(e)}",
            data={},
        )


@router.get("/{cliente_id}/historicos/{periodo}", response_model=ApiResponse)
def get_historico_periodo(
    cliente_id: str,
    periodo: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Obtiene el snapshot de un período específico.

    Response:
        {
            "status": "ok",
            "data": { ...snapshot fields... }
        }
    """
    authorize_cliente_access(cliente_id, user)

    snapshot = get_period_snapshot(cliente_id, periodo)
    if not snapshot:
        return ApiResponse(
            status="error",
            message=f"No existe snapshot para el período {periodo}.",
            data={},
        )

    return ApiResponse(status="ok", data=snapshot)
