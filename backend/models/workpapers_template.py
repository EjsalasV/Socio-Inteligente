from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from datetime import datetime

from backend.models import Base

class WorkpapersTemplate(Base):
    """Plantilla de papeles de trabajo clasificados"""
    __tablename__ = "workpapers_templates"

    id = Column(Integer, primary_key=True)
    codigo = Column(String(10), unique=True, nullable=False)  # ej: 130.03
    numero = Column(String(5), nullable=False)  # ej: 03
    ls = Column(Integer, nullable=False)  # ej: 130 (línea de cuenta)
    nombre = Column(String(255), nullable=False)
    aseveracion = Column(String(50), nullable=False)  # EXISTENCIA, INTEGRIDAD, VALORACION, etc.
    importancia = Column(String(20), nullable=False)  # CRITICO, ALTO, MEDIO, BAJO
    obligatorio = Column(String(20), nullable=False)  # SÍ, NO, CONDICIONAL
    descripcion = Column(Text)  # POR QUÉ se realiza
    archivo_original = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ls', 'ls'),
        Index('idx_aseveracion', 'aseveracion'),
        Index('idx_importancia', 'importancia'),
        Index('idx_ls_importancia', 'ls', 'importancia'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "numero": self.numero,
            "ls": self.ls,
            "nombre": self.nombre,
            "aseveracion": self.aseveracion,
            "importancia": self.importancia,
            "obligatorio": self.obligatorio,
            "descripcion": self.descripcion,
            "archivo_original": self.archivo_original,
        }
