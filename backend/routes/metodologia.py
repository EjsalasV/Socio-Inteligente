from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.auth import get_current_user
from backend.routes.chat import post_metodologia
from backend.schemas import ApiResponse, MetodoRequest, UserContext

router = APIRouter(prefix="/metodologia", tags=["metodologia"])


@router.post("/{cliente_id}", response_model=ApiResponse)
def metodologia_endpoint(
    cliente_id: str,
    payload: MetodoRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    return post_metodologia(cliente_id=cliente_id, payload=payload, user=user)
