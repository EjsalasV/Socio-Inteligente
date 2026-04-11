from __future__ import annotations

import math
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.auth import authorize_cliente_access, get_current_user
from backend.schemas import (
    AreaRiesgo,
    BalanceKPIs,
    DashboardMaterialidadDetalle,
    DashboardResponse,
    DashboardWorkflowGate,
    ProgresoEncargo,
    UserContext,
)
from backend.services.view_cache_service import get_cached_view, set_cached_view

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _dashboard_cache_ttl_seconds() -> float:
    raw = os.getenv("DASHBOARD_CACHE_TTL_SECONDS", "20").strip()
    try:
        ttl = float(raw)
    except Exception:
        ttl = 20.0
    return max(0.0, min(ttl, 300.0))


def _safe_stat_signature(path: Path) -> str:
    try:
        stat = path.stat()
        return f"{int(stat.st_mtime_ns)}:{int(stat.st_size)}"
    except Exception:
        return "missing"


def _areas_signature(cliente_root: Path) -> str:
    areas_dir = cliente_root / "areas"
    if not areas_dir.exists():
        return "missing"
    newest = 0
    count = 0
    try:
        for path in areas_dir.glob("*.yaml"):
            try:
                mtime = int(path.stat().st_mtime_ns)
            except Exception:
                continue
            newest = max(newest, mtime)
            count += 1
    except Exception:
        return "missing"
    return f"{count}:{newest}"


def _dashboard_input_signature(cliente_id: str) -> str:
    root = Path(__file__).resolve().parents[2] / "data" / "clientes" / cliente_id
    parts = [
        _safe_stat_signature(root / "perfil.yaml"),
        _safe_stat_signature(root / "tb.xlsx"),
        _safe_stat_signature(root / "mayor.xlsx"),
        _safe_stat_signature(root / "workflow.yaml"),
        _safe_stat_signature(root / "hallazgos.md"),
        _areas_signature(root),
    ]
    return "|".join(parts)


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        v = float(value)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
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


def _materialidad_detail_from_motor(materialidad: dict[str, object]) -> DashboardMaterialidadDetalle:
    max_pct = _to_float(materialidad.get("porcentaje_maximo", 0.0))
    min_pct = _to_float(materialidad.get("porcentaje_minimo", 0.0))
    return DashboardMaterialidadDetalle(
        nia_base="NIA 320",
        base_usada=_to_str(materialidad.get("base_utilizada", "")),
        base_valor=_to_float(materialidad.get("valor_base", 0.0)),
        porcentaje_aplicado=max_pct,
        porcentaje_rango_min=min_pct,
        porcentaje_rango_max=max_pct,
        criterio_seleccion_pct=(
            "3% alto riesgo, 5% medio, 10% bajo (ajustado por regla de entidad/sector y umbral minimo)"
        ),
        origen_regla=_to_str(materialidad.get("origen_regla", "")),
        minimum_threshold_aplicado=_to_float(materialidad.get("minimum_threshold_aplicado", 0.0)),
        minimum_threshold_origen=_to_str(materialidad.get("minimum_threshold_origen", "")),
    )


def _selected_pct_by_risk(risk_level: str) -> float:
    raw = (risk_level or "").strip().lower()
    if raw in {"alto", "critico"}:
        return 3.0
    if raw in {"medio", "moderado"}:
        return 5.0
    return 10.0


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


def _normalize_workflow_phase(raw: str) -> str:
    value = (raw or "").strip().lower()
    if "inform" in value or "cier" in value:
        return "informe"
    if "ejec" in value or "visita" in value:
        return "ejecucion"
    return "planificacion"


def _normalize_tb_stage(raw: object) -> str:
    value = _to_str(raw, "").strip().lower()
    if value in {"final", "preliminar", "inicial", "sin_saldos"}:
        return value
    return "sin_saldos"


def _extract_riesgo_global_nivel(perfil: dict) -> str:
    raw = perfil.get("riesgo_global")
    if isinstance(raw, dict):
        return _to_str(raw.get("nivel", "MEDIO"), "MEDIO")
    if isinstance(raw, str):
        return _to_str(raw, "MEDIO")
    return "MEDIO"


