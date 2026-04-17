"""
Rutas para Reportes de Papeles de Trabajo
- Carta de Control (observaciones aprobadas por Socio)
- Hallazgos por L/S
- Resumen ejecutivo
"""
from typing import Any

from fastapi import APIRouter, Depends, status

from backend.auth import get_current_user
from backend.models.workpapers_observation import WorkpapersObservation
from backend.models.workpapers_template import WorkpapersTemplate
from backend.schemas import ApiResponse, UserContext
from backend.utils.api_errors import raise_api_error
from backend.utils.database import get_session

router = APIRouter(prefix="/api/reportes/papeles-trabajo", tags=["reportes-papeles"])


@router.get("/{cliente_id}/carta-control", response_model=ApiResponse)
def get_carta_control(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    """
    CARTA DE CONTROL - Observaciones aprobadas por Socio

    Retorna SOLO las observaciones que fueron FINALIZADAS por Socio
    Sin historial, solo conclusión final

    Estructura:
    - Por cada observación: Código papel, Nombre, Motivo, Observación Final, Efecto
    """
    try:
        # Obtener SOLO observaciones FINALIZADAS (aprobadas por Socio)
        observaciones = session.query(WorkpapersObservation).filter(
            WorkpapersObservation.status == "FINALIZADO"
        ).all()

        if not observaciones:
            return ApiResponse(
                data={
                    "cliente_id": cliente_id,
                    "tipo_reporte": "CARTA_CONTROL",
                    "total_hallazgos": 0,
                    "hallazgos": [],
                    "resumen": {
                        "sin_efecto": 0,
                        "con_efecto": 0,
                        "ajuste_requerido": 0,
                    }
                }
            )

        # Enriquecer con template (motivo)
        hallazgos = []
        resumen = {"sin_efecto": 0, "con_efecto": 0, "ajuste_requerido": 0}

        for obs in observaciones:
            # Obtener template para motivo
            template = session.query(WorkpapersTemplate).filter(
                WorkpapersTemplate.codigo == obs.codigo_papel
            ).first()

            hallazgo = {
                "codigo_papel": obs.codigo_papel,
                "nombre": template.nombre if template else "N/A",
                "motivo": template.descripcion if template else "N/A",
                "aseveracion": template.aseveracion if template else "N/A",
                "observacion_final": obs.observacion_final or obs.socio_comment,
                "efecto_financiero": obs.efecto_financiero or "SIN_EFECTO",
                "impacto": obs.impacto or "",
                "accion_recomendada": obs.accion_recomendada or "",
                "revisado_por_socio": obs.socio_by,
                "fecha_finalizacion": obs.socio_at.isoformat() if obs.socio_at else None,
            }

            hallazgos.append(hallazgo)

            # Contar por tipo
            efecto = hallazgo["efecto_financiero"]
            if efecto == "SIN_EFECTO":
                resumen["sin_efecto"] += 1
            elif efecto == "CON_EFECTO":
                resumen["con_efecto"] += 1
            elif efecto == "AJUSTE_REQUERIDO":
                resumen["ajuste_requerido"] += 1

        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "tipo_reporte": "CARTA_CONTROL",
                "total_hallazgos": len(hallazgos),
                "hallazgos": hallazgos,
                "resumen": {
                    "sin_efecto": resumen["sin_efecto"],
                    "con_efecto": resumen["con_efecto"],
                    "ajuste_requerido": resumen["ajuste_requerido"],
                    "total": len(hallazgos),
                }
            }
        )

    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="REPORTE_ERROR",
            message=f"Error generando carta de control: {str(e)}",
        )


