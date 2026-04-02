from __future__ import annotations

import os
from typing import Any, Optional, Dict, List, Tuple

import pandas as pd

from analysis.expert_flags import detectar_expert_flags
from analysis.lector_tb import leer_tb, obtener_resumen_tb
from analysis.variaciones import calcular_variaciones
from core.configuracion import obtener_audit_areas_config
from core.logger import obtener_logger
from core.utils.normalizaciones import normalizar_ls
from infra.repositories.catalogo_repository import cargar_areas_catalogo

try:
    from domain.services.leer_perfil import leer_perfil
except Exception:
    leer_perfil = None

try:
    from domain.services.materialidad_service import calcular_materialidad
except Exception:
    calcular_materialidad = None


AREAS_AUDITORIA_DEFAULT = {
    "130": {"nombre": "Cuentas por Cobrar", "peso": 1.0},
    "140": {"nombre": "Efectivo", "peso": 1.2},
    "145": {"nombre": "Impuestos - Activos", "peso": 0.8},
    "170": {"nombre": "Propiedad e Inversion", "peso": 0.9},
    "200": {"nombre": "Patrimonio", "peso": 1.1},
}
LOGGER = obtener_logger()


def _inferir_peso(area: dict[str, Any]) -> float:
    categoria = str(area.get("categoria_general", "")).lower()
    clase = str(area.get("clase", "")).lower()
    codigo = str(area.get("codigo", "")).strip()
    if "patrimonio" in categoria:
        return 1.1
    if "pasivo" in categoria:
        return 1.0
    if "ingresos" in categoria:
        return 1.1
    if "costos" in categoria or "gastos" in categoria:
        return 0.95
    if "inversion" in clase:
        return 1.0
    if codigo in {"140", "130.1", "130.2"}:
        return 1.0
    return 0.9


def _dynamic_area_name_from_ls(codigo: str) -> str:
    code = str(codigo or "").strip()
    if not code:
        return "Area"
    first = code[0]
    if first == "1":
        return f"Activo ({code})"
    if first == "2":
        return f"Pasivo ({code})"
    if first == "3":
        return f"Patrimonio ({code})"
    if first == "4":
        return f"Ingresos ({code})"
    if first == "5":
        return f"Gastos ({code})"
    return f"Area {code}"


def _cargar_areas_auditoria(tb: pd.DataFrame | None = None) -> dict[str, dict[str, Any]]:
    salida: dict[str, dict[str, Any]] = {}

    # Prioridad 1: áreas configuradas explícitamente en config.yaml.
    for area in obtener_audit_areas_config():
        salida[area["code"]] = {
            "nombre": area["name"],
            "peso": area["weight"],
        }

    # Prioridad 2: catálogo base (rellena faltantes).
    areas_catalogo = cargar_areas_catalogo()
    if areas_catalogo:
        for area in areas_catalogo:
            codigo = str(area.get("codigo", "")).strip()
            if not codigo:
                continue
            if codigo in salida:
                continue
            salida[codigo] = {
                "nombre": str(area.get("titulo", f"Area {codigo}")).strip() or f"Area {codigo}",
                "peso": _inferir_peso(area),
            }

    if isinstance(tb, pd.DataFrame) and not tb.empty and "ls" in tb.columns:
        ls_values = (
            tb["ls"]
            .astype(str)
            .str.strip()
            .replace({"": None, "nan": None, "None": None})
            .dropna()
            .unique()
            .tolist()
        )
        for raw_ls in ls_values:
            codigo = str(raw_ls).strip()
            if not codigo:
                continue
            if codigo not in salida:
                salida[codigo] = {
                    "nombre": _dynamic_area_name_from_ls(codigo),
                    "peso": 0.9,
                }

    if not salida:
        return AREAS_AUDITORIA_DEFAULT
    return salida


def _safe_call(func: Any, *args: Any, default: Any = None, **kwargs: Any) -> Any:
    if func is None:
        return default
    try:
        return func(*args, **kwargs)
    except (ValueError, TypeError, KeyError, OSError):
        return default


