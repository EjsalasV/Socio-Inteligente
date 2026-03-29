from __future__ import annotations

from typing import Any

import pandas as pd


def normalizar_ls(valor: Any) -> str:
    """
    Normaliza valores de L/S (Line of Service) a formato estándar.

    Reglas:
    - Elimina espacios
    - Convierte a string
    - Elimina .0 solo si es decimal exacto
    - Maneja None / NaN

    Ejemplos:
        "14.0" → "14"
        " 130.1 " → "130.1"
        130.0 → "130"
        130.1 → "130.1"
        None → ""
    """
    if valor is None:
        return ""

    valor_str = str(valor).strip()

    if valor_str.lower() in {"nan", "none", ""}:
        return ""

    try:
        numero = float(valor_str)

        # Si es entero (ej: 130.0)
        if numero.is_integer():
            return str(int(numero))

        return str(numero)

    except ValueError:
        # Si no es numérico, devolver limpio
        return valor_str


def normalizar_ls_dataframe(df: pd.DataFrame, columna_ls: str = "ls") -> pd.DataFrame:
    """
    Normaliza la columna L/S en un DataFrame.
    Si la columna no existe, retorna el DataFrame sin cambios.
    """
    if columna_ls not in df.columns:
        return df  # columna ausente: no-op seguro

    df = df.copy()
    df[columna_ls] = df[columna_ls].apply(normalizar_ls)
    return df


def normalizar_columnas_texto(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia columnas tipo texto:
    - elimina espacios
    - convierte a string

    Útil para limpieza general de TB.

    Args:
        df: DataFrame

    Returns:
        DataFrame limpio
    """
    df = df.copy()

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()

    return df
