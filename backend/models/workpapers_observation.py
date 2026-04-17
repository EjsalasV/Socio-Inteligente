from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.models import Base

class WorkpapersObservation(Base):
    """Observaciones de papeles de trabajo (Junior, Senior, Socio)"""
    __tablename__ = "workpapers_observations"

    id = Column(Integer, primary_key=True)
    audit_id = Column(Integer, ForeignKey("audits.id", ondelete="CASCADE"), nullable=True)  # Vinculación a auditoría
    file_id = Column(Integer, ForeignKey("workpapers_files.id", ondelete="CASCADE"), nullable=True)  # FK para V2 (upload)
    codigo_papel = Column(String(10), nullable=False)  # ej: 130.03

    # OBSERVACIÓN JUNIOR
    junior_observation = Column(Text)  # Lo que encontró
    junior_by = Column(String(100))  # Usuario
    junior_at = Column(DateTime)  # Cuándo escribió
    junior_status = Column(String(20), default="PENDIENTE")

    # REVISIÓN SENIOR
    senior_review = Column(String(50))  # APROBADO, RECHAZADO, PENDIENTE_ACLARACION, NO_APLICA
    senior_comment = Column(Text)  # Por qué rechaza/modifica
    senior_by = Column(String(100))
    senior_at = Column(DateTime)

    # REVISIÓN SOCIO
    socio_review = Column(String(50))  # FINALIZADO, REVISAR, NO_APLICA
    socio_comment = Column(Text)  # Faltó esto, resuelto aquí, etc.
    socio_by = Column(String(100))
    socio_at = Column(DateTime)

    # OBSERVACIÓN FINAL APROBADA (para reportes)
    # Esta es la observación que entra en CARTA DE CONTROL
    observacion_final = Column(Text)  # Observación final aprobada por Socio
    efecto_financiero = Column(String(50))  # SIN_EFECTO, CON_EFECTO, AJUSTE_REQUERIDO
    impacto = Column(Text)  # Descripción del impacto en EE.FF.
    accion_recomendada = Column(Text)  # Acción recomendada

    # ESTADO FINAL
    status = Column(String(50), default="PENDIENTE")  # PENDIENTE, APROBADO, RECHAZADO, NO_APLICA, FINALIZADO

    # TRAZABILIDAD
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    history = relationship("WorkpapersObservationHistory", back_populates="observation", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_audit_id', 'audit_id'),
        Index('idx_file_id', 'file_id'),
        Index('idx_codigo_papel', 'codigo_papel'),
        Index('idx_status', 'status'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "audit_id": self.audit_id,
            "file_id": self.file_id,
            "codigo_papel": self.codigo_papel,
            "junior": {
                "observation": self.junior_observation,
                "by": self.junior_by,
                "at": self.junior_at.isoformat() if self.junior_at else None,
                "status": self.junior_status,
            },
            "senior": {
                "review": self.senior_review,
                "comment": self.senior_comment,
                "by": self.senior_by,
                "at": self.senior_at.isoformat() if self.senior_at else None,
            },
            "socio": {
                "review": self.socio_review,
                "comment": self.socio_comment,
                "by": self.socio_by,
                "at": self.socio_at.isoformat() if self.socio_at else None,
            },
            "status": self.status,
        }


class WorkpapersObservationHistory(Base):
    """Historial de cambios en observaciones"""
    __tablename__ = "workpapers_observation_history"

    id = Column(Integer, primary_key=True)
    observation_id = Column(Integer, ForeignKey("workpapers_observations.id", ondelete="CASCADE"), nullable=False)
    rol = Column(String(20), nullable=False)  # junior, senior, socio
    accion = Column(String(100), nullable=False)  # escribio, aprobó, rechazó, comentó, finalizó
    contenido_anterior = Column(Text)
    contenido_nuevo = Column(Text)
    usuario = Column(String(100), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)

    # Relación
    observation = relationship("WorkpapersObservation", back_populates="history")

    __table_args__ = (
        Index('idx_observation_id', 'observation_id'),
        Index('idx_rol_accion', 'rol', 'accion'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "observation_id": self.observation_id,
            "rol": self.rol,
            "accion": self.accion,
            "contenido_anterior": self.contenido_anterior,
            "contenido_nuevo": self.contenido_nuevo,
            "usuario": self.usuario,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
        }
