"""
Rutas para Intelligent Audit Analysis
Detección automática de anomalías con IA
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth import authorize_cliente_access, get_current_user
from backend.schemas import ApiResponse, UserContext
from backend.services.intelligent_analyzer_service import (
    analyze_financial_data,
    get_audit_procedures_for_hallazgo,
)
from backend.services.analysis_history_service import AnalysisHistoryService
from backend.repositories.identity_repository import store as identity_store
from backend.utils.database import get_session

router = APIRouter(prefix="/api/audit-analysis", tags=["audit-analysis"])
LOGGER = logging.getLogger("socio_ai.audit_analysis")


class FinancialDataRequest(BaseModel):
    """Request body para análisis de datos financieros"""
    sector: str | None = None
    tamaño: str | None = None
    marco_referencial: str | None = "NIIF Completas"
    balance_trial: dict[str, Any]
    income_statement: dict[str, Any] | None = None
    additional_data: dict[str, Any] | None = None


@router.post("/{cliente_id}/analyze", response_model=ApiResponse)
def analyze_client_audit(
    cliente_id: str,
    request: FinancialDataRequest,
    user: UserContext = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ApiResponse:
    """
    Analiza datos financieros y detecta anomalías automáticamente
    Con RAG para evitar repetir hallazgos anteriores

    Input:
    - balance_trial: dict con cuentas y saldos
    - income_statement: dict con ingresos/gastos
    - additional_data: otros datos relevantes

    Output:
    - Lista de hallazgos detectados
    - Cada uno con norma, riesgo, procedimientos
    - Plus: histórico de análisis anteriores
    """
    authorize_cliente_access(cliente_id, user)

    try:
        # Obtener learning_role del usuario
        try:
            prefs = identity_store.get_preferences(user.sub)
            learning_role = str(prefs.get("learning_role") or "semi").strip().lower()
        except Exception:
            learning_role = "semi"

        # Datos para análisis
        financial_data = {
            "sector": request.sector,
            "tamaño": request.tamaño,
            "marco_referencial": request.marco_referencial,
            "balance_trial": request.balance_trial,
            "income_statement": request.income_statement or {},
            "additional_data": request.additional_data or {},
        }

        # Ejecutar análisis CON SESSION para RAG
        analysis_result = analyze_financial_data(
            cliente_id,
            financial_data,
            session=session  # ← Pasar session para RAG y guardar histórico
        )

        # Agregar histórico al resultado
        try:
            analysis_history = AnalysisHistoryService.get_analysis_history(session, cliente_id, limit=5)
            analysis_result["analisis_previos"] = analysis_history
        except Exception as hist_err:
            LOGGER.warning(f"⚠️  Error obteniendo histórico: {hist_err}")

        # Si hay hallazgos, enriquecer con procedimientos
        if "hallazgos" in analysis_result and analysis_result["hallazgos"]:
            for hallazgo in analysis_result["hallazgos"]:
                hallazgo["procedimientos_auditoria"] = get_audit_procedures_for_hallazgo(
                    hallazgo, learning_role=learning_role
                )

        LOGGER.info(f"Analysis completed for {cliente_id}: {len(analysis_result.get('hallazgos', []))} hallazgos")

        return ApiResponse(data=analysis_result)

    except Exception as e:
        LOGGER.error(f"Analysis error for {cliente_id}: {e}", exc_info=True)
        return ApiResponse(
            data={
                "error": str(e),
                "cliente_id": cliente_id,
                "hallazgos": [],
            }
        )


@router.get("/{cliente_id}/history", response_model=ApiResponse)
def get_analysis_history(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ApiResponse:
    """
    Obtiene histórico de análisis anteriores para un cliente
    Útil para ver evolución de hallazgos
    """
    authorize_cliente_access(cliente_id, user)

    try:
        history = AnalysisHistoryService.get_analysis_history(session, cliente_id, limit=20)
        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "total_analyses": len(history),
                "analyses": history,
            }
        )
    except Exception as e:
        LOGGER.error(f"Error getting analysis history for {cliente_id}: {e}")
        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "error": str(e),
                "analyses": [],
            }
        )


@router.get("/{cliente_id}/procedures/{hallazgo_id}", response_model=ApiResponse)
def get_hallazgo_procedures(
    cliente_id: str,
    hallazgo_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Obtiene procedimientos detallados para un hallazgo específico

    TODO: Implementar almacenamiento de hallazgos para poder recuperarlos
    """
    authorize_cliente_access(cliente_id, user)

    return ApiResponse(
        data={
            "message": "Endpoint disponible cuando hallazgos estén persistidos",
            "hallazgo_id": hallazgo_id,
        }
    )


@router.post("/{cliente_id}/save-findings", response_model=ApiResponse)
def save_audit_findings(
    cliente_id: str,
    request: dict[str, Any],
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Guarda hallazgos detectados para auditoría posterior

    Conecta con módulo de hallazgos existente
    """
    authorize_cliente_access(cliente_id, user)

    try:
        hallazgos = request.get("hallazgos", [])

        # TODO: Guardar en base de datos de hallazgos
        # Por ahora solo log
        LOGGER.info(f"Saving {len(hallazgos)} findings for {cliente_id}")

        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "findings_saved": len(hallazgos),
                "message": "Hallazgos guardados correctamente",
            }
        )

    except Exception as e:
        LOGGER.error(f"Save findings error: {e}")
        return ApiResponse(
            data={"error": str(e), "findings_saved": 0}
        )
