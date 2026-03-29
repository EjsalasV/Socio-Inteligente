from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from analysis.lector_tb import leer_trial_balance
from analysis.variaciones import calcular_variaciones, marcar_movimientos_relevantes
from domain.services.leer_perfil import (
    cargar_perfil,
    ruta_tb_cliente,
    obtener_nombre_cliente,
    obtener_periodo,
)
from core.configuracion import obtener_scoring_config


def puntaje_por_variacion_absoluta(valor: float, config_thresholds: list | None = None) -> int:
    """
    Calcula puntuación por variación absoluta.

    Args:
        valor: Variación absoluta
        config_thresholds: Lista de [threshold, puntos] desde config (si None, usa defaults)

    Returns:
        Puntuación (0-5 típicamente)
    """
    valor = abs(valor)

    if config_thresholds is None:
        config_thresholds = [
            [100000, 5],
            [50000, 4],
            [10000, 3],
            [1000, 2],
            [500, 1],
        ]

    for threshold, puntos in config_thresholds:
        if valor >= threshold:
            return puntos

    return 0


def puntaje_por_saldo_actual(valor: float, config_thresholds: list | None = None) -> int:
    """
    Calcula puntuación por saldo actual.

    Args:
        valor: Saldo actual
        config_thresholds: Lista de [threshold, puntos] desde config (si None, usa defaults)

    Returns:
        Puntuación (0-5 típicamente)
    """
    valor = abs(valor)

    if config_thresholds is None:
        config_thresholds = [
            [1000000, 5],
            [500000, 4],
            [100000, 3],
            [10000, 2],
            [1000, 1],
        ]

    for threshold, puntos in config_thresholds:
        if valor >= threshold:
            return puntos

    return 0


def puntaje_por_variacion_porcentual(valor: float, config_thresholds: list | None = None) -> int:
    """
    Calcula puntuación por variación porcentual.

    Args:
        valor: Variación porcentual
        config_thresholds: Lista de [threshold, puntos] desde config (si None, usa defaults)

    Returns:
        Puntuación (0-5 típicamente)
    """
    valor = abs(valor)

    if config_thresholds is None:
        config_thresholds = [
            [100, 5],
            [50, 4],
            [20, 3],
            [10, 2],
            [1, 1],
        ]

    for threshold, puntos in config_thresholds:
        if valor >= threshold:
            return puntos

    return 0


def puntaje_por_grupo(grupo: str) -> int:
    grupo = str(grupo).strip().lower()

    if grupo in {"activo", "pasivo", "patrimonio", "ingresos"}:
        return 1

    return 0


def calcular_score_cuentas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula score de cada cuenta basado en variación, saldo y otros factores.
    Usa configuración desde config.yaml si está disponible.

    Args:
        df: DataFrame con variaciones y marcas ya calculadas

    Returns:
        DataFrame con columnas de score agregadas
    """
    df = df.copy()

    # Cargar configuración
    config_scoring = obtener_scoring_config()
    thresholds_var = config_scoring.get("variacion_absoluta")
    thresholds_saldo = config_scoring.get("saldo_actual")

    df["score_variacion"] = df["abs_variacion_absoluta"].apply(
        lambda x: puntaje_por_variacion_absoluta(x, config_thresholds=thresholds_var)
    )
    df["score_saldo"] = df["saldo_actual"].apply(
        lambda x: puntaje_por_saldo_actual(x, config_thresholds=thresholds_saldo)
    )
    df["score_grupo"] = df["grupo"].apply(puntaje_por_grupo)
    df["score_movimiento_relevante"] = df["flag_movimiento_relevante"].apply(
        lambda x: 2 if x else 0
    )
    df["score_sin_base"] = ((df["flag_sin_base"]) & (df["abs_variacion_absoluta"] >= 1000)).apply(
        lambda x: 2 if x else 0
    )

    df["score_total"] = (
        df["score_variacion"]
        + df["score_saldo"]
        + df["score_grupo"]
        + df["score_movimiento_relevante"]
        + df["score_sin_base"]
    )

    return df


def ranking_cuentas(df: pd.DataFrame) -> pd.DataFrame:
    columnas_salida = [
        "numero_cuenta",
        "nombre_cuenta",
        "grupo",
        "subgrupo",
        "saldo_anterior",
        "saldo_actual",
        "variacion_absoluta",
        "abs_variacion_absoluta",
        "variacion_porcentual",
        "flag_sin_base",
        "flag_movimiento_relevante",
        "score_variacion",
        "score_saldo",
        "score_grupo",
        "score_movimiento_relevante",
        "score_sin_base",
        "score_total",
    ]

    df = df[columnas_salida].copy()

    df = df.sort_values(by=["score_total", "abs_variacion_absoluta"], ascending=[False, False])

    df = df.reset_index(drop=True)

    return df


def imprimir_ranking_cuentas(nombre_cliente: str) -> None:
    perfil = cargar_perfil(nombre_cliente)
    ruta_tb = ruta_tb_cliente(nombre_cliente)

    if not Path(ruta_tb).exists():
        raise FileNotFoundError(f"No existe el TB del cliente en: {ruta_tb}")

    df_tb = leer_trial_balance(ruta_tb)

    if df_tb.empty:
        print("El TB está vacío.")
        return

    df_var = calcular_variaciones(df_tb)
    df_var = marcar_movimientos_relevantes(df_var)
    df_score = calcular_score_cuentas(df_var)
    df_rank = ranking_cuentas(df_score)

    cliente = obtener_nombre_cliente(perfil)
    periodo = obtener_periodo(perfil)

    print("\n====================================================")
    print("RANKING DE CUENTAS")
    print("====================================================\n")
    print(f"Cliente: {cliente}")
    print(f"Periodo: {periodo}")
    print(f"TB usado: {ruta_tb}\n")

    with pd.option_context(
        "display.max_rows",
        50,
        "display.max_columns",
        None,
        "display.width",
        240,
        "display.float_format",
        "{:,.2f}".format,
    ):
        print(df_rank.head(30))


if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise ValueError(
                "Debes indicar el nombre de la carpeta del cliente. "
                "Ejemplo: python motor/ranking_cuentas.py bf_holding_2025"
            )

        cliente = sys.argv[1]
        imprimir_ranking_cuentas(cliente)

    except Exception as e:
        print(f"\nError generando ranking de cuentas: {e}")
