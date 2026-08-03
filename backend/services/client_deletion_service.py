from __future__ import annotations

from typing import Any

from backend.models.audit import Audit
from backend.models.client import Client
from backend.models.cliente_configuration import ClienteConfiguration
from backend.models.intelligent_analysis_history import IntelligentAnalysisHistory
from backend.models.knowledge_chunk import KnowledgeChunk
from backend.models.knowledge_entity import KnowledgeEntity
from backend.models.knowledge_event import KnowledgeEvent
from backend.models.knowledge_relation import KnowledgeRelation
from backend.models.workpapers_files import WorkpapersFile
from backend.models.workpapers_observation import WorkpapersObservation, WorkpapersObservationHistory
from backend.repositories.file_repository import delete_cliente as delete_cliente_files


def permanently_delete_client(session: Any, cliente: Client) -> dict[str, int | bool]:
    """Elimina datos SQL del cliente y, tras confirmar la transacción, su expediente local/remoto."""
    cliente_id = str(cliente.client_id)
    database_id = int(cliente.id)
    audit_ids = [row[0] for row in session.query(Audit.id).filter(Audit.client_id == database_id).all()]
    file_ids = [row[0] for row in session.query(WorkpapersFile.id).filter(WorkpapersFile.cliente_id == cliente_id).all()]

    observations_query = session.query(WorkpapersObservation.id)
    conditions = []
    if audit_ids:
        conditions.append(WorkpapersObservation.audit_id.in_(audit_ids))
    if file_ids:
        conditions.append(WorkpapersObservation.file_id.in_(file_ids))
    observation_ids: list[int] = []
    if conditions:
        from sqlalchemy import or_

        observation_ids = [row[0] for row in observations_query.filter(or_(*conditions)).all()]

    deleted: dict[str, int | bool] = {}
    if observation_ids:
        deleted["observation_history"] = session.query(WorkpapersObservationHistory).filter(
            WorkpapersObservationHistory.observation_id.in_(observation_ids)
        ).delete(synchronize_session=False)
        deleted["observations"] = session.query(WorkpapersObservation).filter(
            WorkpapersObservation.id.in_(observation_ids)
        ).delete(synchronize_session=False)

    # Primero se eliminan hijos con llaves foráneas; luego entidades y cliente.
    deleted["knowledge_events"] = session.query(KnowledgeEvent).filter(KnowledgeEvent.cliente_id == cliente_id).delete(synchronize_session=False)
    deleted["knowledge_chunks"] = session.query(KnowledgeChunk).filter(KnowledgeChunk.cliente_id == cliente_id).delete(synchronize_session=False)
    deleted["knowledge_relations"] = session.query(KnowledgeRelation).filter(KnowledgeRelation.cliente_id == cliente_id).delete(synchronize_session=False)
    deleted["knowledge_entities"] = session.query(KnowledgeEntity).filter(KnowledgeEntity.cliente_id == cliente_id).delete(synchronize_session=False)
    deleted["workpapers_files"] = session.query(WorkpapersFile).filter(WorkpapersFile.cliente_id == cliente_id).delete(synchronize_session=False)
    deleted["analysis_history"] = session.query(IntelligentAnalysisHistory).filter(IntelligentAnalysisHistory.cliente_id == cliente_id).delete(synchronize_session=False)
    deleted["configurations"] = session.query(ClienteConfiguration).filter(ClienteConfiguration.client_id == database_id).delete(synchronize_session=False)
    deleted["audits"] = session.query(Audit).filter(Audit.client_id == database_id).delete(synchronize_session=False)
    deleted["clients"] = session.query(Client).filter(Client.id == database_id).delete(synchronize_session=False)
    session.commit()

    # El expediente se elimina después del commit para no borrar archivos si falla SQL.
    try:
        deleted["files"] = delete_cliente_files(cliente_id)
    except ValueError:
        # Compatibilidad con IDs heredados que pudieron persistirse antes de
        # normalizarse (por ejemplo, codigos con puntos). La transaccion SQL
        # ya fue confirmada y un ID invalido no puede resolver una carpeta
        # dentro del repositorio seguro.
        deleted["files"] = False
    return deleted
