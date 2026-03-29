from __future__ import annotations

import pandas as pd
from typing import Optional, Dict

from analysis.lector_tb import leer_tb
from core.utils.normalizaciones import normalizar_ls


def calcular_variaciones(
    cliente: str, tb_anterior: Optional[pd.DataFrame] = None
) -> Optional[pd.DataFrame]:
    try:
        tb = leer_tb(cliente)

        if tb is None or tb.empty:
            return None

        tb = tb.copy()

        if "codigo" in tb.columns:
            tb["codigo"] = tb["codigo"].apply(normalizar_ls)

        if "saldo_abs" not in tb.columns and "saldo" in tb.columns:
            tb["saldo_abs"] = tb["saldo"].abs()

        if tb_anterior is not None and not tb_anterior.empty:
            variaciones_df = _calcular_diffs(tb, tb_anterior)
        else:
            variaciones_df = _detectar_cuentas_significativas(tb)

        if variaciones_df is None or variaciones_df.empty:
            return None

        variaciones_df = variaciones_df.sort_values("impacto", ascending=False)

        return variaciones_df

    except Exception:
        return None


def _calcular_diffs(tb_actual: pd.DataFrame, tb_anterior: pd.DataFrame) -> pd.DataFrame:

    if "codigo" not in tb_actual.columns or "codigo" not in tb_anterior.columns:
        return pd.DataFrame()

    tb_act = tb_actual[["codigo", "nombre", "saldo"]].copy()
    tb_ant = tb_anterior[["codigo", "saldo"]].copy()

    tb_act["codigo"] = tb_act["codigo"].apply(normalizar_ls)
    tb_ant["codigo"] = tb_ant["codigo"].apply(normalizar_ls)

    tb_ant.rename(columns={"saldo": "saldo_anterior"}, inplace=True)

    merged = pd.merge(tb_act, tb_ant, on="codigo", how="left")
    merged["saldo_anterior"] = merged["saldo_anterior"].fillna(0)

    merged["diferencia"] = merged["saldo"] - merged["saldo_anterior"]
    merged["variacion_pct"] = 0.0

    mask = merged["saldo_anterior"] != 0
    merged.loc[mask, "variacion_pct"] = (
        merged.loc[mask, "diferencia"] / merged.loc[mask, "saldo_anterior"].abs()
    ) * 100

    significativas = merged[merged["variacion_pct"].abs() > 10].copy()
    significativas["impacto"] = significativas["diferencia"].abs()

    return significativas


def _detectar_cuentas_significativas(tb: pd.DataFrame) -> pd.DataFrame:

    if "saldo_abs" not in tb.columns:
        return pd.DataFrame()

    top_cuentas = tb.nlargest(20, "saldo_abs").copy()

    total_saldo = tb["saldo_abs"].sum()

    if total_saldo > 0:
        top_cuentas["pct_total"] = (top_cuentas["saldo_abs"] / total_saldo) * 100
    else:
        top_cuentas["pct_total"] = 0

    top_cuentas["impacto"] = top_cuentas["saldo_abs"]

    return top_cuentas


def obtener_cuentas_de_riesgo(cliente: str, umbral_pct: float = 5.0) -> Optional[pd.DataFrame]:

    variaciones = calcular_variaciones(cliente)

    if variaciones is None or variaciones.empty:
        return None

    if "variacion_pct" in variaciones.columns:
        cuentas_riesgo = variaciones[variaciones["variacion_pct"].abs() >= umbral_pct]
    else:
        cuentas_riesgo = variaciones[variaciones["pct_total"] >= umbral_pct]

    return cuentas_riesgo if not cuentas_riesgo.empty else None


def resumen_variaciones(cliente: str) -> Optional[Dict]:

    variaciones = calcular_variaciones(cliente)

    if variaciones is None or variaciones.empty:
        return None

    return {
        "total_cuentas_variacion": len(variaciones),
        "mayor_variacion": variaciones["impacto"].max(),
        "suma_variaciones": variaciones["impacto"].sum(),
        "cuentas_top_5": variaciones["nombre"].head(5).tolist(),
    }


def marcar_movimientos_relevantes(df_var: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Compatibilidad con API legacy: devuelve el DataFrame recibido."""
    return df_var if df_var is not None else pd.DataFrame()
