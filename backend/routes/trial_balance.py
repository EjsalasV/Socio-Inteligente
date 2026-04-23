"""
Endpoints para upload y lectura de Trial Balance y Libro Mayor
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse

from backend.auth import authorize_cliente_access, get_current_user
from backend.schemas import ApiResponse, UserContext
from backend.utils.api_errors import raise_api_error

router = APIRouter(prefix="/api/trial-balance", tags=["trial-balance"])

ROOT = Path(__file__).resolve().parents[2]
DATA_CLIENTES = ROOT / "data" / "clientes"

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}
MAX_FILE_SIZE_MB = 20


def _cliente_dir(cliente_id: str) -> Path:
    return DATA_CLIENTES / cliente_id


def _validate_file(file: UploadFile, kind: str) -> None:
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_FILE_TYPE",
            message=f"Tipo de archivo no permitido: {ext}. Use .xlsx, .xls o .csv",
        )


@router.post("/{cliente_id}/upload", response_model=ApiResponse)
async def upload_trial_balance(
    cliente_id: str,
    file: UploadFile = File(...),
    kind: str = "tb",
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Subir Trial Balance (kind=tb) o Libro Mayor (kind=mayor) para un cliente.
    El archivo se guarda en data/clientes/{cliente_id}/tb.xlsx o mayor.xlsx
    """
    authorize_cliente_access(cliente_id, user)

    if kind not in {"tb", "mayor"}:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_KIND",
            message="El parametro kind debe ser 'tb' o 'mayor'",
        )

    _validate_file(file, kind)

    # Leer contenido del archivo
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="FILE_TOO_LARGE",
            message=f"El archivo excede el limite de {MAX_FILE_SIZE_MB}MB",
        )

    # Crear directorio del cliente si no existe
    cliente_dir = _cliente_dir(cliente_id)
    cliente_dir.mkdir(parents=True, exist_ok=True)

    # Guardar siempre como .xlsx o .csv segun extension original
    original_ext = Path(file.filename or "archivo.xlsx").suffix.lower()
    # Normalizar: siempre guardar como tb.xlsx o mayor.xlsx para compatibilidad
    target_filename = f"{kind}.xlsx" if original_ext in {".xlsx", ".xls"} else f"{kind}.csv"
    target_path = cliente_dir / target_filename

    try:
        with open(target_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="FILE_SAVE_ERROR",
            message=f"Error al guardar el archivo: {str(e)}",
        )

    return ApiResponse(
        data={
            "stored_as": target_filename,
            "original_name": file.filename or target_filename,
            "size_bytes": len(content),
            "kind": kind,
            "cliente_id": cliente_id,
        }
    )


@router.get("/{cliente_id}/diagnostico", response_model=ApiResponse)
def get_tb_diagnostico(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Diagnóstico del TB cargado: columnas detectadas, filas, stage
    """
    authorize_cliente_access(cliente_id, user)
    try:
        from analysis.lector_tb import obtener_diagnostico_tb
        diag = obtener_diagnostico_tb(cliente_id)
        return ApiResponse(data=diag)
    except Exception as e:
        return ApiResponse(data={"error": str(e), "cliente_id": cliente_id})


@router.get("/{cliente_id}/status", response_model=ApiResponse)
def get_tb_status(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Verificar si el cliente tiene TB y Mayor cargados
    """
    authorize_cliente_access(cliente_id, user)

    cliente_dir = _cliente_dir(cliente_id)
    tb_xlsx_path = cliente_dir / "tb.xlsx"
    tb_csv_path = cliente_dir / "tb.csv"
    mayor_xlsx_path = cliente_dir / "mayor.xlsx"
    mayor_csv_path = cliente_dir / "mayor.csv"

    tb_path = tb_xlsx_path if tb_xlsx_path.exists() else tb_csv_path
    mayor_path = mayor_xlsx_path if mayor_xlsx_path.exists() else mayor_csv_path

    has_tb = tb_path.exists() and tb_path.stat().st_size > 0
    has_mayor = mayor_path.exists() and mayor_path.stat().st_size > 0

    return ApiResponse(
        data={
            "cliente_id": cliente_id,
            "has_tb": has_tb,
            "has_mayor": has_mayor,
            "tb_size_bytes": tb_path.stat().st_size if has_tb else 0,
            "mayor_size_bytes": mayor_path.stat().st_size if has_mayor else 0,
        }
    )
