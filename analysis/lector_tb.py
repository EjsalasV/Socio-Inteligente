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

from infra.repositories.cliente_repository import _resolve_cliente_dir, cargar_tb as repo_cargar_tb

# Module-level TB cache
# Populated by app_streamlit.py so internal services
# can access uploaded TBs without filesystem access
_TB_CACHE: dict[str, tuple[str, "pd.DataFrame"]] = {}


def _tb_file_signature(cliente: str) -> str:
    try:
        tb_path = _resolve_cliente_dir(cliente) / "tb.xlsx"
        if not tb_path.exists():
            return "missing"
        stat = tb_path.stat()
        return f"{int(stat.st_mtime_ns)}:{int(stat.st_size)}"
    except Exception:
        return "missing"


def set_tb_cache(cliente: str, df: "pd.DataFrame") -> None:
    """Store a TB DataFrame in module cache."""
    if isinstance(df, pd.DataFrame) and not df.empty:
        _TB_CACHE[str(cliente).strip()] = ("manual", df.copy())


def get_tb_cache(cliente: str, *, signature: str | None = None) -> "Optional[pd.DataFrame]":
    """Retrieve a TB DataFrame from module cache."""
    key = str(cliente).strip()
    cached = _TB_CACHE.get(key)
    if not cached:
        return None
    cached_signature, cached_df = cached
    if signature and cached_signature not in {"manual", signature}:
        return None
    return cached_df.copy()


def clear_tb_cache(cliente: str) -> None:
    """Remove a client's TB from cache."""
    _TB_CACHE.pop(str(cliente).strip(), None)


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


def _is_effectively_empty(series: pd.Series) -> bool:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() == 0:
        return True
    return float(numeric.fillna(0.0).abs().sum()) == 0.0


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

    signature = _tb_file_signature(cliente)
    if signature == "missing":
        clear_tb_cache(cliente)
        return None

    cached = get_tb_cache(cliente, signature=signature)
    if cached is not None:
        return cached

    """
    Lee y procesa el Trial Balance de un cliente.

    Returns:
        DataFrame procesado o None cuando no hay datos.
    """
    try:
        tb = repo_cargar_tb(cliente)
        if tb is None or tb.empty:
            print(f"[WARN] No se encontro TB para: {cliente}")
            clear_tb_cache(cliente)
            return None

        tb = _normalizar_columnas(tb)
        tb = _mapear_columnas_canonicas(tb)
        tb = _validar_tb(tb)
        tb = _enriquecer_tb(tb)

        _TB_CACHE[str(cliente).strip()] = (signature, tb.copy())
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

    saldo_2025_series = tb[s2025_src] if s2025_src else pd.Series([0.0] * len(tb))
    saldo_2024_series = tb[s2024_src] if s2024_src else pd.Series([0.0] * len(tb))
    saldo_preliminar_series = tb[spre_src] if spre_src else pd.Series([0.0] * len(tb))

    tb["saldo_2025"] = _to_numeric(saldo_2025_series)
    tb["saldo_2024"] = _to_numeric(saldo_2024_series)
    tb["saldo_preliminar"] = _to_numeric(saldo_preliminar_series)

    # Si "Saldo 2025" viene vacío (muy común en cargas preliminares),
    # usar "Saldo preliminar" como saldo actual real del trabajo.
    has_2025 = not _is_effectively_empty(saldo_2025_series)
    has_preliminar = not _is_effectively_empty(saldo_preliminar_series)
    has_2024 = not _is_effectively_empty(saldo_2024_series)

    # Seleccion efectiva segun estado del trabajo:
    # final -> 2025, preliminar -> saldo preliminar, inicial -> 2024.
    if has_2025:
        tb["saldo_actual"] = tb["saldo_2025"]
        tb["saldo_anterior"] = tb["saldo_preliminar"] if has_preliminar else tb["saldo_2024"]
        tb["tb_stage"] = "final"
        tb["saldo_fuente_actual"] = "saldo_2025"
        tb["saldo_fuente_anterior"] = "saldo_preliminar" if has_preliminar else "saldo_2024"
    elif has_preliminar:
        tb["saldo_actual"] = tb["saldo_preliminar"]
        tb["saldo_anterior"] = tb["saldo_2024"]
        tb["tb_stage"] = "preliminar"
        tb["saldo_fuente_actual"] = "saldo_preliminar"
        tb["saldo_fuente_anterior"] = "saldo_2024"
    elif has_2024:
        tb["saldo_actual"] = tb["saldo_2024"]
        tb["saldo_anterior"] = pd.Series([0.0] * len(tb))
        tb["tb_stage"] = "inicial"
        tb["saldo_fuente_actual"] = "saldo_2024"
        tb["saldo_fuente_anterior"] = "none"
    else:
        tb["saldo_actual"] = pd.Series([0.0] * len(tb))
        tb["saldo_anterior"] = pd.Series([0.0] * len(tb))
        tb["tb_stage"] = "sin_saldos"
        tb["saldo_fuente_actual"] = "none"
        tb["saldo_fuente_anterior"] = "none"

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


def obtener_resumen_tb(
    cliente: str,
    df: Optional[pd.DataFrame] = None,
) -> Optional[dict]:
    """
    Accepts optional df parameter so Streamlit can
    pass an already-loaded DataFrame directly,
    bypassing the file lookup.
    """
    tb = df if isinstance(df, pd.DataFrame) else leer_tb(cliente)
    if tb is None or tb.empty:
        return None

    resumen: dict = {}

    if "tipo_cuenta" in tb.columns and "saldo" in tb.columns:
        # Normalize tipo_cuenta to uppercase for grouping
        tb2 = tb.copy()
        tb2["tipo_cuenta_norm"] = (
            tb2["tipo_cuenta"].astype(str).str.strip().str.upper()
        )
        grouped = (
            tb2.groupby("tipo_cuenta_norm")["saldo"]
            .sum()
            .to_dict()
        )
        # Map common variants to canonical names
        mapping = {
            "ACTIVO": ["ACTIVO", "ACTIVOS", "ASSET", "ASSETS"],
            "PASIVO": ["PASIVO", "PASIVOS", "LIABILITY", "LIABILITIES"],
            "PATRIMONIO": ["PATRIMONIO", "EQUITY", "CAPITAL"],
            "INGRESOS": ["INGRESOS", "INGRESO", "REVENUE", "INCOME", "VENTAS"],
            "GASTOS": ["GASTOS", "GASTO", "EXPENSE", "EXPENSES", "COSTOS"],
        }
        for canonical, variants in mapping.items():
            total = sum(
                abs(float(grouped.get(v, 0)))
                for v in variants
                if v in grouped
            )
            if total > 0:
                resumen[canonical] = total

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
