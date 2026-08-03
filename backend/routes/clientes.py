"""
API endpoints para gestionar clientes y auditorías
"""
import logging
from typing import Any, Optional, List
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import func

from backend.auth import authorize_cliente_access, get_current_user
from backend.models.client import Client
from backend.models.audit import Audit
from backend.schemas import UserContext, ApiResponse, ClienteCreateRequest, ClienteUpdateRequest
from backend.utils.database import get_session
from backend.utils.api_errors import raise_api_error
from backend.services.client_deletion_service import permanently_delete_client
from backend.services.client_progress_service import build_client_progress
from backend.repositories.file_repository import slugify_cliente_id

router = APIRouter(prefix="/api/clientes", tags=["clientes"])
LOGGER = logging.getLogger("socio_ai.api.clientes")

_MANAGEMENT_ROLES = {"admin", "manager", "socio"}


def _user_can_access(cliente_id: str, user: UserContext) -> bool:
    """True si el usuario tiene acceso al cliente segun sus asignaciones."""
    try:
        authorize_cliente_access(cliente_id, user)
        return True
    except HTTPException:
        return False


def _require_management_role(user: UserContext, message: str) -> None:
    if user.role.lower() not in _MANAGEMENT_ROLES:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="INSUFFICIENT_ROLE",
            message=message,
        )


# ============= CLIENTES =============

@router.get("", response_model=ApiResponse)
async def listar_clientes(
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    """
    Listar todos los clientes con información básica
    """
    try:
        clientes = session.query(Client).order_by(Client.nombre).all()
        clientes_data = [
            c.to_dict()
            for c in clientes
            if c is not None and c.estado != "ARCHIVADO" and _user_can_access(c.client_id, user)
        ]

        return ApiResponse(
            data={
                "total": len(clientes_data),
                "clientes": clientes_data,
            },
        )
    except Exception:
        LOGGER.exception("clientes.listar failed")
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_LISTING_CLIENTS",
            message="No se pudo obtener la lista de clientes.",
            action_hint="Reintenta en unos segundos. Si persiste, contacta soporte.",
            retryable=True,
        )


@router.get("/progress", response_model=ApiResponse)
async def listar_progreso_clientes(
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    clientes = session.query(Client).order_by(Client.nombre).all()
    progress = [
        build_client_progress(cliente.client_id)
        for cliente in clientes
        if cliente is not None and cliente.estado != "ARCHIVADO" and _user_can_access(cliente.client_id, user)
    ]
    return ApiResponse(data={"clients": progress})


@router.get("/{cliente_id}", response_model=ApiResponse)
async def obtener_cliente(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    """
    Obtener información detallada de un cliente
    """
    authorize_cliente_access(cliente_id, user)
    try:
        cliente = session.query(Client).filter(Client.client_id == cliente_id).first()

        if not cliente:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="CLIENT_NOT_FOUND",
                message=f"Cliente {cliente_id} no encontrado",
            )

        return ApiResponse(data=cliente.to_dict())

    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        LOGGER.exception("clientes.obtener failed")
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_FETCHING_CLIENT",
            message="No se pudo obtener el cliente.",
            action_hint="Reintenta en unos segundos. Si persiste, contacta soporte.",
            retryable=True,
        )


@router.post("", response_model=ApiResponse)
async def crear_cliente(
    body: ClienteCreateRequest,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    """
    Crear un nuevo cliente en la base de datos (PERSISTENCIA)

    Body:
    - nombre: Nombre del cliente (requerido)
    - cliente_id: ID único (ej: bustamante_fabara_ip_cl) - si no se proporciona, se genera
    - sector: Sector económico (opcional)
    """
    try:
        # Verificar rol - solo admin, manager, y socio pueden crear clientes
        _require_management_role(user, "Solo perfiles administradores pueden crear clientes.")

        # El ID también se usa como nombre de directorio. Normalizarlo antes
        # de persistir evita clientes huérfanos cuando el usuario escribe
        # códigos con puntos, espacios, tildes u otros caracteres no seguros.
        client_id = slugify_cliente_id(body.cliente_id or body.nombre)
        if not client_id:
            raise_api_error(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="INVALID_CLIENT_ID",
                message="El código del cliente no contiene caracteres utilizables.",
                action_hint="Usa letras y números; SocioAI convertirá separadores en guiones bajos.",
            )

        # Verificar si cliente ya existe
        existing = session.query(Client).filter(Client.client_id == client_id).first()
        if existing:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="CLIENT_ALREADY_EXISTS",
                message=f"Cliente {client_id} ya existe",
            )

        # Crear cliente
        nuevo_cliente = Client(
            client_id=client_id,
            nombre=body.nombre,
            sector=body.sector,
            tipo_entidad=body.tipo_entidad,
            tamano=body.tamano,
            normativa=body.normativa or "NIIF",
            created_by=user.sub if user else "SYSTEM",
            estado="ACTIVO",
        )

        session.add(nuevo_cliente)
        session.commit()
        session.refresh(nuevo_cliente)

        return ApiResponse(
            data=nuevo_cliente.to_dict(),
        )

    except Exception as e:
        session.rollback()
        if hasattr(e, "status_code"):
            raise
        LOGGER.exception("clientes.crear failed")
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_CREATING_CLIENT",
            message="No se pudo crear el cliente.",
            action_hint="Reintenta en unos segundos. Si persiste, contacta soporte.",
            retryable=True,
        )


