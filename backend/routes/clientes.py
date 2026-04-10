from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse

from backend.auth import authorize_cliente_access, get_current_user
from backend.middleware.rate_limit import limiter, LIMITS
from backend.repositories.file_repository import create_cliente, delete_cliente, list_clientes, list_documentos, read_hallazgos, read_perfil
from backend.repositories.identity_repository import store as identity_store
from backend.schemas import ApiResponse, ClienteCreateRequest, ClienteDocumento, ClienteSummary, UserContext
from backend.services.document_ingest_service import ingest_document_for_rag
from backend.services.rag_cache_service import invalidate_rag_cache_for_cliente
from backend.services.realtime_collab_service import hub

router = APIRouter(prefix="/clientes", tags=["clientes"])

# Validar formato de cliente_id para evitar path traversal
_CLIENTE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")

def _validate_cliente_id(cliente_id: str) -> None:
    """Validar cliente_id contra path traversal."""
    if not cliente_id or not _CLIENTE_ID_REGEX.match(cliente_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cliente_id debe contener solo letras, números, guiones y guiones bajos.",
        )


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


@router.post("", response_model=ApiResponse)
def post_cliente(payload: ClienteCreateRequest, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    if user.role.lower() not in {"admin", "manager", "socio"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo perfiles administradores pueden crear clientes.",
        )
    nombre = payload.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="nombre es obligatorio")

    try:
        created = create_cliente(
            cliente_id=(payload.cliente_id or "").strip(),
            nombre=nombre,
            sector=(payload.sector or "").strip() or None,
        )
    except FileExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    # Multiusuario: el creador obtiene acceso inmediato al cliente nuevo (si no usa wildcard).
    if user.user_id and "*" not in user.allowed_clientes:
        try:
            assigned = identity_store.get_user_clientes(user.user_id)
            if created.get("cliente_id") and created["cliente_id"] not in assigned:
                identity_store.set_user_clientes(user.user_id, [*assigned, str(created["cliente_id"])])
        except Exception:
            # No bloqueamos la creación por fallos de asignación secundaria.
            pass

    return ApiResponse(data=created)


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
@limiter.limit(LIMITS["uploads"])  # 3 uploads por minuto por IP
async def upload_cliente_file(
    request: Request,
    cliente_id: str,
    kind: str,
    file: UploadFile = File(...),
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    # Validar cliente_id format antes de usar en path
    _validate_cliente_id(cliente_id)
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

    # Validar tamaño ANTES de leer completo
    MAX_FILE_SIZE_MB = 50
    if file.size and file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo excede límite de {MAX_FILE_SIZE_MB}MB.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo vacio.")
    
    # Double-check tamaño real (en caso que file.size sea None)
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo excede límite de {MAX_FILE_SIZE_MB}MB.",
        )

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

    event_name = "tb_uploaded" if target_name == "tb.xlsx" else "mayor_uploaded"
    hub.publish_event_sync(
        cliente_id=cliente_id,
        event_name=event_name,
        actor=user.display_name or user.sub,
        payload={"rows": int(len(df)), "filename": raw_name},
    )

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


@router.get("/{cliente_id}/documentos", response_model=ApiResponse)
def get_cliente_documentos(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    docs = [ClienteDocumento(**doc).model_dump() for doc in list_documentos(cliente_id)]
    return ApiResponse(data=docs)


@router.post("/{cliente_id}/documentos/upload", response_model=ApiResponse)
async def upload_cliente_documento(
    cliente_id: str,
    file: UploadFile = File(...),
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    _validate_cliente_id(cliente_id)
    authorize_cliente_access(cliente_id, user)

    raw_name = (file.filename or "").strip()
    if not raw_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo sin nombre.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo vacio.")

    docs_dir = Path(__file__).resolve().parents[2] / "data" / "clientes" / cliente_id / "documentos"
    docs_dir.mkdir(parents=True, exist_ok=True)
    target = docs_dir / raw_name
    target.write_bytes(content)
    ingestion: dict[str, object] = {"indexed": False, "text_chars": 0}
    try:
        ingestion = ingest_document_for_rag(cliente_id, target)
    except Exception:
        ingestion = {"indexed": False, "text_chars": 0}
    cache_invalidated = invalidate_rag_cache_for_cliente(cliente_id)

    docs = [ClienteDocumento(**doc).model_dump() for doc in list_documentos(cliente_id)]
    return ApiResponse(
        data={
            "uploaded": True,
            "documento": raw_name,
            "documentos": docs,
            "ingestion": ingestion,
            "rag_cache_invalidated": int(cache_invalidated),
        }
    )


@router.get("/{cliente_id}/hallazgos", response_model=ApiResponse)
def get_cliente_hallazgos(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    raw = read_hallazgos(cliente_id)
    items: list[dict[str, str]] = []
    current_title = ""
    current_body: list[str] = []

    for line in raw.splitlines():
        if line.startswith("## "):
            if current_title or current_body:
                items.append({"title": current_title or "Hallazgo", "body": "\n".join(current_body).strip()})
            current_title = line.replace("## ", "", 1).strip()
            current_body = []
        else:
            current_body.append(line)
    if current_title or current_body:
        items.append({"title": current_title or "Hallazgo", "body": "\n".join(current_body).strip()})

    items = [x for x in items if x.get("title") or x.get("body")]
    return ApiResponse(data=items[-20:])


@router.get("/{cliente_id}/documentos/file")
def get_cliente_documento_file(
    cliente_id: str,
    name: str = Query(...),
    user: UserContext = Depends(get_current_user),
) -> FileResponse:
    authorize_cliente_access(cliente_id, user)
    base = Path(__file__).resolve().parents[2] / "data" / "clientes" / cliente_id
    safe_name = Path(name).name
    candidates = [base / "documentos" / safe_name, base / safe_name]
    for path in candidates:
        if path.exists() and path.is_file():
            return FileResponse(path=path.resolve(), filename=safe_name)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
