from __future__ import annotations

import io
import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from backend.auth import authorize_cliente_access, get_current_user
from backend.schemas import ApiResponse, UserContext
from backend.utils.api_errors import raise_api_error
from backend.utils.database import get_session
from backend.services.mayor_service import (
    build_mayor_summary,
    filter_mayor_movements,
    load_mayor_canonical,
    mayor_dataframe_to_items,
    paginate_dataframe,
)
from backend.services.mayor_knowledge_service import safe_sync_mayor_validations_to_knowledge
from backend.services.mayor_validations import run_mayor_validations

router = APIRouter(prefix="/api/mayor", tags=["mayor"])

CANONICAL_COLUMNS = [
    "fecha",
    "asiento_ref",
    "numero_cuenta",
    "nombre_cuenta",
    "ls",
    "descripcion",
    "referencia",
    "debe",
    "haber",
    "saldo",
    "neto",
    "monto_abs",
    "row_hash",
]


def _export_max_rows() -> int:
    raw = str(os.getenv("MAYOR_EXPORT_MAX_ROWS") or "100000").strip()
    try:
        parsed = int(raw)
    except Exception:
        parsed = 100000
    return max(1, min(parsed, 500000))


@router.get("/{cliente_id}/movimientos", response_model=ApiResponse)
def get_mayor_movimientos(
    cliente_id: str,
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
    cuenta: str | None = Query(None),
    ls: str | None = Query(None),
    referencia: str | None = Query(None),
    texto: str | None = Query(None),
    monto_min: float | None = Query(None, ge=0),
    monto_max: float | None = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)

    canonical, meta = load_mayor_canonical(cliente_id)
    filtered = filter_mayor_movements(
        canonical,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cuenta=cuenta,
        ls=ls,
        referencia=referencia,
        texto=texto,
        monto_min=monto_min,
        monto_max=monto_max,
    )
    page_df, total, total_pages = paginate_dataframe(filtered, page=page, page_size=page_size)

    return ApiResponse(
        data={
            "items": mayor_dataframe_to_items(page_df),
            "total": int(total),
            "page": int(page),
            "page_size": int(page_size),
            "total_pages": int(total_pages),
            "resumen_filtrado": build_mayor_summary(filtered),
            "source": meta,
        }
    )


@router.get("/{cliente_id}/resumen", response_model=ApiResponse)
def get_mayor_resumen(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    canonical, meta = load_mayor_canonical(cliente_id)
    return ApiResponse(
        data={
            "resumen": build_mayor_summary(canonical),
            "source": meta,
        }
    )


@router.get("/{cliente_id}/validaciones", response_model=ApiResponse)
def get_mayor_validaciones(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    canonical, meta = load_mayor_canonical(cliente_id)
    validations = run_mayor_validations(canonical)
    summary = build_mayor_summary(canonical)

    # Non-blocking integration to Knowledge Core.
    safe_sync_mayor_validations_to_knowledge(
        session,
        cliente_id=cliente_id,
        validations=validations,
        summary=summary,
        actor=user.display_name or user.sub,
    )

    return ApiResponse(
        data={
            "validaciones": validations,
            "source": meta,
        }
    )


@router.get("/{cliente_id}/export")
def get_mayor_export(
    cliente_id: str,
    format_value: str = Query("xlsx", alias="format"),
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
    cuenta: str | None = Query(None),
    ls: str | None = Query(None),
    referencia: str | None = Query(None),
    texto: str | None = Query(None),
    monto_min: float | None = Query(None, ge=0),
    monto_max: float | None = Query(None, ge=0),
    user: UserContext = Depends(get_current_user),
):
    authorize_cliente_access(cliente_id, user)

    export_format = str(format_value or "xlsx").strip().lower()
    if export_format not in {"csv", "xlsx"}:
        raise_api_error(
            code="INVALID_EXPORT_FORMAT",
            message="El parámetro format debe ser 'csv' o 'xlsx'.",
            details={"format": format_value},
        )

    canonical, _meta = load_mayor_canonical(cliente_id)
    filtered = filter_mayor_movements(
        canonical,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cuenta=cuenta,
        ls=ls,
        referencia=referencia,
        texto=texto,
        monto_min=monto_min,
        monto_max=monto_max,
    )

    max_rows = _export_max_rows()
    if len(filtered) > max_rows:
        raise_api_error(
            status_code=413,
            code="EXPORT_ROW_LIMIT_EXCEEDED",
            message=f"El resultado filtrado excede el límite de exportación ({max_rows} filas).",
            details={"total_rows": int(len(filtered)), "max_rows": int(max_rows)},
            action_hint="Refina los filtros para exportar menos filas.",
        )

    export_df = filtered.copy()
    for col in CANONICAL_COLUMNS:
        if col not in export_df.columns:
            export_df[col] = ""
    export_df = export_df[CANONICAL_COLUMNS]
    export_df["fecha"] = export_df["fecha"].astype(str).replace({"NaT": "", "nan": ""})

    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base_filename = f"mayor_{cliente_id}_{now}"

    if export_format == "csv":
        csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")
        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{base_filename}.csv"'},
        )

    summary = build_mayor_summary(filtered)
    summary_df = pd.DataFrame([summary])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="movimientos")
        summary_df.to_excel(writer, index=False, sheet_name="resumen_filtrado")
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{base_filename}.xlsx"'},
    )
