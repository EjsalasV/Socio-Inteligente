"""
API endpoints para Validaciones Avanzadas de Mayor
"""
from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.auth import authorize_cliente_access, get_current_user
from backend.schemas import ApiResponse, UserContext
from backend.services.mayor_service import load_mayor_canonical
from backend.services.mayor_validaciones_avanzadas import run_validaciones_avanzadas
from backend.utils.api_errors import raise_api_error
from backend.utils.database import get_session

router = APIRouter(prefix="/api/validaciones", tags=["validaciones"])


@router.get("/{cliente_id}/avanzadas", response_model=ApiResponse)
async def get_validaciones_avanzadas(
    cliente_id: str,
    fecha_cierre: str | None = Query(None),
    user: UserContext = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ApiResponse:
    """
    Ejecuta validaciones AVANZADAS de mayor

    Incluye:
    - Secuencial de asientos (detecta gaps)
    - Cuentas nuevas/eliminadas (comparativo 2024 vs 2025)
    - Mismatch período
    - Fechas anómalas
    - Mayor cuadra
    - Asientos anulados
    - Meses sin transacciones

    Parámetros:
    - cliente_id: ID del cliente
    - fecha_cierre: Fecha de cierre (YYYY-MM-DD) para validaciones
    """
    try:
        authorize_cliente_access(cliente_id, user)

        # Cargar mayor 2025
        df_2025, meta_2025 = load_mayor_canonical(cliente_id, periodo="2025")

        # Intentar cargar mayor 2024 si existe
        df_2024 = None
        meta_2024 = None
        try:
            df_2024, meta_2024 = load_mayor_canonical(cliente_id, periodo="2024")
        except:
            pass

        # Ejecutar validaciones
        validaciones = run_validaciones_avanzadas(
            df_2025=df_2025,
            df_2024=df_2024,
            fecha_cierre=fecha_cierre,
            tolerance_mayor=0.01,
        )

        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "validaciones": validaciones,
                "tiene_comparativo_2024": df_2024 is not None and len(df_2024) > 0,
                "source": {
                    "2025": meta_2025,
                    "2024": meta_2024,
                },
            }
        )

    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        raise_api_error(
            code="ERROR_RUNNING_VALIDATIONS",
            message=str(e),
        )


@router.get("/{cliente_id}/resumen-validaciones", response_model=ApiResponse)
async def get_resumen_validaciones(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Obtiene resumen ejecutivo de validaciones

    Retorna:
    - Status general (OK, WARNING, ERROR)
    - Problemas críticos encontrados
    - Recomendaciones
    """
    try:
        authorize_cliente_access(cliente_id, user)

        df_2025, _ = load_mayor_canonical(cliente_id, periodo="2025")
        df_2024 = None
        try:
            df_2024, _ = load_mayor_canonical(cliente_id, periodo="2024")
        except:
            pass

        validaciones = run_validaciones_avanzadas(
            df_2025=df_2025,
            df_2024=df_2024,
        )

        # Analizar críticos
        criticos = []

        if validaciones["mayor_cuadra"]["status"] == "error":
            criticos.append(
                {
                    "tipo": "error",
                    "mensaje": f"Mayor no cuadra: {validaciones['mayor_cuadra']['diferencia']:,.2f}",
                }
            )

        if validaciones["secuencial_asientos"]["status"] == "error":
            criticos.append(
                {
                    "tipo": "error",
                    "mensaje": f"Gaps en secuencial: {validaciones['secuencial_asientos']['gaps_count']}",
                }
            )

        if validaciones["mismatch_periodo"]["status"] == "error":
            criticos.append(
                {
                    "tipo": "error",
                    "mensaje": f"Mismatch período en {validaciones['mismatch_periodo']['count']} cuentas",
                }
            )

        if validaciones["cuentas_nuevas_eliminadas"]["status"] == "warning":
            criticos.append(
                {
                    "tipo": "warning",
                    "mensaje": f"Nuevas cuentas: {validaciones['cuentas_nuevas_eliminadas']['nuevas_count']}, Eliminadas: {validaciones['cuentas_nuevas_eliminadas']['eliminadas_count']}",
                }
            )

        # Determinar status general
        status_general = "ok"
        if len(criticos) > 0:
            status_general = "warning" if all(c["tipo"] == "warning" for c in criticos) else "error"

        return ApiResponse(
            data={
                "cliente_id": cliente_id,
                "status_general": status_general,
                "total_problemas": len(criticos),
                "criticos": criticos,
                "recomendaciones": _generar_recomendaciones(validaciones),
            }
        )

    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        raise_api_error(
            code="ERROR_GETTING_SUMMARY",
            message=str(e),
        )


def _generar_recomendaciones(validaciones: dict) -> list[str]:
    """Genera recomendaciones basadas en validaciones"""
    recomendaciones = []

    if validaciones["mayor_cuadra"]["status"] == "error":
        recomendaciones.append(
            f"Revisar integridad del mayor. Diferencia: {validaciones['mayor_cuadra']['diferencia']:,.2f}"
        )

    if validaciones["secuencial_asientos"]["status"] == "error":
        recomendaciones.append(
            "Validar que no hay asientos faltantes o borrados"
        )

    if validaciones["mismatch_periodo"]["status"] == "error":
        recomendaciones.append(
            "Revisar reclasificaciones entre períodos (deben tener asientos de soporte)"
        )

    if validaciones["fechas_anomalas"]["anomalias_count"] > 0:
        recomendaciones.append(
            f"Revisar {validaciones['fechas_anomalas']['anomalias_count']} fechas anómalas (domingos, post-cierre, etc)"
        )

    if len(validaciones["meses_sin_transacciones"]["meses_sin_movimiento"]) > 0:
        recomendaciones.append(
            f"Meses sin transacciones: {', '.join(validaciones['meses_sin_transacciones']['meses_sin_movimiento'])}"
        )

    if validaciones["asientos_anulados"]["count"] > 0:
        recomendaciones.append(
            f"Revisar {validaciones['asientos_anulados']['count']} asientos anulados"
        )

    if not recomendaciones:
        recomendaciones.append("Mayor validado correctamente")

    return recomendaciones