@router.get("/{cliente_id}/hallazgos-por-ls", response_model=ApiResponse)
def get_hallazgos_por_ls(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    """
    HALLAZGOS POR LÍNEA DE CUENTA

    Agrupa observaciones finalizadas por L/S
    Útil para ver qué líneas tuvieron problemas
    """
    try:
        observaciones = session.query(WorkpapersObservation).filter(
            WorkpapersObservation.status == "FINALIZADO"
        ).all()

        # Agrupar por LS
        por_ls = {}

        for obs in observaciones:
            template = session.query(WorkpapersTemplate).filter(
                WorkpapersTemplate.codigo == obs.codigo_papel
            ).first()

            if not template:
                continue

            ls = template.ls
            if ls not in por_ls:
                por_ls[ls] = {
                    "total": 0,
                    "sin_efecto": 0,
                    "con_efecto": 0,
                    "hallazgos": [],
                }

            hallazgo = {
                "codigo": obs.codigo_papel,
                "nombre": template.nombre,
                "observacion": obs.observacion_final or obs.socio_comment,
                "efecto": obs.efecto_financiero or "SIN_EFECTO",
            }

            por_ls[ls]["hallazgos"].append(hallazgo)
            por_ls[ls]["total"] += 1

            if hallazgo["efecto"] == "SIN_EFECTO":
                por_ls[ls]["sin_efecto"] += 1
            else:
                por_ls[ls]["con_efecto"] += 1

        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "tipo_reporte": "HALLAZGOS_POR_LS",
                "lineas_con_hallazgos": sorted(por_ls.keys()),
                "hallazgos_por_ls": por_ls,
            }
        )

    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="REPORTE_ERROR",
            message=f"Error generando hallazgos por LS: {str(e)}",
        )


@router.get("/{cliente_id}/resumen-ejecutivo", response_model=ApiResponse)
def get_resumen_ejecutivo(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    """
    RESUMEN EJECUTIVO - Hallazgos principales

    Muestra:
    - Total de papeles auditados
    - Total de hallazgos identificados
    - Clasificación por efecto financiero
    - Papeles con hallazgos significativos
    """
    try:
        # Observaciones finalizadas
        observaciones = session.query(WorkpapersObservation).filter(
            WorkpapersObservation.status == "FINALIZADO"
        ).all()

        # Contar papeles totales
        total_papeles = session.query(WorkpapersTemplate).count()

        # Clasificar hallazgos
        sin_efecto = len([o for o in observaciones if o.efecto_financiero != "CON_EFECTO" and o.efecto_financiero != "AJUSTE_REQUERIDO"])
        con_efecto = len([o for o in observaciones if o.efecto_financiero == "CON_EFECTO"])
        ajuste_requerido = len([o for o in observaciones if o.efecto_financiero == "AJUSTE_REQUERIDO"])

        # Hallazgos significativos (con efecto)
        hallazgos_significativos = []
        for obs in observaciones:
            if obs.efecto_financiero in ["CON_EFECTO", "AJUSTE_REQUERIDO"]:
                template = session.query(WorkpapersTemplate).filter(
                    WorkpapersTemplate.codigo == obs.codigo_papel
                ).first()

                hallazgos_significativos.append({
                    "codigo": obs.codigo_papel,
                    "nombre": template.nombre if template else "N/A",
                    "impacto": obs.impacto or "",
                    "accion": obs.accion_recomendada or "",
                })

        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "tipo_reporte": "RESUMEN_EJECUTIVO",
                "estadisticas": {
                    "total_papeles_auditados": total_papeles,
                    "total_hallazgos": len(observaciones),
                    "hallazgos_sin_efecto": sin_efecto,
                    "hallazgos_con_efecto": con_efecto,
                    "ajustes_requeridos": ajuste_requerido,
                    "porcentaje_hallazgos": round((len(observaciones) / total_papeles * 100), 2) if total_papeles > 0 else 0,
                },
                "hallazgos_significativos": hallazgos_significativos,
                "conclusiones": [
                    "Auditados todos los papeles requeridos",
                    f"Se identificaron {len(observaciones)} observaciones",
                    f"{ajuste_requerido} requieren ajuste en EE.FF." if ajuste_requerido > 0 else "Sin ajustes requeridos en EE.FF.",
                ]
            }
        )

    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="REPORTE_ERROR",
            message=f"Error generando resumen ejecutivo: {str(e)}",
        )
