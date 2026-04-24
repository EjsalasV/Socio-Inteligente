from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_CLIENTES = ROOT / "data" / "clientes"
_DISK_CACHE_NAME = ".mayor_canonical.pkl"

# cache[cliente_id] = (signature, dataframe)
_MAYOR_CACHE: dict[str, tuple[str, pd.DataFrame]] = {}

try:
    # Reuse existing normalization helpers when available.
    from analysis.lector_mayor import _normalize_header as _legacy_normalize_header
    from analysis.lector_mayor import _to_numeric as _legacy_to_numeric
except Exception:  # pragma: no cover - defensive fallback
    _legacy_normalize_header = None
    _legacy_to_numeric = None


def _normalize_header(col: Any) -> str:
    if callable(_legacy_normalize_header):
        return _legacy_normalize_header(col)
    text = str(col or "").strip().lower()
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")


def _to_numeric(series: pd.Series) -> pd.Series:
    if callable(_legacy_to_numeric):
        return _legacy_to_numeric(series)
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _cliente_dir(cliente_id: str) -> Path:
    return DATA_CLIENTES / str(cliente_id or "").strip()


def resolve_mayor_path(cliente_id: str) -> Path | None:
    cdir = _cliente_dir(cliente_id)
    candidates = [cdir / "mayor.xlsx", cdir / "mayor.csv", cdir / "mayor.xls"]
    existing = [p for p in candidates if p.exists() and p.is_file() and p.stat().st_size > 0]
    if not existing:
        return None
    existing.sort(key=lambda p: p.stat().st_mtime_ns, reverse=True)
    return existing[0]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_signature(path: Path | None) -> str:
    if path is None or not path.exists():
        return "missing"
    stat = path.stat()
    content_hash = _sha256_file(path)
    return f"{path.name}:{int(stat.st_size)}:{int(stat.st_mtime_ns)}:{content_hash}"


def _cache_path(cliente_id: str) -> Path:
    return _cliente_dir(cliente_id) / _DISK_CACHE_NAME


