from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd


def _safe_records(df: pd.DataFrame, limit: int = 20) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    out = df.head(max(1, limit)).copy()
    if "fecha" in out.columns:
        out["fecha"] = pd.to_datetime(out["fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
        out["fecha"] = out["fecha"].fillna("")
    return out.to_dict(orient="records")


def _asiento_key(df: pd.DataFrame) -> pd.Series:
    as_ref = df.get("asiento_ref", pd.Series(dtype=str)).astype(str).str.strip()
    ref = df.get("referencia", pd.Series(dtype=str)).astype(str).str.strip()
    key = as_ref.copy()
    key[key == ""] = ref[key == ""]
    return key


def _validate_asientos_descuadrados(df: pd.DataFrame, tolerance: float = 0.01) -> dict[str, Any]:
    if df is None or df.empty:
        return {"count_asientos": 0, "count_movimientos": 0, "items": []}

    work = df.copy()
    work["asiento_key"] = _asiento_key(work)
    work = work[work["asiento_key"] != ""]
    if work.empty:
        return {"count_asientos": 0, "count_movimientos": 0, "items": []}

    grouped = (
        work.groupby("asiento_key", dropna=False)
        .agg(
            movimientos=("row_hash", "count"),
            total_debe=("debe", "sum"),
            total_haber=("haber", "sum"),
            total_neto=("neto", "sum"),
        )
        .reset_index()
    )
    grouped["descuadre_abs"] = (grouped["total_neto"]).abs()
    findings = grouped[grouped["descuadre_abs"] > float(tolerance)].sort_values("descuadre_abs", ascending=False)
    count_mov = int(work[work["asiento_key"].isin(findings["asiento_key"].tolist())].shape[0]) if not findings.empty else 0
    return {
        "count_asientos": int(len(findings)),
        "count_movimientos": count_mov,
        "items": findings.head(50).to_dict(orient="records"),
    }


def _validate_duplicados(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or df.empty:
        return {"grupos": 0, "movimientos": 0, "items": []}

    dups = df[df["row_hash"].duplicated(keep=False)].copy()
    if dups.empty:
        return {"grupos": 0, "movimientos": 0, "items": []}

    grouped = (
        dups.groupby("row_hash", dropna=False)
        .agg(
            repeticiones=("row_hash", "count"),
            asiento_ref=("asiento_ref", "first"),
            referencia=("referencia", "first"),
            numero_cuenta=("numero_cuenta", "first"),
            fecha=("fecha", "first"),
            monto_abs=("monto_abs", "first"),
        )
        .reset_index()
        .sort_values("repeticiones", ascending=False)
    )

    return {
        "grupos": int(len(grouped)),
        "movimientos": int(len(dups)),
        "items": _safe_records(grouped, limit=50),
    }


def _validate_sin_referencia(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or df.empty:
        return {"count": 0, "items": []}
    missing = df[df["referencia"].astype(str).str.strip() == ""].copy()
    return {"count": int(len(missing)), "items": _safe_records(missing, limit=50)}


def _validate_montos_altos(df: pd.DataFrame, *, percentile: float = 0.99) -> dict[str, Any]:
    if df is None or df.empty:
        return {"threshold": 0.0, "count": 0, "items": []}
    p = min(0.999, max(0.5, float(percentile)))
    threshold = float(df["monto_abs"].quantile(p)) if len(df) > 1 else float(df["monto_abs"].max())
    high = df[df["monto_abs"] >= threshold].sort_values("monto_abs", ascending=False)
    return {"threshold": threshold, "count": int(len(high)), "items": _safe_records(high, limit=50)}


def _validate_movimientos_cerca_cierre(df: pd.DataFrame, *, dias: int = 5) -> dict[str, Any]:
    if df is None or df.empty:
        return {"fecha_cierre": "", "dias": int(dias), "count": 0, "items": []}
    work = df.copy()
    work["fecha"] = pd.to_datetime(work["fecha"], errors="coerce")
    valid = work[work["fecha"].notna()].copy()
    if valid.empty:
        return {"fecha_cierre": "", "dias": int(dias), "count": 0, "items": []}
    fecha_cierre = valid["fecha"].max()
    cutoff = fecha_cierre - pd.Timedelta(days=max(0, int(dias)))
    p90 = float(valid["monto_abs"].quantile(0.90)) if len(valid) > 1 else float(valid["monto_abs"].max())
    near = valid[(valid["fecha"] >= cutoff) & (valid["monto_abs"] >= p90)].sort_values("monto_abs", ascending=False)
    return {
        "fecha_cierre": fecha_cierre.strftime("%Y-%m-%d"),
        "dias": int(dias),
        "count": int(len(near)),
        "items": _safe_records(near, limit=50),
    }


def run_mayor_validations(
    df: pd.DataFrame,
    *,
    asiento_tolerance: float = 0.01,
    monto_alto_percentile: float = 0.99,
    dias_cierre: int = 5,
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "asientos_descuadrados": _validate_asientos_descuadrados(df, tolerance=asiento_tolerance),
        "duplicados": _validate_duplicados(df),
        "movimientos_sin_referencia": _validate_sin_referencia(df),
        "montos_altos": _validate_montos_altos(df, percentile=monto_alto_percentile),
        "movimientos_cerca_cierre": _validate_movimientos_cerca_cierre(df, dias=dias_cierre),
    }

