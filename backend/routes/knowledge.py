from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from backend.auth import authorize_cliente_access, get_current_user
from backend.schemas import (
    ApiResponse,
    KnowledgeAskRequest,
    KnowledgeEntityUpsertRequest,
    KnowledgeRelationUpsertRequest,
    UserContext,
)
from backend.services.knowledge_graph_service import build_graph
from backend.services.knowledge_service import (
    ask_with_event,
    ensure_knowledge_core_enabled,
    get_timeline,
    list_entities,
    upsert_entity,
    upsert_relation,
)
from backend.utils.database import get_session

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/entities", response_model=ApiResponse)
def post_knowledge_entity(
    payload: KnowledgeEntityUpsertRequest,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    ensure_knowledge_core_enabled()
    authorize_cliente_access(payload.cliente_id, user)
    saved = upsert_entity(
        session,
        payload.model_dump(),
        actor=user.display_name or user.sub,
    )
    return ApiResponse(data={"entity": saved})


@router.get("/{cliente_id}/entities", response_model=ApiResponse)
def get_knowledge_entities(
    cliente_id: str,
    entity_type: str | None = Query(None),
    source_module: str | None = Query(None),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    ensure_knowledge_core_enabled()
    authorize_cliente_access(cliente_id, user)
    data = list_entities(
        session,
        cliente_id=cliente_id,
        entity_type=entity_type,
        source_module=source_module,
        q=q,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(data=data)


@router.post("/relations", response_model=ApiResponse)
def post_knowledge_relation(
    payload: KnowledgeRelationUpsertRequest,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    ensure_knowledge_core_enabled()
    authorize_cliente_access(payload.cliente_id, user)
    saved = upsert_relation(
        session,
        payload.model_dump(),
        actor=user.display_name or user.sub,
    )
    return ApiResponse(data={"relation": saved})


@router.get("/{cliente_id}/graph", response_model=ApiResponse)
def get_knowledge_graph(
    cliente_id: str,
    max_entities: int = Query(500, ge=1, le=2000),
    max_relations: int = Query(1000, ge=1, le=5000),
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    ensure_knowledge_core_enabled()
    authorize_cliente_access(cliente_id, user)
    graph = build_graph(
        session,
        cliente_id=cliente_id,
        max_entities=max_entities,
        max_relations=max_relations,
    )
    return ApiResponse(data=graph)


@router.get("/{cliente_id}/timeline", response_model=ApiResponse)
def get_knowledge_timeline(
    cliente_id: str,
    limit: int = Query(100, ge=1, le=500),
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    ensure_knowledge_core_enabled()
    authorize_cliente_access(cliente_id, user)
    timeline = get_timeline(session, cliente_id=cliente_id, limit=limit)
    return ApiResponse(data=timeline)


@router.post("/{cliente_id}/ask", response_model=ApiResponse)
def post_knowledge_ask(
    cliente_id: str,
    payload: KnowledgeAskRequest,
    user: UserContext = Depends(get_current_user),
    session: Any = Depends(get_session),
) -> ApiResponse:
    ensure_knowledge_core_enabled()
    authorize_cliente_access(cliente_id, user)
    response = ask_with_event(
        session,
        cliente_id=cliente_id,
        query=payload.query,
        top_k=payload.top_k,
        actor=user.display_name or user.sub,
    )
    return ApiResponse(data=response)
