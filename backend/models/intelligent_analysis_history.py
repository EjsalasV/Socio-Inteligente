"""
Modelo para histórico de análisis inteligentes
Guarda cada análisis realizado para RAG (memoria del analizador)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from backend.models import Base


class IntelligentAnalysisHistory(Base):
    """
    Tabla de histórico de análisis inteligentes
    Guarda cada análisis con sus hallazgos para no repetir
    """
    __tablename__ = "intelligent_analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(String(100), nullable=False, index=True)

    # Análisis detalles
    hallazgos = Column(JSON, nullable=False)  # Lista de hallazgos detectados
    resumen = Column(Text, nullable=True)  # Resumen ejecutivo
    observaciones_sector = Column(Text, nullable=True)  # Notas del sector

    # Trazabilidad
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Para RAG: guardar versión anterior para comparar
    version = Column(Integer, default=1)  # 1, 2, 3... para tracking de cambios

    def __repr__(self):
        return f"<IntelligentAnalysisHistory(cliente_id={self.cliente_id}, version={self.version}, date={self.created_at})>"
