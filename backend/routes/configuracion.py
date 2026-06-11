"""
API endpoints para Configuración de Clientes
Maneja preguntas dinámicas por industria
"""
import logging
from typing import Any
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.auth import authorize_cliente_access, get_current_user
from backend.constants.configuracion_industrias import (
    obtener_preguntas,
    obtener_tipos_entidad,
    CONFIGURACION_INDUSTRIAS,
)
from backend.models.client import Client
from backend.models.cliente_configuration import ClienteConfiguration
from backend.schemas import ApiResponse, UserContext
from backend.utils.database import get_session
from backend.utils.api_errors import raise_api_error

router = APIRouter(prefix="/api/configuracion", tags=["configuracion"])
LOGGER = logging.getLogger("socio_ai.api.configuracion")


class GuardarConfiguracionRequest(BaseModel):
    tipo_entidad: str
    respuestas: dict[str, Any] | None = None


@router.get("/tipos-entidad", response_model=ApiResponse)
async def listar_tipos_entidad(
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Lista todos los tipos de entidad disponibles con sus preguntas
    """
    try:
        tipos = obtener_tipos_entidad()
        return ApiResponse(
            data={
                "total": len(tipos),
                "tipos": tipos,
            }
        )
    except Exception:
        LOGGER.exception("configuracion.listar_tipos failed")
        raise_api_error(
            code="ERROR_LISTING_TYPES",
            message="No se pudieron obtener los tipos de entidad.",
        )


@router.get("/{tipo_entidad}/preguntas", response_model=ApiResponse)
async def obtener_preguntas_dinámicas(
    tipo_entidad: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Obtiene preguntas dinámicas para un tipo de entidad

    Parámetros:
    - tipo_entidad: BANCO, RETAIL, SERVICIOS, MANUFACTURA, HOLDING, SALUD, EDUCACION
    """
    try:
        tipo_upper = tipo_entidad.upper().strip()

        preguntas = obtener_preguntas(tipo_upper)

        if not preguntas:
            raise_api_error(
                code="TIPO_ENTIDAD_NOT_FOUND",
                message=f"Tipo de entidad '{tipo_entidad}' no soportado",
            )

        return ApiResponse(
            data={
                "tipo_entidad": tipo_upper,
                "nombre": preguntas.get("nombre"),
                "preguntas": preguntas.get("preguntas", []),
                "total_preguntas": len(preguntas.get("preguntas", [])),
            }
        )
    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        LOGGER.exception("configuracion.preguntas failed")
        raise_api_error(
            code="ERROR_FETCHING_QUESTIONS",
            message="No se pudieron obtener las preguntas de configuracion.",
        )


@router.post("/{cliente_id}/guardar", response_model=ApiResponse)
async def guardar_configuracion(
    cliente_id: str,
    body: GuardarConfiguracionRequest,
    user: UserContext = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ApiResponse:
    """
    Guarda la configuración (respuestas a preguntas) de un cliente

    Body:
    - tipo_entidad: Tipo de entidad (BANCO, RETAIL, etc)
    - respuestas: Dict con respuestas (JSON)
    """
    authorize_cliente_access(cliente_id, user)
    try:
        # Obtener cliente
        cliente = session.query(Client).filter(Client.client_id == cliente_id).first()
        if not cliente:
            raise_api_error(
                code="CLIENT_NOT_FOUND",
                message=f"Cliente {cliente_id} no encontrado",
            )

        tipo_upper = body.tipo_entidad.upper().strip()

        # Validar tipo_entidad
        if tipo_upper not in CONFIGURACION_INDUSTRIAS:
            raise_api_error(
                code="INVALID_TIPO_ENTIDAD",
                message=f"Tipo de entidad '{body.tipo_entidad}' no soportado",
            )

        # Verificar si ya existe configuración
        config_existente = (
            session.query(ClienteConfiguration)
            .filter(
                ClienteConfiguration.client_id == cliente.id,
                ClienteConfiguration.tipo_entidad == tipo_upper,
            )
            .first()
        )

        if config_existente:
            # Actualizar
            config_existente.respuestas = body.respuestas or {}
            config_existente.updated_by = user.sub if user else "SYSTEM"
        else:
            # Crear nueva
            config = ClienteConfiguration(
                client_id=cliente.id,
                tipo_entidad=tipo_upper,
                respuestas=body.respuestas or {},
                updated_by=user.sub if user else "SYSTEM",
            )
            session.add(config)

        # Actualizar cliente
        cliente.tipo_entidad = tipo_upper

        session.commit()

        config_actualizada = (
            session.query(ClienteConfiguration)
            .filter(
                ClienteConfiguration.client_id == cliente.id,
                ClienteConfiguration.tipo_entidad == tipo_upper,
            )
            .first()
        )

        return ApiResponse(
            data=config_actualizada.to_dict() if config_actualizada else {},
        )

    except Exception as e:
        session.rollback()
        if hasattr(e, "status_code"):
            raise
        LOGGER.exception("configuracion.guardar failed")
        raise_api_error(
            code="ERROR_SAVING_CONFIGURATION",
            message="No se pudo guardar la configuracion del cliente.",
        )


@router.get("/{cliente_id}/obtener", response_model=ApiResponse)
async def obtener_configuracion(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ApiResponse:
    """
    Obtiene la configuración guardada de un cliente
    """
    authorize_cliente_access(cliente_id, user)
    try:
        cliente = session.query(Client).filter(Client.client_id == cliente_id).first()
        if not cliente:
            raise_api_error(
                code="CLIENT_NOT_FOUND",
                message=f"Cliente {cliente_id} no encontrado",
            )

        config = (
            session.query(ClienteConfiguration)
            .filter(ClienteConfiguration.client_id == cliente.id)
            .first()
        )

        if not config:
            return ApiResponse(
                data={
                    "cliente_id": cliente_id,
                    "configuracion": None,
                    "mensaje": "Cliente aún no tiene configuración",
                }
            )

        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "configuracion": config.to_dict(),
            }
        )

    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        LOGGER.exception("configuracion.obtener failed")
        raise_api_error(
            code="ERROR_FETCHING_CONFIGURATION",
            message="No se pudo obtener la configuracion del cliente.",
        )