@router.patch("/{cliente_id}", response_model=ApiResponse)
async def actualizar_cliente(
    cliente_id: str,
    body: ClienteUpdateRequest,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    """
    Actualiza metadatos base del cliente para onboarding y configuración.
    """
    authorize_cliente_access(cliente_id, user)
    try:
        _require_management_role(user, "Solo perfiles administradores pueden actualizar clientes.")

        cliente = session.query(Client).filter(Client.client_id == cliente_id).first()
        if not cliente:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="CLIENT_NOT_FOUND",
                message=f"Cliente {cliente_id} no encontrado",
            )

        if body.nombre is not None:
            cliente.nombre = body.nombre.strip() or cliente.nombre
        if body.sector is not None:
            cliente.sector = body.sector.strip() or None
        if body.tipo_entidad is not None:
            cliente.tipo_entidad = body.tipo_entidad.strip().upper() or None
        if body.tamano is not None:
            cliente.tamano = body.tamano.strip() or None
        if body.normativa is not None:
            cliente.normativa = body.normativa.strip() or "NIIF"

        session.commit()
        session.refresh(cliente)
        return ApiResponse(data=cliente.to_dict())
    except Exception as e:
        session.rollback()
        if hasattr(e, "status_code"):
            raise
        LOGGER.exception("clientes.actualizar failed")
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_UPDATING_CLIENT",
            message="No se pudo actualizar el cliente.",
            action_hint="Reintenta en unos segundos. Si persiste, contacta soporte.",
            retryable=True,
        )


@router.delete("/{cliente_id}", response_model=ApiResponse)
async def archivar_cliente(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    """
    Archivado lógico de un cliente.

    No elimina datos: marca el cliente como ARCHIVADO y deja de mostrarse
    en la cartera. Los datos del encargo se conservan.
    """
    authorize_cliente_access(cliente_id, user)
    try:
        _require_management_role(user, "Solo perfiles administradores pueden archivar clientes.")

        cliente = session.query(Client).filter(Client.client_id == cliente_id).first()
        if not cliente:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="CLIENT_NOT_FOUND",
                message=f"Cliente {cliente_id} no encontrado",
            )

        cliente.estado = "ARCHIVADO"
        session.commit()
        session.refresh(cliente)
        return ApiResponse(data=cliente.to_dict())
    except Exception as e:
        session.rollback()
        if hasattr(e, "status_code"):
            raise
        LOGGER.exception("clientes.archivar failed")
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_ARCHIVING_CLIENT",
            message="No se pudo archivar el cliente.",
            action_hint="Reintenta en unos segundos. Si persiste, contacta soporte.",
            retryable=True,
        )


class PermanentDeleteRequest(BaseModel):
    confirmation: str = Field(min_length=1, max_length=64)


@router.delete("/{cliente_id}/permanent", response_model=ApiResponse)
async def borrar_cliente_permanentemente(
    cliente_id: str,
    body: PermanentDeleteRequest,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    _require_management_role(user, "Solo perfiles administradores pueden borrar clientes definitivamente.")
    if body.confirmation.strip() != cliente_id:
        raise_api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="PERMANENT_DELETE_CONFIRMATION_MISMATCH",
            message="La confirmación no coincide exactamente con el ID del cliente.",
        )
    cliente = session.query(Client).filter(Client.client_id == cliente_id).first()
    if not cliente:
        raise_api_error(status_code=status.HTTP_404_NOT_FOUND, code="CLIENT_NOT_FOUND", message=f"Cliente {cliente_id} no encontrado")
    try:
        deleted = permanently_delete_client(session, cliente)
        LOGGER.warning("Cliente eliminado permanentemente: cliente=%s usuario=%s detalle=%s", cliente_id, user.sub, deleted)
        return ApiResponse(data={"deleted": True, "cliente_id": cliente_id, "details": deleted})
    except Exception as exc:
        session.rollback()
        LOGGER.exception("clientes.permanent_delete failed")
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_PERMANENTLY_DELETING_CLIENT",
            message="No se pudo borrar definitivamente el cliente.",
            action_hint="Los datos se conservaron si la eliminación no pudo completarse.",
        )


# ============= AUDITORÍAS =============