def _extract_tb_stage(tb: object) -> str:
    try:
        if tb is not None and not tb.empty and "tb_stage" in tb.columns:
            return _normalize_tb_stage(tb["tb_stage"].iloc[0])
    except Exception:
        pass
    return "sin_saldos"


@router.get("/{cliente_id}", response_model=DashboardResponse)
def get_dashboard(
    cliente_id: str,
    areas_page: int = Query(1, ge=1),
    areas_page_size: int = Query(8, ge=1, le=100),
    user: UserContext = Depends(get_current_user),
) -> DashboardResponse:
    authorize_cliente_access(cliente_id, user)
    signature = _dashboard_input_signature(cliente_id)
    cache_key = f"dashboard:{cliente_id}:{areas_page}:{areas_page_size}:{signature}"
    ttl_seconds = _dashboard_cache_ttl_seconds()
    if ttl_seconds > 0:
        cached = get_cached_view(cache_key)
        if cached:
            try:
                return DashboardResponse.model_validate(cached)
            except Exception:
                pass

    stage = "init"
    try:
        stage = "imports"
        from analysis.lector_tb import leer_tb, obtener_resumen_tb
        from analysis.ranking_areas import calcular_ranking_areas
        from backend.routes.workpapers import _generate_tasks, _merge_saved_tasks, _quality_gates
        from backend.repositories.file_repository import read_perfil as read_perfil_repo
        from domain.services.leer_perfil import leer_perfil as read_perfil_legacy
        from domain.services.materialidad_service import calcular_materialidad

        stage = "load.perfil"
        try:
            perfil = read_perfil_repo(cliente_id) or {}
        except Exception:
            perfil = {}
        if not perfil:
            try:
                perfil = read_perfil_legacy(cliente_id) or {}
            except Exception:
                perfil = {}
        stage = "load.resumen_tb"
        try:
            resumen_tb = obtener_resumen_tb(cliente_id) or {}
        except Exception:
            resumen_tb = {}
        stage = "load.tb"
        try:
            tb = leer_tb(cliente_id)
        except Exception:
            tb = None
        stage = "load.ranking"
        try:
            ranking = calcular_ranking_areas(cliente_id)
        except Exception:
            ranking = None
        stage = "load.materialidad"
        try:
            materialidad = calcular_materialidad(cliente_id) or {}
        except Exception:
            materialidad = {}

        stage = "build.balance"
        cliente_info = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
        encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}

        balance = BalanceKPIs(
            activo=abs(_to_float(resumen_tb.get("ACTIVO", 0))),
            pasivo=abs(_to_float(resumen_tb.get("PASIVO", 0))),
            patrimonio=abs(_to_float(resumen_tb.get("PATRIMONIO", 0))),
            ingresos=abs(_to_float(resumen_tb.get("INGRESOS", 0))),
            gastos=abs(_to_float(resumen_tb.get("GASTOS", 0))),
        )

        stage = "build.areas"
        all_top_areas: list[AreaRiesgo] = []
        areas_completas = 0
        areas_en_proceso = 0
        areas_no_iniciadas = 0

        if ranking is not None and not ranking.empty:
            if "con_saldo" in ranking.columns:
                try:
                    saldo_series = ranking["saldo_total"].astype(float) if "saldo_total" in ranking.columns else 0.0
                    ranking_visible = ranking[(ranking["con_saldo"] == True) | (saldo_series > 0.0)]  # noqa: E712
                except Exception:
                    ranking_visible = ranking
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

            for _, row in ranking_visible.iterrows():
                all_top_areas.append(
                    AreaRiesgo(
                        codigo=_to_str(row.get("area", "")),
                        nombre=_to_str(row.get("nombre", "")),
                        score_riesgo=_to_float(row.get("score_riesgo", 0.0)),
                        prioridad=_to_str(row.get("prioridad", "baja"), "baja"),
                        saldo_total=_to_float(row.get("saldo_total", 0.0)),
                        con_saldo=bool(row.get("con_saldo", False)),
                    )
                )
        total_top_areas = len(all_top_areas)
        start = max(0, (areas_page - 1) * areas_page_size)
        end = start + areas_page_size
        top_areas = all_top_areas[start:end]
        top_areas_has_more = end < total_top_areas

        stage = "build.progress"
        total_areas = areas_completas + areas_en_proceso + areas_no_iniciadas
        pct_completado = int(round((areas_completas / total_areas) * 100, 0)) if total_areas > 0 else 0
        fase_actual = _to_str(encargo.get("fase_actual", ""), "")
        workflow_phase = _normalize_workflow_phase(fase_actual)
        pct_from_fase = _progreso_from_fase(fase_actual)
        if pct_from_fase is not None:
            pct_completado = pct_from_fase

        stage = "build.gates"
        workflow_gates: list[DashboardWorkflowGate] = []
        try:
            generated = _generate_tasks(cliente_id)
            merged = _merge_saved_tasks(cliente_id, generated)
            gates, _coverage = _quality_gates(cliente_id, merged)
            workflow_gates = [
                DashboardWorkflowGate(code=g.code, title=g.title, status=g.status, detail=g.detail)
                for g in gates
            ]
        except Exception:
            workflow_gates = []

        stage = "build.materialidad"
        mp_perfil, me_perfil, trivial_perfil = _materialidad_from_perfil(perfil)
        mp_calc = _to_float(materialidad.get("materialidad_sugerida", 0.0))
        me_calc = _to_float(materialidad.get("materialidad_desempeno", 0.0))
        trivial_calc = _to_float(materialidad.get("error_trivial", 0.0))

        mp = mp_perfil if mp_perfil > 0 else mp_calc
        me = me_perfil if me_perfil > 0 else me_calc
        trivial = trivial_perfil if trivial_perfil > 0 else trivial_calc
        materialidad_origen = "perfil" if mp_perfil > 0 else ("motor" if mp_calc > 0 else "sin_definir")
        materialidad_detalle = _materialidad_detail_from_motor(materialidad)
        base_valor = materialidad_detalle.base_valor
        riesgo_global_nivel = _extract_riesgo_global_nivel(perfil)
        pct_riesgo = _selected_pct_by_risk(riesgo_global_nivel)
        pct_aplicado = (mp / base_valor * 100.0) if base_valor > 0 and mp > 0 else pct_riesgo
        materialidad_detalle.porcentaje_aplicado = round(pct_aplicado, 2)
        if not materialidad_detalle.criterio_seleccion_pct:
            materialidad_detalle.criterio_seleccion_pct = (
                "3% alto riesgo, 5% medio, 10% bajo (NIA 320, juicio profesional)"
            )

        stage = "build.balance_status"
        accounting_delta = balance.activo - (balance.pasivo + balance.patrimonio)
        resultado_periodo = balance.ingresos - balance.gastos
        delta_abs = abs(accounting_delta)
        delta_vs_resultado = abs(accounting_delta - resultado_periodo)
        if delta_abs < 1.0:
            balance_status = "cuadrado"
        elif delta_vs_resultado < 1.0:
            balance_status = "resultado_periodo"
        else:
            balance_status = "descuadrado"

        stage = "build.payload"
        industria = perfil.get("industria_inteligente", {}) if isinstance(perfil.get("industria_inteligente"), dict) else {}
        sector = _to_str(cliente_info.get("sector", ""))
        if not sector:
            sector = _to_str(industria.get("sector_base", ""))

        payload = DashboardResponse(
            cliente_id=cliente_id,
            nombre_cliente=_to_str(cliente_info.get("nombre_legal", cliente_id), cliente_id),
            periodo=_to_str(encargo.get("anio_activo", "")),
            sector=sector,
            riesgo_global=riesgo_global_nivel,
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
            materialidad_origen=materialidad_origen,
            tb_stage=_extract_tb_stage(tb),
            fase_actual=fase_actual,
            workflow_phase=workflow_phase,
            workflow_gates=workflow_gates,
            balance_status=balance_status,
            resultado_periodo=resultado_periodo,
            balance_delta=delta_abs,
            materialidad_detalle=materialidad_detalle,
            top_areas_page=areas_page,
            top_areas_page_size=areas_page_size,
            top_areas_total=total_top_areas,
            top_areas_has_more=top_areas_has_more,
        )

        if ttl_seconds > 0:
            set_cached_view(cache_key, payload.model_dump(), int(max(1, round(ttl_seconds))))

        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Error interno en dashboard.",
                "stage": stage,
                "error": str(exc),
            },
        ) from exc
