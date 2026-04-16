"""
Global search endpoint.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.auth import get_current_user
from backend.repositories.file_repository import append_audit_log
from backend.schemas import ApiResponse, UserContext
from backend.services.search_service import search, search_suggestions

LOGGER = logging.getLogger("socio_ai.search")

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=ApiResponse)
def get_search(
    q: str = Query(..., min_length=1, max_length=200),
    cliente_id: str | None = Query(None),
    filters: str | None = Query(None),
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Global search endpoint.

    Query Parameters:
    - q: Search query (required)
    - cliente_id: Optional filter by cliente_id
    - filters: Optional JSON-encoded filters dict
        Example: {"tipo": "hallazgo", "severidad": "alto"}

    Returns:
    {
        "results": [
            {
                "type": "hallazgo" | "area" | "reporte" | "norma" | "procedimiento",
                "title": str,
                "id": str,
                "excerpt": str,
                "href": str,
                "metadata": {...}
            }
        ],
        "total": int
    }
    """
    try:
        filters_dict = {}
        if filters:
            try:
                filters_dict = json.loads(filters)
                if not isinstance(filters_dict, dict):
                    filters_dict = {}
            except json.JSONDecodeError:
                LOGGER.warning("Invalid filters JSON: %s", filters)

        result = search(
            query=q,
            cliente_id=cliente_id,
            filters=filters_dict,
        )

        append_audit_log(
            user_id=user.sub,
            cliente_id=cliente_id or "global",
            endpoint="GET /api/search",
            extra={
                "query": q,
                "results_count": result.get("total", 0),
                "filters": filters_dict,
            },
        )

        return ApiResponse(data=result)

    except Exception as e:
        LOGGER.error("Search error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        ) from e


@router.get("/suggestions", response_model=ApiResponse)
def get_search_suggestions(
    q: str = Query(..., min_length=2, max_length=100),
    cliente_id: str | None = Query(None),
    limit: int = Query(5, ge=1, le=20),
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Get autocomplete suggestions for search input.

    Query Parameters:
    - q: Query prefix (min 2 chars)
    - cliente_id: Optional filter by cliente_id
    - limit: Max suggestions to return (1-20, default 5)

    Returns:
    {
        "suggestions": [
            {
                "text": str,
                "type": "hallazgo" | "area" | "reporte" | "norma" | "procedimiento",
                "id": str
            }
        ]
    }
    """
    try:
        result = search_suggestions(
            query=q,
            cliente_id=cliente_id,
            limit=limit,
        )

        return ApiResponse(data=result)

    except Exception as e:
        LOGGER.error("Search suggestions error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search suggestions failed",
        ) from e
