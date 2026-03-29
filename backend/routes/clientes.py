from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import delete_cliente, list_clientes, read_perfil
from backend.schemas import ApiResponse, ClienteSummary, UserContext

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("", response_model=ApiResponse)
def get_clientes(user: UserContext = Depends(get_current_user)) -> ApiResponse:
    out: list[dict] = []
    for cid in list_clientes():
        if "*" not in user.allowed_clientes and cid not in user.allowed_clientes:
            continue
        perfil = read_perfil(cid)
        nombre = str(perfil.get("cliente", {}).get("nombre_legal") or cid)
        sector = perfil.get("cliente", {}).get("sector")
        out.append(ClienteSummary(cliente_id=cid, nombre=nombre, sector=sector).model_dump())
    return ApiResponse(data=out)


@router.delete("/{cliente_id}", response_model=ApiResponse)
def remove_cliente(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    deleted = delete_cliente(cliente_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente no encontrado: {cliente_id}",
        )
    return ApiResponse(data={"cliente_id": cliente_id, "deleted": True})


@router.post("/{cliente_id}/upload/{kind}", response_model=ApiResponse)
async def upload_cliente_file(
    cliente_id: str,
    kind: str,
    file: UploadFile = File(...),
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)

    kind_norm = kind.strip().lower()
    if kind_norm not in {"tb", "trial_balance", "mayor", "libro_mayor"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo invalido. Usa tb|trial_balance|mayor|libro_mayor.",
        )

    raw_name = (file.filename or "").strip()
    if not raw_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo sin nombre.")

    ext = Path(raw_name).suffix.lower()
    if ext not in {".xlsx", ".xls", ".csv"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no soportado. Usa .xlsx, .xls o .csv.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo vacio.")

    try:
        if ext == ".csv":
            df = pd.read_csv(BytesIO(content))
        else:
            df = pd.read_excel(BytesIO(content))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo leer el archivo: {exc}",
        ) from exc

    target_name = "tb.xlsx" if kind_norm in {"tb", "trial_balance"} else "mayor.xlsx"
    target_dir = Path(__file__).resolve().parents[2] / "data" / "clientes" / cliente_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / target_name

    try:
        df.to_excel(target_path, index=False)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo guardar el archivo: {exc}",
        ) from exc

    return ApiResponse(
        data={
            "cliente_id": cliente_id,
            "kind": "trial_balance" if target_name == "tb.xlsx" else "libro_mayor",
            "original_name": raw_name,
            "stored_as": target_name,
            "rows": int(len(df)),
            "columns": list(df.columns),
        }
    )
