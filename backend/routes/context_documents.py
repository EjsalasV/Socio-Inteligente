from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from backend.auth import authorize_cliente_access, get_current_user
from backend.schemas import ApiResponse, UserContext
from backend.services.context_document_service import (
    delete_document,
    document_type_options,
    list_documents,
    reprocess_document,
    store_document,
)
from backend.utils.api_errors import raise_api_error


router = APIRouter(prefix="/api/context-documents", tags=["context-documents"])


@router.get("/types", response_model=ApiResponse)
def get_document_types(user: UserContext = Depends(get_current_user)) -> ApiResponse:
    return ApiResponse(data={"types": document_type_options()})


@router.get("/{cliente_id}", response_model=ApiResponse)
def get_documents(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    rows = list_documents(cliente_id)
    return ApiResponse(data={"documents": rows, "total": len(rows)})


@router.post("/{cliente_id}", response_model=ApiResponse)
async def upload_document(
    cliente_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    period: str = Form(""),
    document_role: str = Form("other"),
    cutoff_date: str = Form(""),
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    content = await file.read()
    try:
        row = store_document(
            cliente_id,
            filename=file.filename or "documento",
            content=content,
            document_type=document_type,
            period=period,
            uploaded_by=user.sub,
            document_role=document_role,
            cutoff_date=cutoff_date,
        )
    except ValueError as exc:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_CONTEXT_DOCUMENT",
            message=str(exc),
        )
    return ApiResponse(data={"document": row})


@router.delete("/{cliente_id}/{document_id}", response_model=ApiResponse)
def remove_document(
    cliente_id: str,
    document_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    removed = delete_document(cliente_id, document_id)
    if not removed:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="CONTEXT_DOCUMENT_NOT_FOUND",
            message="Documento no encontrado.",
        )
    return ApiResponse(data={"removed": True, "document_id": document_id})


@router.post("/{cliente_id}/{document_id}/reprocess", response_model=ApiResponse)
def reprocess_context_document(
    cliente_id: str,
    document_id: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    row = reprocess_document(cliente_id, document_id)
    if row is None:
        raise_api_error(status_code=status.HTTP_404_NOT_FOUND, code="CONTEXT_DOCUMENT_NOT_FOUND", message="Documento no encontrado.")
    return ApiResponse(data={"document": row})