def _read_source_dataframe(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        try:
            return pd.read_csv(path, encoding="utf-8-sig")
        except Exception:
            return pd.read_csv(path, encoding="latin-1")
    if suffix == ".xlsx":
        return pd.read_excel(path, sheet_name=0, engine="openpyxl")
    # .xls fallback (best-effort)
    return pd.read_excel(path, sheet_name=0)


def _resolve_col(columns: list[str], candidates: list[str]) -> str | None:
    for cand in candidates:
        if cand in columns:
            return cand
    return None


def _series_or_empty(df: pd.DataFrame, col: str | None) -> pd.Series:
    if col and col in df.columns:
        return df[col]
    return pd.Series([None] * len(df))


def _normalize_canonical(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(
            columns=[
                "fecha",
                "asiento_ref",
                "numero_cuenta",
                "nombre_cuenta",
                "ls",
                "descripcion",
                "referencia",
                "debe",
                "haber",
                "neto",
                "monto_abs",
                "row_hash",
            ]
        )

    work = df.copy()
    work = work.dropna(how="all").reset_index(drop=True)
    work.columns = [_normalize_header(c) for c in work.columns]
    cols = work.columns.tolist()

    fecha_col = _resolve_col(cols, ["fecha", "date", "fecha_mov", "fecha_asiento", "f_contable"])
    asiento_col = _resolve_col(cols, ["asiento_ref", "asiento", "nro_asiento", "numero_asiento", "id_asiento"])
    cuenta_col = _resolve_col(cols, ["numero_cuenta", "cuenta", "codigo", "cod_cuenta", "numero_de_cuenta"])
    nombre_col = _resolve_col(cols, ["nombre_cuenta", "nombre", "descripcion_cuenta"])
    ls_col = _resolve_col(cols, ["ls", "l_s", "linea_significancia"])
    descripcion_col = _resolve_col(cols, ["descripcion", "detalle", "concepto", "glosa"])
    referencia_col = _resolve_col(cols, ["referencia", "comprobante", "voucher", "numero_doc", "doc"])
    debe_col = _resolve_col(cols, ["debe", "debito", "debit"])
    haber_col = _resolve_col(cols, ["haber", "credito", "credit"])

    out = pd.DataFrame()
    fecha_raw = _series_or_empty(work, fecha_col)
    parsed = pd.to_datetime(fecha_raw, errors="coerce")
    if parsed.notna().sum() == 0:
        parsed = pd.to_datetime(fecha_raw, errors="coerce", dayfirst=True)
    out["fecha"] = parsed
    out["asiento_ref"] = _series_or_empty(work, asiento_col).astype(str).str.strip()
    out["numero_cuenta"] = _series_or_empty(work, cuenta_col).astype(str).str.strip()
    out["nombre_cuenta"] = _series_or_empty(work, nombre_col).astype(str).str.strip()
    out["ls"] = (
        _series_or_empty(work, ls_col)
        .astype(str)
        .str.strip()
        .str.replace(r"\.0+$", "", regex=True)
    )
    out["descripcion"] = _series_or_empty(work, descripcion_col).astype(str).str.strip()
    out["referencia"] = _series_or_empty(work, referencia_col).astype(str).str.strip()
    out["debe"] = _to_numeric(_series_or_empty(work, debe_col).fillna(0))
    out["haber"] = _to_numeric(_series_or_empty(work, haber_col).fillna(0))

    out["asiento_ref"] = out["asiento_ref"].replace({"nan": "", "None": ""})
    out["referencia"] = out["referencia"].replace({"nan": "", "None": ""})
    out["descripcion"] = out["descripcion"].replace({"nan": "", "None": ""})
    out["nombre_cuenta"] = out["nombre_cuenta"].replace({"nan": "", "None": ""})
    out["numero_cuenta"] = out["numero_cuenta"].replace({"nan": "", "None": ""})
    out["ls"] = out["ls"].replace({"nan": "", "None": ""})

    out["neto"] = out["debe"] - out["haber"]
    out["monto_abs"] = out[["debe", "haber", "neto"]].abs().max(axis=1)

    hash_base = (
        out["fecha"].fillna(pd.Timestamp(0)).astype(str)
        + "|"
        + out["asiento_ref"].astype(str)
        + "|"
        + out["numero_cuenta"].astype(str)
        + "|"
        + out["referencia"].astype(str)
        + "|"
        + out["debe"].round(4).astype(str)
        + "|"
        + out["haber"].round(4).astype(str)
        + "|"
        + out["descripcion"].astype(str)
    )
    out["row_hash"] = hash_base.apply(lambda x: hashlib.sha1(x.encode("utf-8")).hexdigest())

    return out


def _load_disk_cache(cliente_id: str, signature: str) -> pd.DataFrame | None:
    path = _cache_path(cliente_id)
    if signature == "missing" or not path.exists():
        return None
    try:
        payload = pd.read_pickle(path)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    if str(payload.get("signature") or "") != signature:
        return None
    df = payload.get("df")
    if not isinstance(df, pd.DataFrame):
        return None
    return df.copy()


def _save_disk_cache(cliente_id: str, signature: str, df: pd.DataFrame) -> None:
    if signature == "missing":
        return
    try:
        _cache_path(cliente_id).parent.mkdir(parents=True, exist_ok=True)
        pd.to_pickle({"signature": signature, "df": df}, _cache_path(cliente_id))
    except Exception:
        return


def load_mayor_canonical(cliente_id: str, *, force_refresh: bool = False) -> tuple[pd.DataFrame, dict[str, Any]]:
    path = resolve_mayor_path(cliente_id)
    signature = _file_signature(path)
    key = str(cliente_id).strip()

    if not force_refresh:
        cached = _MAYOR_CACHE.get(key)
        if cached and cached[0] == signature:
            df = cached[1].copy()
            return df, _metadata(cliente_id, path, signature, len(df), cache="memory")

        disk_df = _load_disk_cache(cliente_id, signature)
        if disk_df is not None:
            _MAYOR_CACHE[key] = (signature, disk_df.copy())
            return disk_df.copy(), _metadata(cliente_id, path, signature, len(disk_df), cache="disk")

    if path is None:
        empty = _normalize_canonical(pd.DataFrame())
        _MAYOR_CACHE[key] = (signature, empty.copy())
        return empty, _metadata(cliente_id, None, signature, 0, cache="none")

    source_df = _read_source_dataframe(path)
    canonical = _normalize_canonical(source_df)
    _MAYOR_CACHE[key] = (signature, canonical.copy())
    _save_disk_cache(cliente_id, signature, canonical)
    return canonical, _metadata(cliente_id, path, signature, len(canonical), cache="rebuilt")


def _metadata(
    cliente_id: str,
    path: Path | None,
    signature: str,
    rows: int,
    *,
    cache: str,
) -> dict[str, Any]:
    return {
        "cliente_id": str(cliente_id),
        "source_file": str(path.name) if path else "",
        "source_path": str(path) if path else "",
        "source_format": str(path.suffix.lower()) if path else "",
        "signature": signature,
        "rows": int(rows),
        "cache": cache,
    }


def mayor_dataframe_to_items(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    out = df.copy()
    if "fecha" in out.columns:
        out["fecha"] = pd.to_datetime(out["fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
        out["fecha"] = out["fecha"].fillna("")
    records = out.to_dict(orient="records")
    return [dict(item) for item in records]


def build_mayor_summary(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or df.empty:
        return {
            "total_movimientos": 0,
            "total_debe": 0.0,
            "total_haber": 0.0,
            "total_neto": 0.0,
            "cuentas_distintas": 0,
            "asientos_distintos": 0,
            "fecha_min": "",
            "fecha_max": "",
            "monto_promedio": 0.0,
        }

    fecha = pd.to_datetime(df.get("fecha"), errors="coerce")
    asientos = df.get("asiento_ref", pd.Series(dtype=str)).astype(str).str.strip()
    nonempty_asientos = asientos[asientos != ""]
    return {
        "total_movimientos": int(len(df)),
        "total_debe": float(df.get("debe", pd.Series(dtype=float)).sum()),
        "total_haber": float(df.get("haber", pd.Series(dtype=float)).sum()),
        "total_neto": float(df.get("neto", pd.Series(dtype=float)).sum()),
        "cuentas_distintas": int(df.get("numero_cuenta", pd.Series(dtype=str)).astype(str).nunique()),
        "asientos_distintos": int(nonempty_asientos.nunique()) if not nonempty_asientos.empty else 0,
        "fecha_min": fecha.min().strftime("%Y-%m-%d") if fecha.notna().any() else "",
        "fecha_max": fecha.max().strftime("%Y-%m-%d") if fecha.notna().any() else "",
        "monto_promedio": float(df.get("monto_abs", pd.Series(dtype=float)).mean() or 0.0),
    }


def filter_mayor_movements(
    df: pd.DataFrame,
    *,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    cuenta: str | None = None,
    ls: str | None = None,
    referencia: str | None = None,
    texto: str | None = None,
    monto_min: float | None = None,
    monto_max: float | None = None,
) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=list(df.columns) if isinstance(df, pd.DataFrame) else [])

    out = df.copy()

    if fecha_desde:
        dt_from = pd.to_datetime(fecha_desde, errors="coerce")
        if pd.notna(dt_from):
            out = out[pd.to_datetime(out["fecha"], errors="coerce") >= dt_from]

    if fecha_hasta:
        dt_to = pd.to_datetime(fecha_hasta, errors="coerce")
        if pd.notna(dt_to):
            out = out[pd.to_datetime(out["fecha"], errors="coerce") <= dt_to]

    if cuenta and str(cuenta).strip():
        prefix = str(cuenta).strip()
        out = out[out["numero_cuenta"].astype(str).str.startswith(prefix)]

    if ls and str(ls).strip():
        ls_q = str(ls).strip()
        out = out[out["ls"].astype(str).str.strip() == ls_q]

    if referencia and str(referencia).strip():
        ref_q = str(referencia).strip().lower()
        out = out[out["referencia"].astype(str).str.lower().str.contains(ref_q, na=False)]

    if texto and str(texto).strip():
        q = str(texto).strip().lower()
        text_mask = (
            out["descripcion"].astype(str).str.lower().str.contains(q, na=False)
            | out["referencia"].astype(str).str.lower().str.contains(q, na=False)
            | out["nombre_cuenta"].astype(str).str.lower().str.contains(q, na=False)
            | out["numero_cuenta"].astype(str).str.lower().str.contains(q, na=False)
            | out["asiento_ref"].astype(str).str.lower().str.contains(q, na=False)
        )
        out = out[text_mask]

    if monto_min is not None and float(monto_min) > 0:
        out = out[out["monto_abs"] >= float(monto_min)]

    if monto_max is not None and float(monto_max) > 0:
        out = out[out["monto_abs"] <= float(monto_max)]

    out = out.sort_values(by=["fecha", "asiento_ref", "numero_cuenta"], ascending=[False, True, True], na_position="last")
    return out.reset_index(drop=True)


def paginate_dataframe(df: pd.DataFrame, *, page: int, page_size: int) -> tuple[pd.DataFrame, int, int]:
    safe_page = max(1, int(page))
    safe_size = max(1, min(int(page_size), 500))
    total = int(len(df))
    total_pages = max(1, (total + safe_size - 1) // safe_size)
    start = (safe_page - 1) * safe_size
    end = start + safe_size
    return df.iloc[start:end].copy(), total, total_pages
