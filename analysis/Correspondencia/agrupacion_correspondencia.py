from __future__ import annotations

import sys
from typing import Any

import pandas as pd

from analysis.lector_tb import leer_tb
from analysis.variaciones import calcular_variaciones
from domain.services.leer_perfil import leer_perfil, obtener_nombre_cliente, obtener_periodo
from infra.repositories.catalogo_repository import (
    cargar_correspondencia_catalogo,
    obtener_modo_correspondencia,
)


def _to_float_series(df: pd.DataFrame, candidates: list[str], default: float = 0.0) -> pd.Series:
    for col in candidates:
        if col in df.columns:
            return pd.to_numeric(df[col], errors="coerce").fillna(default)
    return pd.Series([default] * len(df), index=df.index, dtype=float)


def _resolve_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _obtener_mapa_correspondencia(perfil: dict[str, Any] | None) -> tuple[str, dict[str, str]]:
    catalogo = cargar_correspondencia_catalogo()
    modo = obtener_modo_correspondencia(perfil)

    mapa = catalogo.get(modo)
    if not isinstance(mapa, dict) or not mapa:
        modo = "con_inventario"
        mapa = catalogo.get("con_inventario", {})

    if not mapa:
        mapa = {"Activo corriente": "1.1.2.10.100"}

    return modo, mapa


def clasificar_correspondencia(no_correspondencia: Any, mapa: dict[str, str] | None = None) -> str:
    """
    Clasifica una cuenta segun su prefijo de correspondencia.
    """
    valor = str(no_correspondencia or "").strip()
    if not valor:
        return "Sin correspondencia"

    mapa = mapa or cargar_correspondencia_catalogo().get("con_inventario", {})
    if not isinstance(mapa, dict) or not mapa:
        return "Sin correspondencia"

    for categoria, prefijo in sorted(mapa.items(), key=lambda kv: len(str(kv[1])), reverse=True):
        pref = str(prefijo).strip()
        if pref and valor.startswith(pref):
            return str(categoria)
    return "Sin correspondencia"


def agrupar_correspondencia(df: pd.DataFrame, mapa: dict[str, str] | None = None) -> pd.DataFrame:
    """
    Agrupa cuentas por categoria de correspondencia.
    """
    if df is None or df.empty:
        return pd.DataFrame(
            columns=[
                "area_correspondencia",
                "cuentas",
                "saldo_total",
                "variacion_total",
                "abs_variacion_total",
                "variacion_porcentual",
            ]
        )

    base = df.copy()

    corr_col = _resolve_col(base, ["no_correspondencia", "correspondencia", "codigo_correspondencia"])
    if corr_col is None:
        raise ValueError(
            "Faltan columnas requeridas para agrupacion por correspondencia: no_correspondencia/correspondencia"
        )

    base["no_correspondencia"] = base[corr_col].astype(str).str.strip()
    base["saldo_total"] = _to_float_series(base, ["saldo_actual", "saldo", "saldo_2025", "saldo_preliminar"])
    base["variacion_total"] = _to_float_series(base, ["variacion_absoluta", "impacto", "diferencia"])
    base["abs_variacion_total"] = base["variacion_total"].abs()
    base["area_correspondencia"] = base["no_correspondencia"].apply(lambda x: clasificar_correspondencia(x, mapa))

    resumen = (
        base.groupby("area_correspondencia", dropna=False)
        .agg(
            cuentas=("no_correspondencia", "count"),
            saldo_total=("saldo_total", "sum"),
            variacion_total=("variacion_total", "sum"),
            abs_variacion_total=("abs_variacion_total", "sum"),
        )
        .reset_index()
    )

    resumen["variacion_porcentual"] = (
        resumen["variacion_total"] / resumen["saldo_total"].replace(0, pd.NA)
    ) * 100
    resumen = resumen.sort_values(by="abs_variacion_total", ascending=False).reset_index(drop=True)
    return resumen


def obtener_agrupacion_correspondencia(cliente: str) -> pd.DataFrame:
    """
    Devuelve la agrupacion por correspondencia para un cliente.
    """
    perfil = leer_perfil(cliente) or {}
    df_tb = leer_tb(cliente)
    if df_tb is None or df_tb.empty:
        raise ValueError(f"El TB del cliente '{cliente}' esta vacio o no existe.")

    modo, mapa = _obtener_mapa_correspondencia(perfil)
    base = df_tb.copy()

    if "variacion_absoluta" not in base.columns:
        df_var = calcular_variaciones(cliente)
        if df_var is not None and not df_var.empty:
            tb_code_col = _resolve_col(base, ["codigo", "numero_de_cuenta", "cuenta", "cod_cuenta"])
            var_code_col = _resolve_col(df_var, ["codigo", "numero_de_cuenta", "cuenta", "cod_cuenta"])
            if tb_code_col and var_code_col and "impacto" in df_var.columns:
                impacto_map = (
                    df_var[[var_code_col, "impacto"]]
                    .dropna(subset=[var_code_col])
                    .assign(_k=lambda d: d[var_code_col].astype(str).str.strip())
                    .groupby("_k")["impacto"]
                    .sum()
                    .to_dict()
                )
                base["variacion_absoluta"] = (
                    base[tb_code_col].astype(str).str.strip().map(impacto_map).fillna(0.0)
                )
            else:
                base["variacion_absoluta"] = 0.0

    resultado = agrupar_correspondencia(base, mapa=mapa)
    resultado.attrs["modo_correspondencia"] = modo
    return resultado


def imprimir_agrupacion_correspondencia(cliente: str) -> None:
    """
    Imprime en consola la agrupacion por correspondencia.
    """
    perfil = leer_perfil(cliente) or {}
    nombre_cliente = obtener_nombre_cliente(perfil) or cliente
    periodo = obtener_periodo(perfil) or "N/A"

    resumen = obtener_agrupacion_correspondencia(cliente)
    modo, _ = _obtener_mapa_correspondencia(perfil)

    print("\n====================================================")
    print("AGRUPACION POR CORRESPONDENCIA")
    print("====================================================\n")
    print(f"Cliente: {nombre_cliente}")
    print(f"Periodo: {periodo}")
    print(f"Modo de correspondencia: {modo}\n")

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
        print(resumen)


if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise ValueError(
                "Debes indicar el nombre de la carpeta del cliente. "
                "Ejemplo: python -m analysis.Correspondencia.agrupacion_correspondencia cliente_demo"
            )
        imprimir_agrupacion_correspondencia(sys.argv[1])
    except Exception as exc:
        print(f"\nError en agrupacion por correspondencia: {exc}")

