"""
API endpoints para gestionar clientes y auditorías
"""
from typing import Any, Optional, List
from datetime import datetime, date

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy import func

from backend.auth import get_current_user
from backend.models.client import Client
from backend.models.audit import Audit
from backend.schemas import UserContext, ApiResponse
from backend.utils.database import get_session
from backend.utils.api_errors import raise_api_error

router = APIRouter(prefix="/api/clientes", tags=["clientes"])


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
        clientes_data = [c.to_dict() for c in clientes]

        return ApiResponse(
            status="success",
            data={
                "total": len(clientes_data),
                "clientes": clientes_data,
            },
        )
    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_LISTING_CLIENTS",
            message=str(e),
        )


@router.get("/{cliente_id}", response_model=ApiResponse)
async def obtener_cliente(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    """
    Obtener información detallada de un cliente
    """
    try:
        cliente = session.query(Client).filter(Client.client_id == cliente_id).first()

        if not cliente:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="CLIENT_NOT_FOUND",
                message=f"Cliente {cliente_id} no encontrado",
            )

        return ApiResponse(status="success", data=cliente.to_dict())

    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_FETCHING_CLIENT",
            message=str(e),
        )


@router.post("", response_model=ApiResponse)
async def crear_cliente(
    client_id: str = Query(...),
    nombre: str = Query(...),
    ruc: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    tipo_entidad: Optional[str] = Query(None),
    contacto_nombre: Optional[str] = Query(None),
    contacto_email: Optional[str] = Query(None),
    periodo_actual: Optional[str] = Query(None),
    materialidad_general: Optional[float] = Query(None),
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    """
    Crear un nuevo cliente en la base de datos (PERSISTENCIA)

    Parámetros:
    - client_id: ID único (ej: bustamante_fabara_ip_cl)
    - nombre: Nombre del cliente
    - ruc: RUC/NIT (opcional)
    - sector: Sector económico (opcional)
    - tipo_entidad: Tipo de entidad (opcional)
    - contacto_nombre: Nombre del contacto (opcional)
    - contacto_email: Email de contacto (opcional)
    - periodo_actual: Período a auditar (ej: 2025)
    - materialidad_general: Materialidad general (opcional)
    """
    try:
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
            nombre=nombre,
            ruc=ruc,
            sector=sector,
            tipo_entidad=tipo_entidad,
            contacto_nombre=contacto_nombre,
            contacto_email=contacto_email,
            periodo_actual=periodo_actual,
            materialidad_general=materialidad_general,
            created_by=user.username if user else "SYSTEM",
            estado="ACTIVO",
        )

        session.add(nuevo_cliente)
        session.commit()

        return ApiResponse(
            status="success",
            message=f"Cliente {nombre} creado exitosamente",
            data=nuevo_cliente.to_dict(),
        )

    except Exception as e:
        session.rollback()
        if hasattr(e, "status_code"):
            raise
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_CREATING_CLIENT",
            message=str(e),
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
            status="success",
            data={
                "cliente_id": cliente_id,
                "total_auditorias": len(auditorias_data),
                "auditorias": auditorias_data,
            },
        )

    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_LISTING_AUDITS",
            message=str(e),
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
    try:
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
            status="success",
            message=f"Auditoría creada para período {periodo}",
            data=nueva_auditoria.to_dict(),
        )

    except Exception as e:
        session.rollback()
        if hasattr(e, "status_code"):
            raise
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_CREATING_AUDIT",
            message=str(e),
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
    try:
        auditoria = session.query(Audit).filter(Audit.id == audit_id).first()
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
            status="success",
            message=f"Auditoría actualizada a estado {estado}",
            data=auditoria.to_dict(),
        )

    except Exception as e:
        session.rollback()
        if hasattr(e, "status_code"):
            raise
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ERROR_UPDATING_AUDIT",
            message=str(e),
        )
