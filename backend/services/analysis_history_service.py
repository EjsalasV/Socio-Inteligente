"""
Servicio para manejar histórico de análisis y RAG
Guarda análisis anteriores y los recupera para evitar repeticiones
"""

import json
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.intelligent_analysis_history import IntelligentAnalysisHistory

LOGGER = logging.getLogger("socio_ai.analysis_history")


class AnalysisHistoryService:
    """Servicio para guardar y recuperar histórico de análisis"""

    @staticmethod
    def save_analysis(
        session: Session,
        cliente_id: str,
        hallazgos: list,
        resumen: str,
        observaciones_sector: str,
    ) -> IntelligentAnalysisHistory:
        """
        Guarda un análisis en el histórico

        Args:
            session: Sesión SQLAlchemy
            cliente_id: ID del cliente
            hallazgos: Lista de hallazgos detectados
            resumen: Resumen del análisis
            observaciones_sector: Observaciones del sector

        Returns:
            Registro guardado
        """
        try:
            # Contar versión actual para este cliente
            latest = session.query(IntelligentAnalysisHistory).filter_by(
                cliente_id=cliente_id
            ).order_by(IntelligentAnalysisHistory.version.desc()).first()

            version = (latest.version + 1) if latest else 1

            record = IntelligentAnalysisHistory(
                cliente_id=cliente_id,
                hallazgos=hallazgos,
                resumen=resumen,
                observaciones_sector=observaciones_sector,
                version=version,
            )

            session.add(record)
            session.commit()

            LOGGER.info(f"✅ Análisis guardado para {cliente_id} (v{version}, {len(hallazgos)} hallazgos)")
            return record

        except Exception as e:
            LOGGER.error(f"❌ Error guardando análisis para {cliente_id}: {e}")
            session.rollback()
            raise

    @staticmethod
    def get_previous_analyses(
        session: Session,
        cliente_id: str,
        limit: int = 3,
    ) -> list[IntelligentAnalysisHistory]:
        """
        Recupera análisis anteriores de un cliente

        Args:
            session: Sesión SQLAlchemy
            cliente_id: ID del cliente
            limit: Cuántos análisis anteriores recuperar

        Returns:
            Lista de análisis anteriores (ordenados por fecha desc)
        """
        try:
            records = session.query(IntelligentAnalysisHistory).filter_by(
                cliente_id=cliente_id
            ).order_by(
                IntelligentAnalysisHistory.created_at.desc()
            ).limit(limit).all()

            return records

        except Exception as e:
            LOGGER.error(f"❌ Error recuperando análisis previos para {cliente_id}: {e}")
            return []

    @staticmethod
    def build_rag_context(
        session: Session,
        cliente_id: str,
    ) -> str:
        """
        Construye contexto RAG con análisis anteriores
        Se pasa al prompt para evitar repeticiones

        Args:
            session: Sesión SQLAlchemy
            cliente_id: ID del cliente

        Returns:
            Texto con contexto de análisis anteriores (vacío si no hay)
        """
        previous = AnalysisHistoryService.get_previous_analyses(session, cliente_id, limit=3)

        if not previous:
            LOGGER.debug(f"📋 No hay análisis previos para {cliente_id}")
            return ""

        # Construir contexto con hallazgos anteriores
        context = "\n\n⚠️ PREVIOUS FINDINGS (avoid repeating these):\n"

        for i, analysis in enumerate(previous, 1):
            context += f"\nAnalysis v{analysis.version} ({analysis.created_at.strftime('%Y-%m-%d %H:%M')}):\n"

            # Agregar hallazgos anteriores
            if analysis.hallazgos:
                try:
                    hallazgos = analysis.hallazgos if isinstance(analysis.hallazgos, list) else json.loads(analysis.hallazgos)
                    for h in hallazgos:
                        cuenta = h.get('cuenta_afectada', 'N/A')
                        desc = h.get('descripcion', 'N/A')[:100]  # Primeros 100 chars
                        context += f"  - [{h.get('id', 'H000')}] {cuenta}: {desc}\n"
                except:
                    pass

        context += "\n📌 IDENTIFY NEW FINDINGS not listed above:\n"
        LOGGER.debug(f"📋 RAG context construido: {len(context)} caracteres")

        return context

    @staticmethod
    def get_analysis_history(
        session: Session,
        cliente_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Obtiene histórico formateado para API

        Args:
            session: Sesión SQLAlchemy
            cliente_id: ID del cliente
            limit: Máximo de registros

        Returns:
            Lista de análisis formateados
        """
        records = session.query(IntelligentAnalysisHistory).filter_by(
            cliente_id=cliente_id
        ).order_by(
            IntelligentAnalysisHistory.created_at.desc()
        ).limit(limit).all()

        return [
            {
                "id": r.id,
                "version": r.version,
                "fecha": r.created_at.isoformat(),
                "total_hallazgos": len(r.hallazgos) if r.hallazgos else 0,
                "resumen": r.resumen[:200] if r.resumen else "",
                "hallazgos_ids": [h.get('id') for h in r.hallazgos] if r.hallazgos else [],
            }
            for r in records
        ]
