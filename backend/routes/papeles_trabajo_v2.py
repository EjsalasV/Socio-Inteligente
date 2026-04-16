from __future__ import annotations

import hashlib
import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse

from backend.auth import get_current_user
from backend.models.workpapers_files import WorkpapersFile
from backend.repositories.workpapers_repository import WorkpapersRepository
from backend.schemas import ApiResponse, UserContext
from backend.services.excel_parser_service import ExcelParserService
from backend.utils.api_errors import raise_api_error
from backend.utils.database import get_session

router = APIRouter(prefix="/api/papeles-trabajo", tags=["papeles-trabajo-v2"])

# Directorio base para almacenamiento
UPLOADS_BASE = Path("uploads/papeles-trabajo")
UPLOADS_BASE.mkdir(parents=True, exist_ok=True)


def _calculate_hash(content: bytes) -> str:
    """Calcula SHA256 de contenido."""
    return hashlib.sha256(content).hexdigest()


def _get_file_path(cliente_id: str, area_code: str, version: str = "v_actual") -> Path:
    """Obtiene ruta para almacenar archivo."""
    path = UPLOADS_BASE / cliente_id / area_code / version
    path.mkdir(parents=True, exist_ok=True)
    return path


@router.get("/{cliente_id}/plantilla", response_class=FileResponse)
def get_plantilla(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
) -> FileResponse:
    """
    Descarga plantilla Excel vacía para rellenar papeles de trabajo.

    Returns:
        Archivo Excel con estructura y ejemplo
    """
    try:
        template_content = ExcelParserService.create_template_excel()
        return FileResponse(
            content=template_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"plantilla_papeles_trabajo_{cliente_id}.xlsx",
        )
    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="PLANTILLA_ERROR",
            message=f"Error generating template: {str(e)}",
        )


@router.post("/{cliente_id}/upload", response_model=ApiResponse)
async def upload_papeles_trabajo(
    cliente_id: str,
    area_code: str,
    area_name: str,
    file: UploadFile = File(...),
    user: UserContext = Depends(get_current_user),
    session=Depends(get_session),
) -> ApiResponse:
    """
    Sube archivo Excel, parsea y almacena.

    - Comprime automáticamente (ZIP)
    - Detecta duplicados por HASH
    - Mueve versión anterior a backup
    - Parsea datos a BD
    """
    try:
        # Leer contenido
        content = await file.read()
        if not content:
            raise_api_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="EMPTY_FILE",
                message="Archivo vacío",
            )

        # Calcular HASH
        file_hash = _calculate_hash(content)

        # Verificar si ya existe (duplicado)
        existing = WorkpapersRepository.get_latest_file(session, cliente_id, area_code)
        if existing and existing.file_hash == file_hash:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="DUPLICATE_FILE",
                message="Este archivo ya fue subido",
            )

        # Parsear Excel
        parsed = ExcelParserService.parse_excel(content)
        if parsed["errors"]:
            raise_api_error(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="PARSING_ERROR",
                message="Error parseando Excel",
                details=parsed["errors"],
            )

        # Comprimir archivo
        compressed_content = ExcelParserService.compress_file(content, filename=file.filename or "papeles.xlsx")

        # Mover versión anterior a backup
        backup_path = None
        if existing:
            old_file_path = Path(existing.file_path)
            if old_file_path.exists():
                backup_dir = _get_file_path(cliente_id, area_code, "v_anterior")
                backup_file = backup_dir / old_file_path.name
                old_file_path.rename(backup_file)
                backup_path = str(backup_file)

        # Guardar nuevo archivo en v_actual
        file_path = _get_file_path(cliente_id, area_code, "v_actual")
        new_filename = f"{area_code}_{file_hash[:8]}.zip"
        full_path = file_path / new_filename

        with open(full_path, "wb") as f:
            f.write(compressed_content)

        # Registrar en BD
        db_file = WorkpapersRepository.create_file(
            session,
            cliente_id=cliente_id,
            area_code=area_code,
            area_name=area_name,
            filename=new_filename,
            file_hash=file_hash,
            file_size=len(content),
            file_path=str(full_path),
            uploaded_by=user.sub,
            parsed_data=parsed.get("rows", []),
            backup_path=backup_path,
        )

        return ApiResponse(
            data={
                "file_id": db_file.id,
                "version": db_file.file_version,
                "parsed_rows": len(parsed.get("rows", [])),
                "summary": parsed.get("summary", {}),
                "status": "success",
            }
        )

    except Exception as e:
        if "raise_api_error" not in str(e):
            raise_api_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="UPLOAD_ERROR",
                message=f"Error uploading file: {str(e)}",
            )
        raise


@router.get("/{cliente_id}/files", response_model=ApiResponse)
def list_files(
    cliente_id: str,
    user: UserContext = Depends(get_current_user),
    session=Depends(get_session),
) -> ApiResponse:
    """Lista todos los archivos de papeles de trabajo por cliente."""
    try:
        files = WorkpapersRepository.list_files_by_cliente(session, cliente_id)

        files_data = []
        for f in files:
            signatures = WorkpapersRepository.get_file_signatures(session, f.id)
            files_data.append({
                "id": f.id,
                "area_code": f.area_code,
                "area_name": f.area_name,
                "version": f.file_version,
                "uploaded_by": f.uploaded_by,
                "uploaded_at": f.uploaded_at.isoformat(),
                "status": f.status,
                "signatures": signatures,
                "has_backup": f.backup_path is not None,
            })

        return ApiResponse(data={"files": files_data})
    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="LIST_ERROR",
            message=f"Error listing files: {str(e)}",
        )


@router.get("/{cliente_id}/{area_code}/respaldo", response_class=FileResponse)
def download_backup(
    cliente_id: str,
    area_code: str,
    user: UserContext = Depends(get_current_user),
    session=Depends(get_session),
) -> FileResponse:
    """Descarga versión anterior (respaldo) de papeles de trabajo."""
    try:
        # Obtener versión 1 (backup)
        file = WorkpapersRepository.get_file_by_version(session, cliente_id, area_code, 1)

        if not file or not file.backup_path:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="NO_BACKUP",
                message="No backup available",
            )

        backup_file = Path(file.backup_path)
        if not backup_file.exists():
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="BACKUP_NOT_FOUND",
                message="Backup file not found on disk",
            )

        return FileResponse(
            path=backup_file,
            media_type="application/zip",
            filename=f"respaldo_{area_code}.zip",
        )

    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="DOWNLOAD_ERROR",
            message=f"Error downloading backup: {str(e)}",
        )


@router.post("/{cliente_id}/{area_code}/{file_id}/sign", response_model=ApiResponse)
def sign_file(
    cliente_id: str,
    area_code: str,
    file_id: int,
    role: str,  # junior, senior, socio
    user: UserContext = Depends(get_current_user),
    session=Depends(get_session),
) -> ApiResponse:
    """Firma archivo (Junior, Senior o Socio)."""
    try:
        if role not in ["junior", "senior", "socio"]:
            raise_api_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="INVALID_ROLE",
                message="Role must be junior, senior, or socio",
            )

        WorkpapersRepository.sign_file(session, file_id, role, user.sub)

        signatures = WorkpapersRepository.get_file_signatures(session, file_id)

        return ApiResponse(
            data={
                "file_id": file_id,
                "signed_by": role,
                "signed_at": __import__("datetime").datetime.utcnow().isoformat(),
                "signatures": signatures,
            }
        )

    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="SIGN_ERROR",
            message=f"Error signing file: {str(e)}",
        )
