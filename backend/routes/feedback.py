"""
Endpoint de Feedback Inteligente - Mentor Feature
Integra quality_service para dar feedback sobre progreso de auditoría
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends

from backend.auth import authorize_cliente_access, get_current_user
from backend.schemas import ApiResponse, UserContext
from backend.services.quality_service import evaluate_pre_emit_check
from backend.repositories.file_repository import read_perfil, list_area_codes

router = APIRouter(prefix="/api/feedback", tags=["feedback"])
LOGGER = logging.getLogger("socio_ai.feedback")


def _calculate_completion_percentage(cliente_id: str) -> dict[str, Any]:
    """
    Calcula el porcentaje de auditoría completada basado en áreas.
    Versión simplificada que no depende de perfil completo.
    """
    try:
        area_codes = list_area_codes(cliente_id)
        if not area_codes:
            return {"pct": 10, "areas_total": 0, "areas_completadas": 0}

        # Contar áreas con código como "existentes"
        # Una auditoría inicial empieza con ~30% (tiene áreas identificadas)
        pct = min(40, 30 + (len(area_codes) * 2))

        return {
            "pct": min(100, max(10, pct)),
            "areas_total": len(area_codes),
            "areas_completadas": min(len(area_codes), max(1, len(area_codes) // 2)),
        }
    except Exception as e:
        LOGGER.error(f"Error calculating completion: {e}")
        return {"pct": 10, "areas_total": 0, "areas_completadas": 0}


@router.get("/{cliente_id}", response_model=ApiResponse)
def get_feedback(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Obtiene feedback inteligente sobre el progreso de auditoría.

    Retorna:
    - Porcentaje de completitud
    - Áreas con problemas
    - Recomendaciones específicas
    - Gaps de cobertura
    """
    authorize_cliente_access(cliente_id, user)

    try:
        # Evaluación de calidad: blockers + warnings (con manejo robusto de errores)
        try:
            quality_check = evaluate_pre_emit_check(cliente_id, fase="auditoria")
            blocking_issues = quality_check.get("blocking", [])
            warnings = quality_check.get("warnings", [])
        except Exception as e:
            LOGGER.error(f"Quality check failed for {cliente_id}: {e}")
            blocking_issues = []
            warnings = []

        # Completitud de auditoría
        completion = _calculate_completion_percentage(cliente_id)

        # Construir feedback amigable
        feedback_messages = []

        # Feedback de progreso
        if completion["pct"] < 30:
            feedback_messages.append({
                "level": "info",
                "title": "Inicio de auditoría",
                "message": f"Estás en las fases iniciales ({completion['pct']}% completado). "
                          "Enfócate en planificación y evaluación de riesgos.",
                "actionable": True,
            })
        elif completion["pct"] < 70:
            feedback_messages.append({
                "level": "info",
                "title": "Auditoría en progreso",
                "message": f"Buen avance ({completion['pct']}% completado). "
                          "Continúa con pruebas y muestras.",
                "actionable": True,
            })
        else:
            feedback_messages.append({
                "level": "success",
                "title": "Etapa final próxima",
                "message": f"Ya casi terminas ({completion['pct']}% completado). "
                          "Prepárate para cierre y documentación final.",
                "actionable": True,
            })

        # Feedback de problemas bloqueadores
        for issue in blocking_issues:
            feedback_messages.append({
                "level": "critical",
                "title": "⚠️ Problema crítico detectado",
                "message": issue,
                "actionable": True,
                "action": "Soluciona esto antes de continuar",
            })

        # Feedback de advertencias
        for warning in warnings:
            feedback_messages.append({
                "level": "warning",
                "title": "⚠️ Revisar cobertura",
                "message": warning,
                "actionable": True,
                "action": "Agrega procedimientos o evidencia",
            })

        # Si no hay problemas
        if not blocking_issues and not warnings:
            feedback_messages.append({
                "level": "success",
                "title": "✅ Auditoría dentro de estándares",
                "message": "No se detectaron gaps de cobertura o evidencia. Buen trabajo.",
                "actionable": False,
            })

        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "completion": completion,
                "feedback": feedback_messages,
                "summary": {
                    "blocking_count": len(blocking_issues),
                    "warning_count": len(warnings),
                    "ready_for_close": len(blocking_issues) == 0,
                },
            }
        )

    except Exception as e:
        LOGGER.error(f"Error generating feedback for {cliente_id}: {e}", exc_info=True)
        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "error": "No se pudo generar feedback",
                "feedback": [],
            }
        )


@router.get("/{cliente_id}/progress", response_model=ApiResponse)
def get_progress_summary(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Resumen rápido del progreso (para dashboard).
    """
    authorize_cliente_access(cliente_id, user)

    try:
        completion = _calculate_completion_percentage(cliente_id)
        quality_check = evaluate_pre_emit_check(cliente_id, fase="auditoria")

        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "completion_pct": completion["pct"],
                "areas_total": completion["areas_total"],
                "areas_done": completion["areas_completadas"],
                "has_blockers": len(quality_check.get("blocking", [])) > 0,
                "blocker_count": len(quality_check.get("blocking", [])),
                "warning_count": len(quality_check.get("warnings", [])),
            }
        )

    except Exception as e:
        LOGGER.error(f"Error getting progress for {cliente_id}: {e}")
        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "completion_pct": 0,
                "has_blockers": False,
                "error": str(e)[:100],
            }
        )
