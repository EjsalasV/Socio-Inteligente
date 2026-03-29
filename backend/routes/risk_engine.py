from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from fastapi import APIRouter, Depends

from backend.auth import authorize_cliente_access, get_current_user
from backend.constants.runtime_config import get_runtime_config
from backend.schemas import (
    ApiResponse,
    RiskCriticalArea,
    RiskEngineResponse,
    RiskMatrixCell,
    RiskStrategyResponse,
    RiskStrategyTest,
    UserContext,
)
from backend.services.judgement_service import build_risk_judgement_with_ai

router = APIRouter(prefix="/risk-engine", tags=["risk-engine"])
RUNTIME_CFG = get_runtime_config()


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data
    return {}


def _normalize_level(score: float) -> str:
    if score >= 80:
        return "ALTO"
    if score >= 55:
        return "MEDIO"
    return "BAJO"


def _compute_score(area_data: dict[str, Any]) -> tuple[float, int, int]:
    hallazgos = area_data.get("hallazgos_abiertos")
    procedimientos = area_data.get("procedimientos")

    hallazgos_count = len(hallazgos) if isinstance(hallazgos, list) else 0
    pendientes_count = 0
    if isinstance(procedimientos, list):
        for proc in procedimientos:
            if not isinstance(proc, dict):
                continue
            estado = str(proc.get("estado", "")).strip().lower()
            if estado in {"pendiente", "planificado", "en_proceso"}:
                pendientes_count += 1

    score = 35.0 + (hallazgos_count * 22.0) + min(pendientes_count * 6.0, 30.0)
    score = max(8.0, min(99.0, score))
    return score, hallazgos_count, pendientes_count


def _score_to_axes(score: float) -> tuple[int, int]:
    impacto = max(1, min(5, int(round(score / 20.0))))
    frecuencia = max(1, min(5, int(round((score * 0.8) / 20.0)) + 1))
    return frecuencia, impacto


def _build_matrix_cells(areas: list[RiskCriticalArea]) -> list[list[RiskMatrixCell]]:
    grid: list[list[RiskMatrixCell]] = []
    by_pos: dict[tuple[int, int], RiskCriticalArea] = {}

    for item in areas:
        key = (item.frecuencia, item.impacto)
        current = by_pos.get(key)
        if current is None or item.score > current.score:
            by_pos[key] = item

    for row in range(5, 0, -1):
        matrix_row: list[RiskMatrixCell] = []
        for col in range(1, 6):
            found = by_pos.get((row, col))
            score = found.score if found else float((row * col) * 3)
            nivel = _normalize_level(score)
            matrix_row.append(
                RiskMatrixCell(
                    row=6 - row,
                    col=col - 1,
                    frecuencia=row,
                    impacto=col,
                    score=round(score, 2),
                    nivel=nivel,
                    area_id=found.area_id if found else None,
                    area_nombre=found.area_nombre if found else None,
                )
            )
        grid.append(matrix_row)
    return grid


def _slug(value: str) -> str:
    s = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "item"


def _priority_from_level(level: str) -> str:
    normalized = str(level or "").upper()
    if normalized == "ALTO":
        return "alta"
    if normalized == "MEDIO":
        return "media"
    return "baja"


def _build_control_test(area: RiskCriticalArea, nia_ref: str, title: str, description: str) -> RiskStrategyTest:
    return RiskStrategyTest(
        test_id=f"ctl-{area.area_id}-{_slug(title)}",
        test_type="control",
        area_id=area.area_id,
        area_nombre=area.area_nombre,
        nia_ref=nia_ref,
        title=title,
        description=description,
        where_to_execute="workpapers",
        priority=_priority_from_level(area.nivel),
    )


def _build_substantive_test(area: RiskCriticalArea, nia_ref: str, title: str, description: str) -> RiskStrategyTest:
    return RiskStrategyTest(
        test_id=f"sub-{area.area_id}-{_slug(title)}",
        test_type="sustantiva",
        area_id=area.area_id,
        area_nombre=area.area_nombre,
        nia_ref=nia_ref,
        title=title,
        description=description,
        where_to_execute="workpapers",
        priority=_priority_from_level(area.nivel),
    )


