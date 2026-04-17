"""
Modelo para Auditorías - asociadas a clientes, una por período
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Audit(Base):
    """
    Tabla de auditorías - una auditoría por cliente-período
    """
    __tablename__ = "audits"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    codigo_auditoria = Column(String(50), unique=True, nullable=False, index=True)  # BUSTAMANTE_2025
    periodo = Column(String(10), nullable=False, index=True)  # "2025"

    # Equipo de auditoría
    socio_asignado = Column(String(100), nullable=True)
    senior_asignado = Column(String(100), nullable=True)
    semi_asignados = Column(Text, nullable=True)  # JSON array
    junior_asignados = Column(Text, nullable=True)  # JSON array

    # Estado
    estado = Column(String(20), default="PLANEACIÓN", index=True)  # PLANEACIÓN, EJECUCIÓN, REPORTE, FINALIZADO
    fecha_inicio = Column(Date, nullable=True)
    fecha_fin = Column(Date, nullable=True)
    fecha_emision = Column(Date, nullable=True)

    # Resultados
    hallazgos_total = Column(Integer, default=0)
    hallazgos_críticos = Column(Integer, default=0)
    hallazgos_observados = Column(Integer, default=0)

    # Trazabilidad
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "codigo_auditoria": self.codigo_auditoria,
            "periodo": self.periodo,
            "socio_asignado": self.socio_asignado,
            "senior_asignado": self.senior_asignado,
            "semi_asignados": self.semi_asignados,
            "junior_asignados": self.junior_asignados,
            "estado": self.estado,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_fin": self.fecha_fin.isoformat() if self.fecha_fin else None,
            "fecha_emision": self.fecha_emision.isoformat() if self.fecha_emision else None,
            "hallazgos_total": self.hallazgos_total,
            "hallazgos_críticos": self.hallazgos_críticos,
            "hallazgos_observados": self.hallazgos_observados,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
