"""
Modelo para Clientes - memoria persistente del sistema
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Client(Base):
    """
    Tabla de clientes - almacena información persistente de cada cliente
    """
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(50), unique=True, nullable=False, index=True)  # bustamante_fabara_ip_cl
    nombre = Column(String(255), nullable=False)
    ruc = Column(String(20), nullable=True)
    sector = Column(String(100), nullable=True)
    tipo_entidad = Column(String(50), nullable=True)

    # Contacto
    contacto_nombre = Column(String(100), nullable=True)
    contacto_email = Column(String(100), nullable=True)
    contacto_telefono = Column(String(20), nullable=True)

    # Auditoría config
    moneda = Column(String(10), default="COP")
    materialidad_general = Column(Numeric(15, 2), nullable=True)
    materialidad_procedimiento = Column(Numeric(15, 2), nullable=True)

    # Período actual
    periodo_actual = Column(String(10), nullable=True)  # "2025" o "2025-12"
    fecha_cierre = Column(Date, nullable=True)
    estado = Column(String(20), default="ACTIVO")  # ACTIVO, EN_AUDITORÍA, FINALIZADO, ARCHIVADO

    # Trazabilidad
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "nombre": self.nombre,
            "ruc": self.ruc,
            "sector": self.sector,
            "tipo_entidad": self.tipo_entidad,
            "contacto_nombre": self.contacto_nombre,
            "contacto_email": self.contacto_email,
            "contacto_telefono": self.contacto_telefono,
            "moneda": self.moneda,
            "materialidad_general": str(self.materialidad_general) if self.materialidad_general else None,
            "materialidad_procedimiento": str(self.materialidad_procedimiento) if self.materialidad_procedimiento else None,
            "periodo_actual": self.periodo_actual,
            "fecha_cierre": self.fecha_cierre.isoformat() if self.fecha_cierre else None,
            "estado": self.estado,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }
