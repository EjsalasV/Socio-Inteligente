from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from backend.models.workpapers_files import WorkpapersFile


class WorkpapersRepository:
    """Repositorio para operaciones con papeles de trabajo."""

    @staticmethod
    def get_latest_file(session: Session, cliente_id: str, area_code: str) -> WorkpapersFile | None:
        """Obtiene la versión más reciente de un archivo para un cliente y área."""
        return (
            session.query(WorkpapersFile)
            .filter(
                and_(
                    WorkpapersFile.cliente_id == cliente_id,
                    WorkpapersFile.area_code == area_code,
                    WorkpapersFile.file_version
                    == session.query(WorkpapersFile.file_version)
                    .filter(
                        and_(
                            WorkpapersFile.cliente_id == cliente_id,
                            WorkpapersFile.area_code == area_code,
                        )
                    )
                    .order_by(desc(WorkpapersFile.file_version))
                    .limit(1)
                    .correlate(None),
                )
            )
            .first()
        )

    @staticmethod
    def get_file_by_version(
        session: Session, cliente_id: str, area_code: str, file_version: int
    ) -> WorkpapersFile | None:
        """Obtiene un archivo específico por versión."""
        return (
            session.query(WorkpapersFile)
            .filter(
                and_(
                    WorkpapersFile.cliente_id == cliente_id,
                    WorkpapersFile.area_code == area_code,
                    WorkpapersFile.file_version == file_version,
                )
            )
            .first()
        )

    @staticmethod
    def list_files_by_cliente(session: Session, cliente_id: str) -> list[WorkpapersFile]:
        """Lista todos los archivos de un cliente."""
        return (
            session.query(WorkpapersFile)
            .filter(WorkpapersFile.cliente_id == cliente_id)
            .order_by(WorkpapersFile.area_code, desc(WorkpapersFile.file_version))
            .all()
        )

    @staticmethod
    def create_file(
        session: Session,
        cliente_id: str,
        area_code: str,
        area_name: str,
        filename: str,
        file_hash: str,
        file_size: int,
        file_path: str,
        uploaded_by: str,
        parsed_data: dict[str, Any] | None = None,
        backup_path: str | None = None,
    ) -> WorkpapersFile:
        """Crea un nuevo archivo de papeles de trabajo."""
        # Obtener versión anterior si existe
        latest = WorkpapersRepository.get_latest_file(session, cliente_id, area_code)
        new_version = 1 if latest is None else latest.file_version + 1

        file = WorkpapersFile(
            cliente_id=cliente_id,
            area_code=area_code,
            area_name=area_name,
            filename=filename,
            file_version=new_version,
            file_hash=file_hash,
            file_size=file_size,
            file_path=file_path,
            uploaded_by=uploaded_by,
            parsed_data=parsed_data or {},
            backup_path=backup_path,
            status="pending_review",
        )
        session.add(file)
        session.commit()
        return file

    @staticmethod
    def add_modification(
        session: Session,
        file_id: int,
        user_role: str,
        field: str,
        old_value: Any,
        new_value: Any,
    ) -> None:
        """Registra una modificación en el archivo."""
        file = session.query(WorkpapersFile).get(file_id)
        if not file:
            return

        modification = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_role": user_role,
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
        }

        if file.modifications is None:
            file.modifications = []
        file.modifications.append(modification)
        session.commit()

    @staticmethod
    def sign_file(
        session: Session,
        file_id: int,
        role: str,  # junior, senior, socio
        signed_by: str,
    ) -> None:
        """Registra firma de un usuario."""
        file = session.query(WorkpapersFile).get(file_id)
        if not file:
            return

        now = datetime.utcnow()
        if role == "junior":
            file.junior_signed_at = now
            file.junior_signed_by = signed_by
        elif role == "senior":
            file.senior_signed_at = now
            file.senior_signed_by = signed_by
        elif role == "socio":
            file.socio_signed_at = now
            file.socio_signed_by = signed_by

        # Actualizar status si todos firman
        if file.junior_signed_at and file.senior_signed_at and file.socio_signed_at:
            file.status = "signed"

        session.commit()

    @staticmethod
    def get_file_signatures(session: Session, file_id: int) -> dict[str, Any]:
        """Obtiene estado de firmas de un archivo."""
        file = session.query(WorkpapersFile).get(file_id)
        if not file:
            return {}

        return {
            "junior": {
                "signed": file.junior_signed_at is not None,
                "signed_at": file.junior_signed_at,
                "signed_by": file.junior_signed_by,
            },
            "senior": {
                "signed": file.senior_signed_at is not None,
                "signed_at": file.senior_signed_at,
                "signed_by": file.senior_signed_by,
            },
            "socio": {
                "signed": file.socio_signed_at is not None,
                "signed_at": file.socio_signed_at,
                "signed_by": file.socio_signed_by,
            },
        }