def _tests_for_area(area: RiskCriticalArea) -> tuple[list[RiskStrategyTest], list[RiskStrategyTest]]:
    name = area.area_nombre.lower()
    controls: list[RiskStrategyTest] = []
    substantives: list[RiskStrategyTest] = []

    if "efectivo" in name or "banco" in name or area.area_id == "140":
        controls.append(
            _build_control_test(
                area,
                "NIA 315",
                "Control sobre conciliaciones bancarias",
                "Validar diseno e implementacion del control de conciliacion mensual y aprobacion por nivel adecuado.",
            )
        )
        substantives.append(
            _build_substantive_test(
                area,
                "NIA 505",
                "Confirmaciones bancarias externas",
                "Obtener confirmaciones directas de bancos y recalcular partidas conciliatorias de cierre.",
            )
        )
    elif "cobrar" in name or "ingreso" in name or area.area_id == "130":
        controls.append(
            _build_control_test(
                area,
                "NIA 315",
                "Control de aprobacion de credito y facturacion",
                "Revisar evidencia de aprobaciones, segregacion y bloqueo de modificaciones no autorizadas.",
            )
        )
        substantives.append(
            _build_substantive_test(
                area,
                "NIA 505",
                "Circularizacion de cuentas por cobrar",
                "Confirmar saldos relevantes y documentar diferencias con soporte posterior de cobro.",
            )
        )
    elif "invent" in name:
        controls.append(
            _build_control_test(
                area,
                "NIA 330",
                "Control de movimientos y conteos ciclicos",
                "Evaluar autorizaciones de entradas/salidas y trazabilidad de ajustes de inventario.",
            )
        )
        substantives.append(
            _build_substantive_test(
                area,
                "NIA 501",
                "Conteo fisico y pruebas de corte",
                "Asistir a toma fisica selectiva y cruzar movimientos de cierre con documentos fuente.",
            )
        )
    elif "patrimonio" in name or area.area_id == "200":
        controls.append(
            _build_control_test(
                area,
                "NIA 315",
                "Control sobre actas y aprobaciones societarias",
                "Validar que cambios patrimoniales tengan aprobacion formal y registro oportuno.",
            )
        )
        substantives.append(
            _build_substantive_test(
                area,
                "NIA 500",
                "Recalculo de movimientos patrimoniales",
                "Recalcular variaciones y conciliar contra actas, asientos y revelaciones del periodo.",
            )
        )
    else:
        controls.append(
            _build_control_test(
                area,
                "NIA 330",
                "Walkthrough de control clave",
                "Documentar flujo de proceso y evidencia de ejecucion del control principal del area.",
            )
        )
        substantives.append(
            _build_substantive_test(
                area,
                "NIA 520",
                "Procedimiento analitico focalizado",
                "Comparar variaciones no esperadas y sustentar diferencias con evidencia suficiente.",
            )
        )

    return controls, substantives


def _build_strategy_deterministic(areas: list[RiskCriticalArea]) -> RiskStrategyResponse:
    if not areas:
        return RiskStrategyResponse(
            approach="Mixto",
            control_pct=50,
            substantive_pct=50,
            rationale=(
                "Sin datos suficientes para calibrar el enfoque. Se recomienda iniciar en modo mixto y "
                "ajustar al cargar TB y mayor."
            ),
            control_tests=[],
            substantive_tests=[],
        )

    top = areas[:5]
    weighted = sum(a.score * (1.15 if a.nivel == "ALTO" else 1.0) for a in top) / max(1, len(top))
    highs = sum(1 for a in top if a.nivel == "ALTO")

    if weighted >= 75 or highs >= 2:
        control_pct, substantive_pct = 35, 65
        rationale = (
            "El perfil de riesgo requiere priorizar procedimientos sustantivos (NIA 330), "
            "manteniendo pruebas de control focalizadas en procesos criticos."
        )
    elif weighted >= 55:
        control_pct, substantive_pct = 45, 55
        rationale = (
            "El riesgo es moderado: se sostiene enfoque mixto con sesgo sustantivo, "
            "combinando efectividad de controles y validaciones directas."
        )
    else:
        control_pct, substantive_pct = 60, 40
        rationale = (
            "El riesgo observado permite soportar mayor peso en pruebas de control, "
            "complementadas con sustantivos selectivos sobre saldos materiales."
        )

    control_tests: list[RiskStrategyTest] = []
    substantive_tests: list[RiskStrategyTest] = []
    for area in top:
        ctl, sub = _tests_for_area(area)
        control_tests.extend(ctl)
        substantive_tests.extend(sub)

    return RiskStrategyResponse(
        approach="Mixto",
        control_pct=control_pct,
        substantive_pct=substantive_pct,
        rationale=rationale,
        control_tests=control_tests[:6],
        substantive_tests=substantive_tests[:6],
    )


def _norm_header(value: Any) -> str:
    txt = str(value or "").strip().lower()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
    txt = re.sub(r"[^a-z0-9]+", "_", txt).strip("_")
    return txt


