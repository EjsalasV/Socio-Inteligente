from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.auth import authorize_cliente_access, get_current_user
from backend.schemas import (
    AreaRiesgo,
    BalanceKPIs,
    DashboardResponse,
    ProgresoEncargo,
    UserContext,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _to_str(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


@router.get("/{cliente_id}", response_model=DashboardResponse)
def get_dashboard(cliente_id: str, user: UserContext = Depends(get_current_user)) -> DashboardResponse:
    authorize_cliente_access(cliente_id, user)

    from analysis.lector_tb import obtener_resumen_tb
    from analysis.ranking_areas import calcular_ranking_areas
    from domain.services.leer_perfil import leer_perfil
    from domain.services.materialidad_service import calcular_materialidad

    perfil = leer_perfil(cliente_id) or {}
    resumen_tb = obtener_resumen_tb(cliente_id) or {}
    ranking = calcular_ranking_areas(cliente_id)
    materialidad = calcular_materialidad(cliente_id) or {}

    cliente_info = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}

    balance = BalanceKPIs(
        activo=abs(_to_float(resumen_tb.get("ACTIVO", 0))),
        pasivo=abs(_to_float(resumen_tb.get("PASIVO", 0))),
        patrimonio=abs(_to_float(resumen_tb.get("PATRIMONIO", 0))),
        ingresos=abs(_to_float(resumen_tb.get("INGRESOS", 0))),
        gastos=abs(_to_float(resumen_tb.get("GASTOS", 0))),
    )

    top_areas: list[AreaRiesgo] = []
    areas_completas = 0
    areas_en_proceso = 0
    areas_no_iniciadas = 0

    if ranking is not None and not ranking.empty:
        for _, row in ranking.iterrows():
            prioridad = _to_str(row.get("prioridad", "baja"), "baja").lower()
            if prioridad == "baja":
                areas_completas += 1
            elif prioridad == "media":
                areas_en_proceso += 1
            else:
                areas_no_iniciadas += 1

        for _, row in ranking.head(5).iterrows():
            top_areas.append(
                AreaRiesgo(
                    codigo=_to_str(row.get("area", "")),
                    nombre=_to_str(row.get("nombre", "")),
                    score_riesgo=_to_float(row.get("score_riesgo", 0.0)),
                    prioridad=_to_str(row.get("prioridad", "baja"), "baja"),
                    saldo_total=_to_float(row.get("saldo_total", 0.0)),
                    con_saldo=bool(row.get("con_saldo", False)),
                )
            )

    total_areas = areas_completas + areas_en_proceso + areas_no_iniciadas
    pct_completado = int(round((areas_completas / total_areas) * 100, 0)) if total_areas > 0 else 0

    payload = DashboardResponse(
        cliente_id=cliente_id,
        nombre_cliente=_to_str(cliente_info.get("nombre_legal", cliente_id), cliente_id),
        periodo=_to_str(encargo.get("anio_activo", "")),
        sector=_to_str(cliente_info.get("sector", "")),
        riesgo_global=_to_str((perfil.get("riesgo_global", {}) or {}).get("nivel", "MEDIO"), "MEDIO"),
        balance=balance,
        progreso=ProgresoEncargo(
            pct_completado=pct_completado,
            areas_completas=areas_completas,
            areas_en_proceso=areas_en_proceso,
            areas_no_iniciadas=areas_no_iniciadas,
            total_areas=total_areas,
        ),
        top_areas=top_areas,
        materialidad_global=_to_float(materialidad.get("materialidad_sugerida", 0.0)),
    )

    return payload
