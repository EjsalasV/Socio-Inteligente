"""
Ledger reader service (Libro Mayor).
Reads mayor.xlsx from client folder and provides
filtering and search functions.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Optional

import pandas as pd


DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "clientes"
MAYOR_FILENAME = "mayor.xlsx"


def _ruta_mayor(cliente: str) -> Path:
    return DATA_ROOT / cliente / MAYOR_FILENAME


def _normalize_header(col: Any) -> str:
    txt = str(col or "").strip().lower()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
    txt = re.sub(r"[^a-z0-9]+", "_", txt)
    return re.sub(r"_+", "_", txt).strip("_")


def _to_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype(str).str.strip()
         .str.replace(",", "", regex=False)
         .str.replace("$", "", regex=False)
         .replace({"": None, "nan": None}),
        errors="coerce",
    ).fillna(0.0)


def mayor_existe(cliente: str) -> bool:
    """Returns True if mayor.xlsx exists for the client."""
    return _ruta_mayor(cliente).exists()


def leer_mayor(cliente: str) -> Optional[pd.DataFrame]:
    """
    Loads and normalizes the ledger for a client.
    Returns None if file does not exist.
    """
    ruta = _ruta_mayor(cliente)
    if not ruta.exists():
        return None

    try:
        df = pd.read_excel(ruta, sheet_name=0, engine="openpyxl")
    except Exception as e:
        print(f"[ERROR] leer_mayor({cliente}): {e}")
        return None

    if df is None or df.empty:
        return None

    df = df.dropna(how="all").reset_index(drop=True)
    df.columns = [_normalize_header(c) for c in df.columns]

    # Canonical columns
    col_map = {
        "fecha":         ["fecha", "date", "fecha_mov"],
        "numero_cuenta": ["numero_cuenta", "cuenta", "codigo",
                          "cod_cuenta", "numero_de_cuenta"],
        "nombre_cuenta": ["nombre_cuenta", "nombre", "descripcion_cuenta"],
        "ls":            ["ls", "l_s", "linea_significancia"],
        "descripcion":   ["descripcion", "detalle", "concepto",
                          "glosa", "referencia_descripcion"],
        "referencia":    ["referencia", "comprobante", "voucher",
                          "numero_doc", "doc"],
        "debe":          ["debe", "debito", "debit"],
        "haber":         ["haber", "credito", "credit"],
        "saldo":         ["saldo", "saldo_acumulado", "balance"],
        "tipo":          ["tipo", "type", "dc"],
    }

    def _find(candidates):
        for c in candidates:
            if c in df.columns:
                return c
        return None

    out = pd.DataFrame()
    for canon, cands in col_map.items():
        src = _find(cands)
        if src:
            out[canon] = df[src]
        else:
            out[canon] = None

    # Type coercions
    out["debe"] = _to_numeric(out["debe"].fillna(0))
    out["haber"] = _to_numeric(out["haber"].fillna(0))
    out["saldo"] = _to_numeric(out["saldo"].fillna(0))

    try:
        out["fecha"] = pd.to_datetime(
            out["fecha"], errors="coerce", dayfirst=True
        )
    except Exception:
        pass

    out["numero_cuenta"] = out["numero_cuenta"].astype(str).str.strip()
    out["ls"] = (
        out["ls"].astype(str).str.strip()
        .str.replace(r"\.0+$", "", regex=True)
    )
    out["descripcion"] = out["descripcion"].astype(str).str.strip()
    out["nombre_cuenta"] = out["nombre_cuenta"].astype(str).str.strip()
    out["referencia"] = out["referencia"].astype(str).str.strip()
    out["tipo"] = out["tipo"].astype(str).str.upper().str.strip()

    out["movimiento"] = out["debe"] - out["haber"]

    print(f"[OK] mayor cargado para {cliente}: {len(out)} movimientos")
    return out


def filtrar_por_ls(
    df: pd.DataFrame, codigo_ls: str
) -> pd.DataFrame:
    """Returns rows matching the L/S code exactly."""
    if df is None or df.empty or "ls" not in df.columns:
        return pd.DataFrame()
    return df[
        df["ls"].astype(str).str.strip() == str(codigo_ls).strip()
    ].copy()


def filtrar_por_cuenta(
    df: pd.DataFrame, numero_cuenta: str
) -> pd.DataFrame:
    """Returns rows where numero_cuenta starts with the given prefix."""
    if df is None or df.empty or "numero_cuenta" not in df.columns:
        return pd.DataFrame()
    return df[
        df["numero_cuenta"].astype(str)
        .str.startswith(str(numero_cuenta).strip())
    ].copy()


def buscar_movimientos(
    df: pd.DataFrame,
    texto: str = "",
    monto_min: float = 0.0,
    monto_max: float = 0.0,
) -> pd.DataFrame:
    """
    Searches ledger rows by description text and/or amount range.
    monto_max=0 means no upper limit.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    resultado = df.copy()

    if texto.strip():
        q = texto.strip().lower()
        mask_desc = resultado["descripcion"].str.lower().str.contains(
            q, na=False
        )
        mask_ref = resultado["referencia"].str.lower().str.contains(
            q, na=False
        )
        mask_cta = resultado["nombre_cuenta"].str.lower().str.contains(
            q, na=False
        )
        resultado = resultado[mask_desc | mask_ref | mask_cta]

    if monto_min > 0:
        resultado = resultado[
            resultado["debe"].abs().ge(monto_min)
            | resultado["haber"].abs().ge(monto_min)
        ]

    if monto_max > 0:
        resultado = resultado[
            resultado["debe"].abs().le(monto_max)
            | resultado["haber"].abs().le(monto_max)
        ]

    return resultado.reset_index(drop=True)


def resumen_mayor(df: pd.DataFrame) -> dict[str, Any]:
    """Returns a summary dict for dashboard display."""
    if df is None or df.empty:
        return {
            "total_movimientos": 0,
            "total_debe": 0.0,
            "total_haber": 0.0,
            "cuentas_distintas": 0,
            "fecha_min": None,
            "fecha_max": None,
        }
    return {
        "total_movimientos": len(df),
        "total_debe": float(df["debe"].sum()),
        "total_haber": float(df["haber"].sum()),
        "cuentas_distintas": int(df["numero_cuenta"].nunique()),
        "fecha_min": df["fecha"].min() if "fecha" in df else None,
        "fecha_max": df["fecha"].max() if "fecha" in df else None,
    }


def obtener_mayor_cliente(cliente: str) -> Optional[pd.DataFrame]:
    """Convenience wrapper used by Streamlit."""
    return leer_mayor(cliente)
