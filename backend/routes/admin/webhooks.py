"""API routes for webhook management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.services.webhook_service import WebhookService
from backend.repositories.webhook_repository import WebhookRepository
from backend.services.audit_logger_service import AuditLoggerService
from backend.models.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookCall,
)
from backend.auth import verify_token

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def get_webhook_service(
    session: Session = Depends(lambda: Session()),
) -> WebhookService:
    """Get webhook service dependency."""
    repo = WebhookRepository(session)
    audit_logger = AuditLoggerService(session)
    return WebhookService(repo, audit_logger)


@router.get("/{cliente_id}", response_model=list[WebhookResponse])
async def get_webhooks(
    cliente_id: str,
    webhook_service: WebhookService = Depends(get_webhook_service),
    token: dict = Depends(verify_token),
):
    """Get all webhooks for a client."""
    # Verify cliente access
    if token.get("cliente_id") != cliente_id and token.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    webhooks = webhook_service.get_webhooks(cliente_id)
    return webhooks


@router.post("/{cliente_id}", response_model=WebhookResponse)
async def create_webhook(
    cliente_id: str,
    webhook_create: WebhookCreate,
    webhook_service: WebhookService = Depends(get_webhook_service),
    token: dict = Depends(verify_token),
):
    """Create a new webhook (admin only)."""
    if token.get("role") not in ["admin", "socio"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create webhooks",
        )

    try:
        webhook = webhook_service.create_webhook(cliente_id, webhook_create)
        return webhook
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.put("/{cliente_id}/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    cliente_id: str,
    webhook_id: str,
    webhook_update: WebhookUpdate,
    webhook_service: WebhookService = Depends(get_webhook_service),
    token: dict = Depends(verify_token),
):
    """Update a webhook (admin only)."""
    if token.get("role") not in ["admin", "socio"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    try:
        webhook = webhook_service.update_webhook(cliente_id, webhook_id, webhook_update)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found"
            )
        return webhook
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.delete("/{cliente_id}/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    cliente_id: str,
    webhook_id: str,
    webhook_service: WebhookService = Depends(get_webhook_service),
    token: dict = Depends(verify_token),
):
    """Delete a webhook (admin only)."""
    if token.get("role") not in ["admin", "socio"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    success = webhook_service.delete_webhook(cliente_id, webhook_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found"
        )


@router.post("/{cliente_id}/{webhook_id}/test")
async def test_webhook(
    cliente_id: str,
    webhook_id: str,
    webhook_service: WebhookService = Depends(get_webhook_service),
    token: dict = Depends(verify_token),
):
    """Test a webhook with dummy payload."""
    if token.get("role") not in ["admin", "socio"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    try:
        result = webhook_service.test_webhook(cliente_id, webhook_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get("/{cliente_id}/{webhook_id}/history", response_model=list[WebhookCall])
async def get_webhook_history(
    cliente_id: str,
    webhook_id: str,
    limit: int = 10,
    webhook_service: WebhookService = Depends(get_webhook_service),
    token: dict = Depends(verify_token),
):
    """Get webhook call history."""
    # Verify cliente access
    if token.get("cliente_id") != cliente_id and token.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    try:
        history = webhook_service.get_webhook_history(cliente_id, webhook_id, limit)
        return history
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