def _to_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def _safe_percentage(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return (numerator / denominator) * 100


def _resolve_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _preparar_tb(tb: pd.DataFrame) -> pd.DataFrame:
    tb2 = tb.copy()
    codigo_col = _resolve_col(tb2, ["codigo", "numero_de_cuenta", "cuenta", "cod_cuenta"])
    ls_col = _resolve_col(tb2, ["ls", "l/s", "l_s", "L/S"])
    saldo_col = _resolve_col(tb2, ["saldo_actual", "saldo", "saldo_2025", "saldo_preliminar"])

    if saldo_col is None:
        return pd.DataFrame()

    if codigo_col is not None:
        tb2["codigo"] = tb2[codigo_col].astype(str).apply(normalizar_ls)
    else:
        tb2["codigo"] = ""
    if ls_col is not None:
        tb2["ls"] = tb2[ls_col].astype(str).str.strip()
    else:
        tb2["ls"] = ""
    tb2["saldo_actual"] = pd.to_numeric(tb2[saldo_col], errors="coerce").fillna(0.0)
    tb2["saldo_abs"] = tb2["saldo_actual"].abs()
    return tb2


def _preparar_variaciones(variaciones: pd.DataFrame | None) -> pd.DataFrame:
    if variaciones is None or variaciones.empty:
        return pd.DataFrame()

    var = variaciones.copy()
    codigo_col = _resolve_col(var, ["codigo", "numero_de_cuenta", "cuenta", "cod_cuenta"])
    ls_col = _resolve_col(var, ["ls", "l/s", "l_s", "L/S"])
    impacto_col = _resolve_col(var, ["impacto", "variacion_absoluta", "abs_variacion_absoluta", "saldo_abs"])

    if codigo_col is not None:
        var["codigo"] = var[codigo_col].astype(str).apply(normalizar_ls)
    else:
        var["codigo"] = ""
    if ls_col is not None:
        var["ls"] = var[ls_col].astype(str).str.strip()
    else:
        var["ls"] = ""
    if impacto_col:
        var["impacto"] = pd.to_numeric(var[impacto_col], errors="coerce").fillna(0.0)
    else:
        var["impacto"] = 0.0

    return var


def seleccionar_filas_area_por_ls(df: pd.DataFrame, codigo_area: str) -> tuple[pd.DataFrame, str]:
    """
    Selecciona filas del area priorizando LS exacto.

    Reglas:
    - Si existe columna ls y hay valores ls no vacios, usa igualdad exacta de ls.
    - Solo si no hay match exacto, permite fallback por codigo para filas sin ls.
    - Si no existe ls (o ls esta completamente vacio), usa fallback por codigo.
    """
    if df is None or df.empty:
        return pd.DataFrame(), "empty_df"

    codigo = str(codigo_area).strip()
    work = df.copy()

    if "ls" in work.columns:
        ls_norm = work["ls"].astype(str).apply(normalizar_ls)
        nonempty_ls = ls_norm != ""

        # Hay LS usable en dataset: usar match exacto obligatorio.
        if nonempty_ls.any():
            exact = work[ls_norm == codigo]
            if not exact.empty:
                return exact, "ls_exact"

            # Solo considerar filas sin LS para fallback.
            if "codigo" in work.columns:
                fallback_base = work[~nonempty_ls].copy()
                if not fallback_base.empty:
                    by_code = fallback_base[fallback_base["codigo"].astype(str).str.startswith(codigo)]
                    return by_code, "codigo_fallback_only_missing_ls"
            return pd.DataFrame(columns=work.columns), "ls_exact_no_match"

    # Dataset sin ls util: fallback legacy por codigo.
    if "codigo" in work.columns:
        by_code = work[work["codigo"].astype(str).str.startswith(codigo)]
        return by_code, "codigo_fallback_no_ls"

    return pd.DataFrame(columns=work.columns), "no_ls_no_codigo"


def _debug_area_selection(
    codigo: str,
    nombre: str,
    tb_area: pd.DataFrame,
    tb_method: str,
    var_area: pd.DataFrame,
    var_method: str,
) -> None:
    if str(os.getenv("SOCIOAI_DEBUG_RANKING", "")).strip() not in {"1", "true", "TRUE", "yes", "YES"}:
        return

    targets_raw = str(os.getenv("SOCIOAI_DEBUG_AREAS", "1,14,200")).strip()
    targets = {x.strip() for x in targets_raw.split(",") if x.strip()}
    if targets and str(codigo).strip() not in targets:
        return

    tb_ls = []
    tb_names = []
    if not tb_area.empty:
        if "ls" in tb_area.columns:
            tb_ls = [str(x) for x in tb_area["ls"].dropna().astype(str).head(5).tolist()]
        if "nombre" in tb_area.columns:
            tb_names = [str(x) for x in tb_area["nombre"].dropna().astype(str).head(3).tolist()]

    var_ls = []
    if not var_area.empty and "ls" in var_area.columns:
        var_ls = [str(x) for x in var_area["ls"].dropna().astype(str).head(5).tolist()]

    LOGGER.info(
        f"[RANK-DEBUG] area={codigo} nombre={nombre} "
        f"tb_method={tb_method} tb_rows={len(tb_area)} tb_ls_sample={tb_ls} tb_names_sample={tb_names} "
        f"var_method={var_method} var_rows={len(var_area)} var_ls_sample={var_ls}"
    )


def _calcular_materialidad_cliente(cliente: str) -> dict[str, Any]:
    mat = _safe_call(calcular_materialidad, cliente, default=None)
    if not isinstance(mat, dict):
        return {}

    return {
        "materialidad_sugerida": _to_float(mat.get("materialidad_sugerida", 0)),
        "materialidad_ejecucion": _to_float(mat.get("materialidad_desempeno", 0)),
        "trivialidad": _to_float(mat.get("error_trivial", 0)),
        "base_utilizada": mat.get("base_utilizada", ""),
    }


def _construir_justificacion(result: dict[str, Any]) -> str:
    pct_total = _to_float(result.get("pct_total", 0))
    mat_rel = _to_float(result.get("materialidad_relativa", 0))
    flags = int(result.get("expert_flags_count", 0) or 0)
    score = _to_float(result.get("score_riesgo", 0))

    parts: list[str] = []
    if pct_total >= 10:
        parts.append("alta concentracion de saldo")
    if mat_rel >= 50:
        parts.append("impacto material sobre materialidad")
    if flags > 0:
        parts.append(f"{flags} senales expertas")
    if score >= 60:
        parts.append("score de riesgo elevado")

    if not parts:
        return "riesgo moderado por composicion y variaciones del area"

    return "; ".join(parts)


def _prioridad_accionable(score: float, mat_rel: float, flags_count: int) -> str:
    if score >= 70 or mat_rel >= 80 or flags_count >= 2:
        return "alta"
    if score >= 45 or mat_rel >= 40 or flags_count >= 1:
        return "media"
    return "baja"


def _is_holding_profile(perfil: dict[str, Any]) -> bool:
    if not isinstance(perfil, dict):
        return False
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    contexto = perfil.get("contexto_negocio", {}) if isinstance(perfil.get("contexto_negocio"), dict) else {}
    industria = perfil.get("industria_inteligente", {}) if isinstance(perfil.get("industria_inteligente"), dict) else {}
    blob = " ".join(
        [
            str(cliente.get("sector", "")),
            str(cliente.get("subsector", "")),
            str(contexto.get("actividad_principal", "")),
            str(industria.get("sector_base", "")),
            str(industria.get("subtipo_negocio", "")),
        ]
    ).lower()
    return "holding" in blob or "cartera" in blob


def _holding_context_boost(codigo: str, perfil: dict[str, Any]) -> float:
    if not _is_holding_profile(perfil):
        return 0.0
    boosts = {
        "14": 4.0,
        "200": 3.5,
        "425.2": 2.0,
        "136": 1.5,
        "15": 1.5,
    }
    return boosts.get(str(codigo).strip(), 0.0)


def _estado_presencia(presente: bool, con_saldo: bool) -> str:
    if not presente:
        return "no_presente"
    if con_saldo:
        return "con_saldo"
    return "sin_saldo"


def calcular_ranking_areas(cliente: str) -> Optional[pd.DataFrame]:
    try:
        tb_raw = leer_tb(cliente)
        if tb_raw is None or tb_raw.empty:
            return None

        tb = _preparar_tb(tb_raw)
        if tb.empty:
            return None

        variaciones = _preparar_variaciones(calcular_variaciones(cliente))
        perfil = _safe_call(leer_perfil, cliente, default={}) or {}
        mat = _calcular_materialidad_cliente(cliente)

        total_balance = _to_float(tb["saldo_abs"].sum())
        materialidad_ejecucion = _to_float(mat.get("materialidad_ejecucion", 0))

        areas_auditoria = _cargar_areas_auditoria(tb=tb)
        resultados: list[dict[str, Any]] = []

        for codigo_area, info_area in areas_auditoria.items():
            resultado = _calcular_score_area(
                codigo=codigo_area,
                info=info_area,
                tb=tb,
                variaciones=variaciones,
                total_balance=total_balance,
                materialidad_ejecucion=materialidad_ejecucion,
                perfil=perfil,
                mat=mat,
            )
            resultados.append(resultado)

        ranking_df = pd.DataFrame(resultados)
        ranking_df = ranking_df.sort_values("score_riesgo", ascending=False).reset_index(drop=True)
        ranking_df["ranking"] = range(1, len(ranking_df) + 1)
        return ranking_df

    except (ValueError, TypeError, KeyError) as exc:
        LOGGER.error("ranking.error_calculando", extra={"cliente": cliente, "error": str(exc)})
        return None


def _calcular_score_area(
    codigo: str,
    info: Dict[str, Any],
    tb: pd.DataFrame,
    variaciones: pd.DataFrame,
    total_balance: float,
    materialidad_ejecucion: float,
    perfil: dict[str, Any],
    mat: dict[str, Any],
) -> Dict[str, Any]:
    tb_area, tb_method = seleccionar_filas_area_por_ls(tb, codigo)

    presente = not tb_area.empty

    if tb_area.empty:
        base = {
            "area": codigo,
            "nombre": info["nombre"],
            "saldo_total": 0.0,
            "pct_total": 0.0,
            "num_cuentas": 0,
            "score_materialidad": 0.0,
            "score_variacion": 0.0,
            "score_complejidad": 0.0,
            "score_riesgo_inherente": round(info["peso"] * 10, 2),
            "score_riesgo": round(info["peso"] * 10, 2),
            "materialidad_relativa": 0.0,
            "expert_flags": [],
            "expert_flags_count": 0,
            "materialidad_sugerida": _to_float(mat.get("materialidad_sugerida", 0)),
            "materialidad_ejecucion": _to_float(mat.get("materialidad_ejecucion", 0)),
            "trivialidad": _to_float(mat.get("trivialidad", 0)),
            "presente": False,
            "con_saldo": False,
            "estado_presencia": "no_presente",
        }
        base["justificacion"] = _construir_justificacion(base)
        base["prioridad"] = _prioridad_accionable(base["score_riesgo"], 0, 0)
        _debug_area_selection(codigo, info["nombre"], tb_area, tb_method, pd.DataFrame(), "n/a")
        return base

    saldo_area = _to_float(tb_area["saldo_abs"].sum())
    pct_total = _safe_percentage(saldo_area, total_balance)
    score_materialidad = min(pct_total / 2.5, 40)

    if not variaciones.empty:
        var_area, var_method = seleccionar_filas_area_por_ls(variaciones, codigo)
    else:
        var_area, var_method = pd.DataFrame(), "variaciones_empty"
    score_variacion = min(len(var_area) * 5, 30) if not var_area.empty else 0.0
    variacion_abs_total = _to_float(var_area["impacto"].sum()) if not var_area.empty else 0.0

    num_cuentas = int(len(tb_area))
    score_complejidad = min(num_cuentas / 20, 20)
    score_riesgo_inherente = info["peso"] * 10

    materialidad_relativa = _safe_percentage(saldo_area, materialidad_ejecucion)

    flags = detectar_expert_flags(
        codigo_area=codigo,
        perfil=perfil,
        metricas_area={
            "saldo_total": saldo_area,
            "pct_total": pct_total,
            "variacion_abs_total": variacion_abs_total,
            "materialidad_relativa": materialidad_relativa,
        },
    )
    flags_count = len(flags)

    score_flags = min(flags_count * 8, 16)
    score_total = score_materialidad + score_variacion + score_complejidad + score_riesgo_inherente + score_flags
    score_total += _holding_context_boost(codigo, perfil)

    con_saldo = saldo_area > 0.01
    zero_no_signal = (not con_saldo) and flags_count == 0 and variacion_abs_total <= 0.01
    if zero_no_signal:
        # Evita que areas sin saldo ni senales queden artificialmente altas.
        score_total = min(score_total, max(6.0, score_riesgo_inherente * 0.65))

    result = {
        "area": codigo,
        "nombre": info["nombre"],
        "saldo_total": round(saldo_area, 2),
        "pct_total": round(pct_total, 2),
        "num_cuentas": num_cuentas,
        "score_materialidad": round(score_materialidad, 2),
        "score_variacion": round(score_variacion, 2),
        "score_complejidad": round(score_complejidad, 2),
        "score_riesgo_inherente": round(score_riesgo_inherente, 2),
        "score_riesgo": round(score_total, 2),
        "materialidad_relativa": round(materialidad_relativa, 2),
        "materialidad_sugerida": round(_to_float(mat.get("materialidad_sugerida", 0)), 2),
        "materialidad_ejecucion": round(_to_float(mat.get("materialidad_ejecucion", 0)), 2),
        "trivialidad": round(_to_float(mat.get("trivialidad", 0)), 2),
        "expert_flags": flags,
        "expert_flags_count": flags_count,
        "variacion_abs_total": round(variacion_abs_total, 2),
        "presente": bool(presente),
        "con_saldo": bool(con_saldo),
        "estado_presencia": _estado_presencia(bool(presente), bool(con_saldo)),
    }

    result["justificacion"] = _construir_justificacion(result)
    prioridad = _prioridad_accionable(result["score_riesgo"], result["materialidad_relativa"], flags_count)
    if zero_no_signal:
        prioridad = "baja"
        result["justificacion"] = "area presente sin saldo relevante ni senales adicionales"
    result["prioridad"] = prioridad
    _debug_area_selection(codigo, info["nombre"], tb_area, tb_method, var_area, var_method)
    return result


def obtener_top_areas(cliente: str, top_n: int = 3) -> Optional[List[Tuple[str, str, float]]]:
    ranking = calcular_ranking_areas(cliente)
    if ranking is None or ranking.empty:
        return None

    top = ranking.head(top_n)
    return [(row["area"], row["nombre"], row["score_riesgo"]) for _, row in top.iterrows()]


def resumen_riesgos(cliente: str) -> Optional[Dict[str, Any]]:
    ranking = calcular_ranking_areas(cliente)
    if ranking is None or ranking.empty:
        return None

    return {
        "total_areas": len(ranking),
        "score_riesgo_promedio": round(ranking["score_riesgo"].mean(), 2),
        "area_mayor_riesgo": ranking.iloc[0]["nombre"],
        "score_mayor_riesgo": ranking.iloc[0]["score_riesgo"],
        "top_3_areas": obtener_top_areas(cliente, 3),
    }


def obtener_indicadores_clave(cliente: str) -> Optional[Dict[str, Any]]:
    ranking = calcular_ranking_areas(cliente)
    resumen_tb = obtener_resumen_tb(cliente)

    if ranking is None or resumen_tb is None:
        return None

    return {
        "areas_alto_riesgo": len(ranking[ranking["score_riesgo"] > 50]),
        "areas_medio_riesgo": len(ranking[(ranking["score_riesgo"] >= 30) & (ranking["score_riesgo"] <= 50)]),
        "areas_bajo_riesgo": len(ranking[ranking["score_riesgo"] < 30]),
        "patrimonio_total": resumen_tb.get("TOTAL", 0),
        "concentracion_principal_area": round(ranking.iloc[0]["pct_total"], 2) if len(ranking) > 0 else 0,
    }


def obtener_ranking_areas_cliente(cliente: str) -> Optional[pd.DataFrame]:
    """Compatibilidad con API legacy tras refactor."""
    return calcular_ranking_areas(cliente)
