from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class WorkpapersFile(Base):
    """Modelo para archivos Excel de papeles de trabajo con versionamiento."""

    __tablename__ = "workpapers_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(String(255), nullable=False, index=True)
    area_code = Column(String(50), nullable=False)
    area_name = Column(String(255), nullable=False)

    # Archivo y versión
    filename = Column(String(255), nullable=False)
    file_version = Column(Integer, default=1)  # v1, v2, etc
    file_hash = Column(String(64), nullable=False)  # SHA256
    file_size = Column(Integer, nullable=False)  # bytes
    file_path = Column(String(512), nullable=False)  # /uploads/papeles-trabajo/[cliente]/[area]/v_actual/

    # Metadata
    uploaded_by = Column(String(255), nullable=False)  # usuario que subió
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Estado
    status = Column(String(50), default="pending_review")  # pending_review, approved, signed

    # Firmas (guardadas cuando usuario firma)
    junior_signed_at = Column(DateTime, nullable=True)
    junior_signed_by = Column(String(255), nullable=True)

    senior_signed_at = Column(DateTime, nullable=True)
    senior_signed_by = Column(String(255), nullable=True)

    socio_signed_at = Column(DateTime, nullable=True)
    socio_signed_by = Column(String(255), nullable=True)

    # Backup de versión anterior
    backup_path = Column(String(512), nullable=True)  # ruta a v_anterior

    # JSON de modificaciones
    modifications = Column(JSON, default=list)  # [{timestamp, user_role, field, old_value, new_value}, ...]

    # Datos parseados del Excel (para visualización en BD)
    parsed_data = Column(JSON, nullable=True)  # Tabla completa parseada

    def __repr__(self) -> str:
        return (
            f"<WorkpapersFile "
            f"cliente_id={self.cliente_id} "
            f"area={self.area_code} "
            f"v{self.file_version} "
            f"status={self.status}>"
        )
