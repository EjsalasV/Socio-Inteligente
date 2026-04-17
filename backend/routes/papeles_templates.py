"""
Rutas para papeles de trabajo clasificados y observaciones
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.models.workpapers_template import WorkpapersTemplate
from backend.models.workpapers_observation import WorkpapersObservation, WorkpapersObservationHistory
from backend.schemas import ApiResponse, UserContext
from backend.utils.api_errors import raise_api_error
from backend.utils.database import get_session
from datetime import datetime

router = APIRouter(prefix="/api/papeles-trabajo", tags=["papeles-templates"])


@router.get("/{cliente_id}/templates/ls/{ls}", response_model=ApiResponse)
def get_templates_by_ls(
    cliente_id: str,
    ls: int,
    user: UserContext = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ApiResponse:
    """
    Obtiene todos los papeles de una línea de cuenta (LS)
    Ordenados por importancia (CRITICO → ALTO → MEDIO → BAJO)

    Ejemplo: GET /api/papeles-trabajo/cliente-123/templates/ls/130
    Retorna todos los papeles del LS 130 (Cuentas por Cobrar)
    """
    try:
        # Importancia order
        importancia_order = {
            "CRITICO": 0,
            "ALTO": 1,
            "MEDIO": 2,
            "BAJO": 3,
        }

        templates = session.query(WorkpapersTemplate).filter(
            WorkpapersTemplate.ls == ls
        ).all()

        if not templates:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="NO_TEMPLATES",
                message=f"No se encontraron papeles para LS {ls}",
            )

        # Ordenar por importancia
        templates.sort(key=lambda x: importancia_order.get(x.importancia, 4))

        return ApiResponse(
            data={
                "ls": ls,
                "total": len(templates),
                "templates": [t.to_dict() for t in templates],
            }
        )

    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="TEMPLATES_ERROR",
            message=f"Error obteniendo papeles: {str(e)}",
        )


@router.get("/templates", response_model=ApiResponse)
def get_all_templates(
    user: UserContext = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ApiResponse:
    """Obtiene todos los papeles de trabajo (para dropdown, búsqueda, etc.)"""
    try:
        templates = session.query(WorkpapersTemplate).all()

        # Agrupar por LS
        by_ls = {}
        for t in templates:
            if t.ls not in by_ls:
                by_ls[t.ls] = []
            by_ls[t.ls].append(t.to_dict())

        return ApiResponse(
            data={
                "total": len(templates),
                "lineas_de_cuenta": sorted(by_ls.keys()),
                "templates_by_ls": by_ls,
            }
        )

    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="TEMPLATES_ERROR",
            message=f"Error obteniendo papeles: {str(e)}",
        )


@router.post("/{cliente_id}/observations/{file_id}/{codigo_papel}", response_model=ApiResponse)
async def create_observation(
    cliente_id: str,
    file_id: int,
    codigo_papel: str,
    observation_text: str,
    user: UserContext = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ApiResponse:
    """
    Crea o actualiza observación para un papel

    El rol del usuario (Junior, Senior, Socio) se detecta automáticamente
    y se guarda en la columna correspondiente
    """
    try:
        # Validar que el papel existe
        template = session.query(WorkpapersTemplate).filter(
            WorkpapersTemplate.codigo == codigo_papel
        ).first()

        if not template:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="TEMPLATE_NOT_FOUND",
                message=f"Papel {codigo_papel} no existe",
            )

        # Obtener o crear observación
        obs = session.query(WorkpapersObservation).filter(
            WorkpapersObservation.file_id == file_id,
            WorkpapersObservation.codigo_papel == codigo_papel,
        ).first()

        if not obs:
            obs = WorkpapersObservation(
                file_id=file_id,
                codigo_papel=codigo_papel,
            )

        # Detectar rol del usuario (simplificado)
        # En producción, esto vendría del JWT token o DB
        rol = user.role.lower() if hasattr(user, 'role') else "junior"

        # Guardar observación según rol
        if rol == "junior":
            obs.junior_observation = observation_text
            obs.junior_by = user.sub
            obs.junior_at = datetime.utcnow()
            obs.junior_status = "ESCRITO"
            obs.status = "PENDIENTE_SENIOR"

        elif rol == "senior":
            obs.senior_comment = observation_text
            obs.senior_by = user.sub
            obs.senior_at = datetime.utcnow()
            obs.senior_review = "REVISADO"
            obs.status = "PENDIENTE_SOCIO"

        elif rol == "socio":
            obs.socio_comment = observation_text
            obs.socio_by = user.sub
            obs.socio_at = datetime.utcnow()
            obs.socio_review = "FINALIZADO"
            obs.status = "FINALIZADO"

        session.add(obs)

        # Registrar en historial
        history = WorkpapersObservationHistory(
            observation_id=obs.id if obs.id else None,
            rol=rol,
            accion=f"{rol}_escribio",
            contenido_nuevo=observation_text,
            usuario=user.sub,
        )
        session.add(history)

        session.commit()

        return ApiResponse(
            data={
                "file_id": file_id,
                "codigo_papel": codigo_papel,
                "observation": obs.to_dict(),
            }
        )

    except Exception as e:
        session.rollback()
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="OBSERVATION_ERROR",
            message=f"Error guardando observación: {str(e)}",
        )


@router.get("/{cliente_id}/observations/{file_id}/{codigo_papel}", response_model=ApiResponse)
def get_observation(
    cliente_id: str,
    file_id: int,
    codigo_papel: str,
    user: UserContext = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ApiResponse:
    """Obtiene observación y su historial para un papel"""
    try:
        obs = session.query(WorkpapersObservation).filter(
            WorkpapersObservation.file_id == file_id,
            WorkpapersObservation.codigo_papel == codigo_papel,
        ).first()

        if not obs:
            return ApiResponse(
                data={
                    "file_id": file_id,
                    "codigo_papel": codigo_papel,
                    "observation": None,
                    "history": [],
                }
            )

        # Obtener historial
        history = session.query(WorkpapersObservationHistory).filter(
            WorkpapersObservationHistory.observation_id == obs.id
        ).all()

        return ApiResponse(
            data={
                "file_id": file_id,
                "codigo_papel": codigo_papel,
                "observation": obs.to_dict(),
                "history": [h.to_dict() for h in history],
            }
        )

    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="OBSERVATION_ERROR",
            message=f"Error obteniendo observación: {str(e)}",
        )


@router.post("/{cliente_id}/observations/{file_id}/{codigo_papel}/approve", response_model=ApiResponse)
async def approve_observation(
    cliente_id: str,
    file_id: int,
    codigo_papel: str,
    review_status: str,  # APROBADO, RECHAZADO, NO_APLICA
    comment: str = "",
    user: UserContext = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ApiResponse:
    """
    Senior o Socio aprueban/rechazan/comentan observación
    """
    try:
        rol = user.role.lower() if hasattr(user, 'role') else "senior"

        obs = session.query(WorkpapersObservation).filter(
            WorkpapersObservation.file_id == file_id,
            WorkpapersObservation.codigo_papel == codigo_papel,
        ).first()

        if not obs:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="OBSERVATION_NOT_FOUND",
                message="Observación no existe",
            )

        # Actualizar según rol
        if rol == "senior":
            obs.senior_review = review_status
            obs.senior_comment = comment
            obs.senior_by = user.sub
            obs.senior_at = datetime.utcnow()

        elif rol == "socio":
            obs.socio_review = review_status
            obs.socio_comment = comment
            obs.socio_by = user.sub
            obs.socio_at = datetime.utcnow()

        # Actualizar estado final
        if review_status == "APROBADO":
            obs.status = "APROBADO"
        elif review_status == "RECHAZADO":
            obs.status = "RECHAZADO"
        elif review_status == "NO_APLICA":
            obs.status = "NO_APLICA"

        # Registrar en historial
        history = WorkpapersObservationHistory(
            observation_id=obs.id,
            rol=rol,
            accion=f"{rol}_{review_status.lower()}",
            contenido_nuevo=comment,
            usuario=user.sub,
        )
        session.add(history)
        session.commit()

        return ApiResponse(
            data={
                "file_id": file_id,
                "codigo_papel": codigo_papel,
                "observation": obs.to_dict(),
            }
        )

    except Exception as e:
        session.rollback()
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="APPROVAL_ERROR",
            message=f"Error aprobando observación: {str(e)}",
        )