def _normalize_code(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.endswith(".0"):
        raw = raw[:-2]
    return raw


def _resolve_col(columns: list[str], candidates: list[str]) -> str | None:
    for cand in candidates:
        if cand in columns:
            return cand
    return None


def _to_numeric(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.replace(",", "", regex=False).str.replace("$", "", regex=False).str.strip()
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def _load_mayor(cliente_id: str) -> pd.DataFrame:
    path = Path(__file__).resolve().parents[2] / "data" / "clientes" / cliente_id / "mayor.xlsx"
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    df.columns = [_norm_header(c) for c in df.columns]
    return df


def _build_code_to_area(cliente_id: str) -> dict[str, str]:
    try:
        from analysis.lector_tb import leer_tb

        tb = leer_tb(cliente_id)
        if tb is None or tb.empty:
            return {}
        work = tb.copy()
        work.columns = [_norm_header(c) for c in work.columns]
        code_col = _resolve_col(work.columns.tolist(), ["codigo", "numero_de_cuenta", "cuenta", "cod_cuenta"])
        ls_col = _resolve_col(work.columns.tolist(), ["ls", "l_s", "l_s_", "linea_significancia", "l"])
        if code_col is None or ls_col is None:
            return {}
        out: dict[str, str] = {}
        for _, row in work.iterrows():
            code = _normalize_code(row.get(code_col))
            area = _normalize_code(row.get(ls_col))
            if not code or not area:
                continue
            out[code] = area
        return out
    except Exception:
        return {}


def _map_area_for_account(account_code: str, code_to_area: dict[str, str]) -> str:
    code = _normalize_code(account_code)
    if not code:
        return ""
    if code in code_to_area:
        return code_to_area[code]
    prefixes = sorted(code_to_area.keys(), key=len, reverse=True)
    for key in prefixes:
        if code.startswith(key) or key.startswith(code):
            return code_to_area[key]
    return ""


def _mayor_signals_by_area(cliente_id: str, tb_totals_by_area: dict[str, float]) -> dict[str, dict[str, Any]]:
    df = _load_mayor(cliente_id)
    if df.empty:
        return {}

    code_to_area = _build_code_to_area(cliente_id)
    if not code_to_area:
        return {}

    cols = df.columns.tolist()
    account_col = _resolve_col(cols, ["codigo", "cuenta", "numero_de_cuenta", "cuenta_codigo", "cod_cuenta"])
    if account_col is None:
        return {}

    debit_col = _resolve_col(cols, ["debe", "debito", "debit"])
    credit_col = _resolve_col(cols, ["haber", "credito", "credit"])
    amount_col = _resolve_col(cols, ["monto", "importe", "amount", "valor"])
    date_col = _resolve_col(cols, ["fecha", "date", "fecha_asiento", "f_contable"])
    user_col = _resolve_col(cols, ["usuario", "user", "created_by"])
    desc_col = _resolve_col(cols, ["descripcion", "detalle", "glosa", "concepto"])

    work = df.copy()
    work["account_code"] = work[account_col].apply(_normalize_code)
    work["area_id"] = work["account_code"].apply(lambda x: _map_area_for_account(x, code_to_area))
    work = work[work["area_id"] != ""]
    if work.empty:
        return {}

    if amount_col:
        work["amount_net"] = _to_numeric(work[amount_col])
        work["amount_abs"] = work["amount_net"].abs()
    elif debit_col and credit_col:
        debit = _to_numeric(work[debit_col])
        credit = _to_numeric(work[credit_col])
        work["amount_net"] = debit - credit
        work["amount_abs"] = (debit.abs() + credit.abs()) / 2.0
    elif debit_col:
        debit = _to_numeric(work[debit_col])
        work["amount_net"] = debit
        work["amount_abs"] = debit.abs()
    else:
        work["amount_net"] = 0.0
        work["amount_abs"] = 0.0

    if date_col:
        work["txn_date"] = pd.to_datetime(work[date_col], errors="coerce")
    else:
        work["txn_date"] = pd.NaT

    if user_col:
        work["txn_user"] = work[user_col].astype(str).str.strip().replace({"": "N/A"})
    else:
        work["txn_user"] = "N/A"

    if desc_col:
        work["txn_desc"] = work[desc_col].astype(str).str.lower()
    else:
        work["txn_desc"] = ""

    out: dict[str, dict[str, Any]] = {}
    risk_cfg = RUNTIME_CFG.get("risk_engine", {}) if isinstance(RUNTIME_CFG, dict) else {}
    weights = risk_cfg.get("weights", {}) if isinstance(risk_cfg, dict) else {}
    caps = risk_cfg.get("caps", {}) if isinstance(risk_cfg, dict) else {}
    w_closing = _to_float(weights.get("closing_entries"), 3.0)
    w_user = _to_float(weights.get("user_spike_factor"), 40.0)
    w_reversals = _to_float(weights.get("reversals"), 2.0)
    w_dormant = _to_float(weights.get("dormant_accounts"), 2.0)
    w_gap_divisor = max(0.1, _to_float(weights.get("tb_mayor_gap_divisor"), 8.0))

    cap_closing = _to_float(caps.get("closing_entries"), 12.0)
    cap_user = _to_float(caps.get("user_spike"), 10.0)
    cap_reversals = _to_float(caps.get("reversals"), 8.0)
    cap_dormant = _to_float(caps.get("dormant_accounts"), 8.0)
    cap_gap = _to_float(caps.get("tb_mayor_gap"), 15.0)
    cap_total = _to_float(caps.get("mayor_boost_total"), 25.0)
    for area_id, grp in work.groupby("area_id"):
        total_abs = float(grp["amount_abs"].sum())
        if total_abs <= 0:
            continue

        p90 = float(grp["amount_abs"].quantile(0.90)) if len(grp) > 2 else float(grp["amount_abs"].max())
        closing_count = 0
        if grp["txn_date"].notna().any():
            max_date = grp["txn_date"].max()
            closing_mask = grp["txn_date"] >= (max_date - pd.Timedelta(days=3))
            closing_count = int((closing_mask & (grp["amount_abs"] >= p90)).sum())

        user_share = 0.0
        if grp["txn_user"].nunique() > 0:
            user_totals = grp.groupby("txn_user")["amount_abs"].sum()
            user_share = float((user_totals.max() / total_abs) if total_abs > 0 else 0.0)

        reversal_count = int(grp["txn_desc"].str.contains(r"revers|anul|ajuste|reclas", regex=True, na=False).sum())

        dormant_count = 0
        if grp["txn_date"].notna().any():
            by_account_month = (
                grp.dropna(subset=["txn_date"])
                .assign(yyyymm=lambda x: x["txn_date"].dt.to_period("M").astype(str))
                .groupby("account_code")
                .agg(months=("yyyymm", "nunique"), amount=("amount_abs", "sum"))
            )
            if not by_account_month.empty:
                cutoff = float(by_account_month["amount"].quantile(0.75))
                dormant_count = int(((by_account_month["months"] <= 2) & (by_account_month["amount"] >= cutoff)).sum())

        mayor_net = float(grp["amount_net"].sum())
        tb_total = abs(_to_float(tb_totals_by_area.get(area_id, 0.0)))
        correlation_gap_pct = 0.0
        if tb_total > 0:
            correlation_gap_pct = abs(abs(mayor_net) - tb_total) / tb_total * 100.0

        components = {
            "closing_entries": min(cap_closing, closing_count * w_closing),
            "user_spike": min(cap_user, max(0.0, (user_share - 0.50) * w_user)),
            "reversals": min(cap_reversals, reversal_count * w_reversals),
            "dormant_accounts": min(cap_dormant, dormant_count * w_dormant),
            "tb_mayor_gap": min(cap_gap, correlation_gap_pct / w_gap_divisor),
        }
        boost = min(cap_total, sum(components.values()))

        drivers: list[str] = []
        if components["closing_entries"] > 0:
            drivers.append(f"Asientos de cierre inusuales ({closing_count})")
        if components["user_spike"] > 0:
            drivers.append(f"Concentracion por usuario ({user_share * 100:.1f}%)")
        if components["reversals"] > 0:
            drivers.append(f"Reversiones/ajustes atipicos ({reversal_count})")
        if components["dormant_accounts"] > 0:
            drivers.append(f"Cuentas con movimiento concentrado ({dormant_count})")
        if components["tb_mayor_gap"] > 0:
            drivers.append(f"Brecha TB vs Mayor ({correlation_gap_pct:.1f}%)")

        out[area_id] = {
            "boost": round(boost, 2),
            "drivers": drivers[:3],
            "components": {k: round(v, 2) for k, v in components.items()},
        }
    return out


def _from_ranking(cliente_id: str) -> list[RiskCriticalArea]:
    try:
        from analysis.ranking_areas import calcular_ranking_areas

        ranking = calcular_ranking_areas(cliente_id)
        if ranking is None or ranking.empty:
            return []

        if "con_saldo" in ranking.columns:
            ranking = ranking[ranking["con_saldo"] == True]  # noqa: E712
        if ranking.empty:
            return []

        tb_totals_by_area = {
            str(row.get("area") or ""): _to_float(row.get("saldo_total", 0.0))
            for _, row in ranking.iterrows()
        }
        mayor_signals = _mayor_signals_by_area(cliente_id, tb_totals_by_area)

        out: list[RiskCriticalArea] = []
        for _, row in ranking.sort_values("score_riesgo", ascending=False).head(12).iterrows():
            area_id = str(row.get("area") or "")
            base_score = _to_float(row.get("score_riesgo", 0.0))
            signal = mayor_signals.get(area_id, {})
            mayor_boost = _to_float(signal.get("boost", 0.0))
            final_score = min(99.0, base_score + mayor_boost)
            frecuencia, impacto = _score_to_axes(final_score)

            components = {"base_model": round(base_score, 2), "mayor_boost": round(mayor_boost, 2)}
            components.update(signal.get("components", {}))

            out.append(
                RiskCriticalArea(
                    area_id=area_id,
                    area_nombre=str(row.get("nombre") or f"Area {area_id}"),
                    score=round(final_score, 2),
                    nivel=_normalize_level(final_score),
                    frecuencia=frecuencia,
                    impacto=impacto,
                    hallazgos_abiertos=_to_int(row.get("expert_flags_count", 0), 0),
                    drivers=signal.get("drivers", []),
                    score_components=components,
                )
            )
        return out
    except Exception:
        return []


def _from_area_files(cliente_id: str) -> list[RiskCriticalArea]:
    cliente_root = Path(__file__).resolve().parents[2] / "data" / "clientes" / cliente_id
    areas_dir = cliente_root / "areas"
    critical_areas: list[RiskCriticalArea] = []

    if areas_dir.exists():
        for area_file in sorted(areas_dir.glob("*.yaml")):
            area_data = _safe_read_yaml(area_file)
            if not area_data:
                continue

            score, hallazgos_count, _pendientes_count = _compute_score(area_data)
            area_id = str(area_data.get("codigo") or area_file.stem)
            area_name = str(area_data.get("nombre") or f"Area {area_id}")
            frecuencia, impacto = _score_to_axes(score)
            critical_areas.append(
                RiskCriticalArea(
                    area_id=area_id,
                    area_nombre=area_name,
                    score=round(score, 2),
                    nivel=_normalize_level(score),
                    frecuencia=frecuencia,
                    impacto=impacto,
                    hallazgos_abiertos=_to_int(hallazgos_count, 0),
                    drivers=[],
                    score_components={"base_model": round(score, 2)},
                )
            )

    return critical_areas


@router.get("/{cliente_id}", response_model=ApiResponse)
def get_risk_engine(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)

    critical_areas = _from_ranking(cliente_id)
    if not critical_areas:
        critical_areas = _from_area_files(cliente_id)

    if not critical_areas:
        critical_areas = [
            RiskCriticalArea(
                area_id="14",
                area_nombre="Inversiones no corrientes",
                score=72.0,
                nivel="MEDIO",
                frecuencia=4,
                impacto=4,
                hallazgos_abiertos=0,
                drivers=["Sin datos historicos suficientes; riesgo base por relevancia financiera."],
                score_components={"base_model": 72.0},
            ),
            RiskCriticalArea(
                area_id="200",
                area_nombre="Patrimonio",
                score=65.0,
                nivel="MEDIO",
                frecuencia=4,
                impacto=3,
                hallazgos_abiertos=0,
                drivers=[],
                score_components={"base_model": 65.0},
            ),
            RiskCriticalArea(
                area_id="1000",
                area_nombre="Gastos administrativos",
                score=52.0,
                nivel="BAJO",
                frecuencia=3,
                impacto=3,
                hallazgos_abiertos=0,
                drivers=[],
                score_components={"base_model": 52.0},
            ),
        ]

    critical_areas.sort(key=lambda x: x.score, reverse=True)
    quadrants = _build_matrix_cells(critical_areas)
    deterministic_strategy = _build_strategy_deterministic(critical_areas)
    strategy = build_risk_judgement_with_ai(
        cliente_id,
        areas=critical_areas,
        deterministic=deterministic_strategy,
    )

    payload = RiskEngineResponse(
        cliente_id=cliente_id,
        quadrants=quadrants,
        areas_criticas=critical_areas[:8],
        strategy=strategy,
    )
    return ApiResponse(data=payload.model_dump())
