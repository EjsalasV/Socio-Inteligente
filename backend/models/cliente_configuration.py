"""
Modelo para Configuración de Cliente - Respuestas a preguntas dinámicas por industria
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.models import Base


class ClienteConfiguration(Base):
    """
    Tabla de configuración de cliente - almacena respuestas a preguntas dinámicas
    """
    __tablename__ = "cliente_configurations"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)

    # Tipo de entidad (debe coincidir con client.tipo_entidad)
    tipo_entidad = Column(String(50), nullable=False)  # BANCO, RETAIL, SERVICIOS, etc

    # Respuestas a preguntas en formato JSON
    # Ej: {"rango_vencimiento": "30", "clasificacion_cartera": "A/B/C/D/E", ...}
    respuestas = Column(JSON, nullable=True)

    # Trazabilidad
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), nullable=True)

    # Relación
    client = relationship("Client", back_populates="configuraciones")

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "tipo_entidad": self.tipo_entidad,
            "respuestas": self.respuestas or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by": self.updated_by,
        }
