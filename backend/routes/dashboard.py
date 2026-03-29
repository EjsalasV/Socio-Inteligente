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


def _materialidad_from_perfil(perfil: dict) -> tuple[float, float, float]:
    materialidad = perfil.get("materialidad", {}) if isinstance(perfil.get("materialidad"), dict) else {}
    preliminar = materialidad.get("preliminar", {}) if isinstance(materialidad.get("preliminar"), dict) else {}
    final = materialidad.get("final", {}) if isinstance(materialidad.get("final"), dict) else {}

    mp = _to_float(final.get("materialidad_planeacion", 0.0))
    me = _to_float(final.get("materialidad_ejecucion", 0.0))
    trivial = _to_float(final.get("umbral_trivialidad", 0.0))

    if mp <= 0:
        mp = _to_float(preliminar.get("materialidad_global", 0.0))
    if me <= 0:
        me = _to_float(preliminar.get("materialidad_desempeno", 0.0))
    if trivial <= 0:
        trivial = _to_float(preliminar.get("error_trivial", 0.0))

    return mp, me, trivial


def _progreso_from_fase(fase_actual: str) -> int | None:
    fase = fase_actual.strip().lower()
    if not fase:
        return None
    if "plan" in fase:
        return 20
    if "ejec" in fase or "visita" in fase:
        return 60
    if "inform" in fase or "cierre" in fase:
        return 90
    return None


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
        if "con_saldo" in ranking.columns:
            saldo_series = ranking["saldo_total"].astype(float) if "saldo_total" in ranking.columns else 0.0
            ranking_visible = ranking[(ranking["con_saldo"] == True) | (saldo_series > 0.0)]  # noqa: E712
        else:
            ranking_visible = ranking
        if ranking_visible.empty:
            ranking_visible = ranking.iloc[0:0]

        for _, row in ranking_visible.iterrows():
            prioridad = _to_str(row.get("prioridad", "baja"), "baja").lower()
            if prioridad == "baja":
                areas_completas += 1
            elif prioridad == "media":
                areas_en_proceso += 1
            else:
                areas_no_iniciadas += 1

        for _, row in ranking_visible.head(8).iterrows():
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
    fase_actual = _to_str(encargo.get("fase_actual", ""), "planificacion")
    pct_from_fase = _progreso_from_fase(fase_actual)
    if pct_from_fase is not None:
        pct_completado = pct_from_fase

    mp_perfil, me_perfil, trivial_perfil = _materialidad_from_perfil(perfil)
    mp_calc = _to_float(materialidad.get("materialidad_sugerida", 0.0))
    me_calc = _to_float(materialidad.get("materialidad_desempeno", 0.0))
    trivial_calc = _to_float(materialidad.get("error_trivial", 0.0))

    mp = mp_perfil if mp_perfil > 0 else mp_calc
    me = me_perfil if me_perfil > 0 else me_calc
    trivial = trivial_perfil if trivial_perfil > 0 else trivial_calc

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
        materialidad_global=mp,
        materialidad_ejecucion=me,
        umbral_trivial=trivial,
        fase_actual=fase_actual,
    )

    return payload
