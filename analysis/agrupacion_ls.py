from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from analysis.lector_tb import leer_trial_balance
from analysis.variaciones import calcular_variaciones, marcar_movimientos_relevantes
from core.utils.normalizaciones import normalizar_ls
from domain.services.leer_perfil import (
    cargar_perfil,
    ruta_tb_cliente,
    obtener_nombre_cliente,
    obtener_periodo,
)


def agrupar_por_ls(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "ls" not in df.columns:
        raise ValueError("El TB no contiene la columna L/S.")

    df["ls"] = df["ls"].apply(normalizar_ls)

    resumen = (
        df.groupby("ls")
        .agg(
            cuentas=("numero_cuenta", "count"),
            saldo_anterior=("saldo_anterior", "sum"),
            saldo_actual=("saldo_actual", "sum"),
            variacion_total=("variacion_absoluta", "sum"),
            abs_variacion_total=("abs_variacion_absoluta", "sum"),
            cuentas_relevantes=("flag_movimiento_relevante", "sum"),
            cuentas_sin_base=("flag_sin_base", "sum"),
        )
        .reset_index()
    )

    resumen["variacion_porcentual"] = (
        resumen["variacion_total"] / resumen["saldo_anterior"].replace(0, pd.NA)
    ) * 100

    resumen = resumen.sort_values(by="abs_variacion_total", ascending=False).reset_index(drop=True)

    return resumen


def imprimir_agrupacion_ls(nombre_cliente: str) -> None:
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

    df_ls = agrupar_por_ls(df_var)

    cliente = obtener_nombre_cliente(perfil)
    periodo = obtener_periodo(perfil)

    print("\n====================================================")
    print("AGRUPACIÓN POR L/S")
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
        print(df_ls)


if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise ValueError(
                "Debes indicar el nombre de la carpeta del cliente. "
                "Ejemplo: python motor/agrupacion_ls.py bf_holding_2025"
            )

        cliente = sys.argv[1]
        imprimir_agrupacion_ls(cliente)

    except Exception as e:
        print(f"\nError en agrupación por L/S: {e}")