@router.get("/{cliente_id}/auditorias", response_model=ApiResponse)
async def listar_auditorias(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    """
    Listar todas las auditorías de un cliente (historial de períodos)
    """
    authorize_cliente_access(cliente_id, user)
    try:
        cliente = session.query(Client).filter(Client.client_id == cliente_id).first()
        if not cliente:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="CLIENT_NOT_FOUND",
                message=f"Cliente {cliente_id} no encontrado",
            )

        auditorias = (
            session.query(Audit)
            .filter(Audit.client_id == cliente.id)
            .order_by(Audit.periodo.desc())
            .all()
        )

        auditorias_data = [a.to_dict() for a in auditorias]

        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "total_auditorias": len(auditorias_data),
                "auditorias": auditorias_data,
            },
        )

    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        LOGGER.exception("clientes.listar_auditorias failed")
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_LISTING_AUDITS",
            message="No se pudieron obtener las auditorias del cliente.",
            action_hint="Reintenta en unos segundos. Si persiste, contacta soporte.",
            retryable=True,
        )


@router.post("/{cliente_id}/auditorias", response_model=ApiResponse)
async def crear_auditoria(
    cliente_id: str,
    periodo: str = Query(..., description="Ej: 2025"),
    socio_asignado: Optional[str] = Query(None),
    senior_asignado: Optional[str] = Query(None),
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    """
    Crear una nueva auditoría para un cliente y período

    Parámetros:
    - cliente_id: ID del cliente
    - periodo: Período a auditar (ej: 2025)
    - socio_asignado: Socio responsable (opcional)
    - senior_asignado: Senior responsable (opcional)
    """
    authorize_cliente_access(cliente_id, user)
    try:
        _require_management_role(user, "Solo perfiles administradores pueden crear auditorias.")

        cliente = session.query(Client).filter(Client.client_id == cliente_id).first()
        if not cliente:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="CLIENT_NOT_FOUND",
                message=f"Cliente {cliente_id} no encontrado",
            )

        # Verificar si auditoría para período ya existe
        existing = (
            session.query(Audit)
            .filter(Audit.client_id == cliente.id, Audit.periodo == periodo)
            .first()
        )
        if existing:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="AUDIT_ALREADY_EXISTS",
                message=f"Auditoría para período {periodo} ya existe",
            )

        codigo_auditoria = f"{cliente_id.upper()}_{periodo}"

        nueva_auditoria = Audit(
            client_id=cliente.id,
            codigo_auditoria=codigo_auditoria,
            periodo=periodo,
            socio_asignado=socio_asignado,
            senior_asignado=senior_asignado,
            estado="PLANEACIÓN",
            fecha_inicio=datetime.now().date(),
        )

        session.add(nueva_auditoria)
        session.commit()

        return ApiResponse(
            data=nueva_auditoria.to_dict(),
        )

    except Exception as e:
        session.rollback()
        if hasattr(e, "status_code"):
            raise
        LOGGER.exception("clientes.crear_auditoria failed")
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_CREATING_AUDIT",
            message="No se pudo crear la auditoria.",
            action_hint="Reintenta en unos segundos. Si persiste, contacta soporte.",
            retryable=True,
        )


@router.put("/{cliente_id}/auditorias/{audit_id}", response_model=ApiResponse)
async def actualizar_auditoria_estado(
    cliente_id: str,
    audit_id: int,
    estado: str = Query(..., description="PLANEACIÓN, EJECUCIÓN, REPORTE, FINALIZADO"),
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    """
    Actualizar estado de una auditoría
    """
    authorize_cliente_access(cliente_id, user)
    try:
        _require_management_role(user, "Solo perfiles administradores pueden actualizar auditorias.")

        # La auditoria debe pertenecer al cliente indicado en la ruta.
        auditoria = (
            session.query(Audit)
            .join(Client, Audit.client_id == Client.id)
            .filter(Audit.id == audit_id, Client.client_id == cliente_id)
            .first()
        )
        if not auditoria:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="AUDIT_NOT_FOUND",
                message=f"Auditoría {audit_id} no encontrada",
            )

        # Validar estado
        estados_validos = ["PLANEACIÓN", "EJECUCIÓN", "REPORTE", "FINALIZADO", "ARCHIVADO"]
        if estado not in estados_validos:
            raise_api_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="INVALID_STATE",
                message=f"Estado inválido. Valores válidos: {', '.join(estados_validos)}",
            )

        auditoria.estado = estado
        auditoria.updated_at = datetime.utcnow()

        session.commit()

        return ApiResponse(
            data=auditoria.to_dict(),
        )

    except Exception as e:
        session.rollback()
        if hasattr(e, "status_code"):
            raise
        LOGGER.exception("clientes.actualizar_auditoria failed")
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_UPDATING_AUDIT",
            message="No se pudo actualizar la auditoria.",
            action_hint="Reintenta en unos segundos. Si persiste, contacta soporte.",
            retryable=True,
        )
