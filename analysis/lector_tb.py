"""
Servicio para leer y procesar Trial Balance (TB).

Utiliza cliente_repository como base y añade normalizacion defensiva
para esquemas reales de clientes.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Optional

import pandas as pd

from infra.repositories.cliente_repository import cargar_tb as repo_cargar_tb


def _normalize_header(col: Any) -> str:
    txt = str(col or "").strip().lower()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
    txt = txt.replace("%", " pct ")
    txt = re.sub(r"[^a-z0-9]+", "_", txt)
    txt = re.sub(r"_+", "_", txt).strip("_")
    return txt


def _first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = set(df.columns)
    for cand in candidates:
        if cand in cols:
            return cand
    return None


def _to_numeric(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    s = s.str.replace(",", "", regex=False)
    s = s.str.replace("$", "", regex=False)
    s = s.replace({"": None, "nan": None, "None": None})
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def _normalizar_ls_val(v: Any) -> str:
    txt = str(v).strip()
    if not txt or txt.lower() in {"nan", "none"}:
        return ""
    try:
        f = float(txt)
        if f.is_integer():
            return str(int(f))
    except Exception:
        pass
    return txt


def leer_tb(cliente: str) -> Optional[pd.DataFrame]:
    if not cliente or not isinstance(cliente, str):
        return None
    """
    Lee y procesa el Trial Balance de un cliente.

    Returns:
        DataFrame procesado o None cuando no hay datos.
    """
    try:
        tb = repo_cargar_tb(cliente)
        if tb is None or tb.empty:
            print(f"[WARN] No se encontro TB para: {cliente}")
            return None

        tb = _normalizar_columnas(tb)
        tb = _mapear_columnas_canonicas(tb)
        tb = _validar_tb(tb)
        tb = _enriquecer_tb(tb)

        print(f"[OK] TB cargado para {cliente}: {tb.shape[0]} filas")
        return tb
    except Exception as e:
        print(f"[ERROR] Error al leer TB de {cliente}: {e}")
        return None


def _normalizar_columnas(tb: pd.DataFrame) -> pd.DataFrame:
    tb = tb.copy()
    tb.columns = [_normalize_header(c) for c in tb.columns]
    return tb


def _mapear_columnas_canonicas(tb: pd.DataFrame) -> pd.DataFrame:
    tb = tb.copy()

    # codigo de cuenta
    codigo_src = _first_col(
        tb,
        [
            "codigo",
            "numero_de_cuenta",
            "numero_cuenta",
            "cuenta",
            "cod_cuenta",
            "codigo_cuenta",
        ],
    )
    if codigo_src:
        tb["codigo"] = tb[codigo_src].astype(str).str.strip()
    else:
        tb["codigo"] = ""

    # nombre cuenta
    nombre_src = _first_col(
        tb,
        ["nombre", "nombre_cuenta", "descripcion", "detalle", "cuenta_nombre"],
    )
    if nombre_src:
        tb["nombre"] = tb[nombre_src].astype(str).str.strip()
    else:
        tb["nombre"] = ""

    # l/s
    ls_src = _first_col(
        tb,
        ["ls", "l_s", "linea_significancia", "linea_de_significancia"],
    )
    if ls_src:
        tb["ls"] = tb[ls_src].apply(_normalizar_ls_val)
    else:
        tb["ls"] = ""

    # correspondencia
    corr_src = _first_col(
        tb,
        ["no_correspondencia", "correspondencia", "codigo_correspondencia"],
    )
    if corr_src:
        tb["no_correspondencia"] = tb[corr_src].astype(str).str.strip()

    # saldos
    s2025_src = _first_col(tb, ["saldo_2025", "saldo_actual", "saldo"])
    s2024_src = _first_col(tb, ["saldo_2024", "saldo_anterior"])
    spre_src = _first_col(tb, ["saldo_preliminar"])

    tb["saldo_2025"] = _to_numeric(tb[s2025_src]) if s2025_src else 0.0
    tb["saldo_2024"] = _to_numeric(tb[s2024_src]) if s2024_src else 0.0
    tb["saldo_preliminar"] = _to_numeric(tb[spre_src]) if spre_src else tb["saldo_2025"]

    # columna base esperada por modulos existentes
    tb["saldo_actual"] = tb["saldo_2025"]
    tb["saldo"] = tb["saldo_actual"]

    return tb


def _validar_tb(tb: pd.DataFrame) -> pd.DataFrame:
    tb = tb.copy()
    if "codigo" not in tb.columns:
        tb["codigo"] = ""
    if "nombre" not in tb.columns:
        tb["nombre"] = ""
    if "saldo" not in tb.columns:
        tb["saldo"] = 0.0

    tb["codigo"] = tb["codigo"].astype(str).str.strip()
    tb["nombre"] = tb["nombre"].astype(str).str.strip()
    tb["saldo"] = _to_numeric(tb["saldo"])

    return tb


def _enriquecer_tb(tb: pd.DataFrame) -> pd.DataFrame:
    tb = tb.copy()
    tb["tipo_cuenta"] = tb["codigo"].apply(_clasificar_cuenta)
    tb["saldo_abs"] = tb["saldo"].abs()
    return tb


def _clasificar_cuenta(codigo: str) -> str:
    txt = str(codigo or "").strip()
    if not txt:
        return "OTRA"
    first = txt[0]
    clasificacion = {
        "1": "ACTIVO",
        "2": "PASIVO",
        "3": "PATRIMONIO",
        "4": "INGRESOS",
        "5": "GASTOS",
        "6": "GANANCIAS",
        "7": "PERDIDAS",
    }
    return clasificacion.get(first, "OTRA")


def obtener_resumen_tb(cliente: str) -> Optional[dict]:
    tb = leer_tb(cliente)
    if tb is None:
        return None

    resumen = {}
    if "tipo_cuenta" in tb.columns and "saldo" in tb.columns:
        resumen = tb.groupby("tipo_cuenta")["saldo"].sum().to_dict()
    if "saldo" in tb.columns:
        resumen["TOTAL"] = float(tb["saldo"].sum())
    return resumen


def obtener_diagnostico_tb(cliente: str, sample_rows: int = 5) -> dict[str, Any]:
    """
    Resumen debug de carga TB para validar pipeline de datos.
    """
    tb = leer_tb(cliente)
    if tb is None or tb.empty:
        return {
            "cliente": cliente,
            "rows_loaded": 0,
            "columns_detected": [],
            "rows_saldo_no_cero": 0,
            "rows_codigo_presentes": 0,
            "rows_ls_presentes": 0,
            "sample_first_rows": [],
        }

    saldo_nz = int((pd.to_numeric(tb.get("saldo", 0), errors="coerce").fillna(0.0) != 0).sum())
    codigo_ok = int(tb.get("codigo", pd.Series(dtype=str)).astype(str).str.strip().ne("").sum())
    ls_ok = int(tb.get("ls", pd.Series(dtype=str)).astype(str).str.strip().ne("").sum())

    return {
        "cliente": cliente,
        "rows_loaded": int(len(tb)),
        "columns_detected": list(tb.columns),
        "rows_saldo_no_cero": saldo_nz,
        "rows_codigo_presentes": codigo_ok,
        "rows_ls_presentes": ls_ok,
        "sample_first_rows": tb.head(max(1, sample_rows)).to_dict(orient="records"),
    }


def filtrar_por_tipo(cliente: str, tipo: str) -> Optional[pd.DataFrame]:
    tb = leer_tb(cliente)
    if tb is None or "tipo_cuenta" not in tb.columns:
        return None
    filtrado = tb[tb["tipo_cuenta"] == tipo.upper()]
    return filtrado if not filtrado.empty else None


def filtrar_por_saldo_minimo(cliente: str, minimo: float) -> Optional[pd.DataFrame]:
    tb = leer_tb(cliente)
    if tb is None or "saldo_abs" not in tb.columns:
        return None
    filtrado = tb[tb["saldo_abs"] >= minimo].sort_values("saldo_abs", ascending=False)
    return filtrado if not filtrado.empty else None


def obtener_cuentas_por_area(cliente: str, area_codigo: str) -> Optional[pd.DataFrame]:
    tb = leer_tb(cliente)
    if tb is None:
        return None

    area_code = str(area_codigo).strip()
    if not area_code:
        return None

    # Priorizar match LS exacto cuando existe.
    if "ls" in tb.columns and tb["ls"].astype(str).str.strip().eq(area_code).any():
        filtrado = tb[tb["ls"].astype(str).str.strip() == area_code]
    else:
        filtrado = tb[tb["codigo"].astype(str).str.startswith(area_code)]
    return filtrado if not filtrado.empty else None


def leer_trial_balance(cliente: str) -> Optional[pd.DataFrame]:
    """Compatibilidad con nombre legacy tras refactor."""
    return leer_tb(cliente)
