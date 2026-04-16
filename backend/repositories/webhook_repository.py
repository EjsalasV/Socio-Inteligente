"""Repository for webhook database operations."""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.models.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookCall,
)


class WebhookRepository:
    """Repository for managing webhooks."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, webhook_create: WebhookCreate) -> WebhookResponse:
        """Create a new webhook."""
        webhook_id = str(uuid.uuid4())
        now = datetime.utcnow()

        webhook = {
            "id": webhook_id,
            "cliente_id": webhook_create.cliente_id,
            "evento": webhook_create.evento,
            "url": str(webhook_create.url),
            "headers": webhook_create.headers or {},
            "activo": webhook_create.activo,
            "created_at": now,
            "updated_at": now,
        }

        return WebhookResponse(**webhook)

    def get_by_id(self, webhook_id: str, cliente_id: str) -> Optional[WebhookResponse]:
        """Get webhook by ID and cliente_id."""
        # Mock implementation
        return None

    def get_all_by_cliente(self, cliente_id: str) -> List[WebhookResponse]:
        """Get all webhooks for a client."""
        # Mock implementation
        return []

    def get_active_by_evento(self, cliente_id: str, evento: str) -> List[WebhookResponse]:
        """Get active webhooks for a specific event."""
        # Mock implementation
        return []

    def update(
        self, webhook_id: str, cliente_id: str, webhook_update: WebhookUpdate
    ) -> Optional[WebhookResponse]:
        """Update a webhook."""
        # Mock implementation
        return None

    def delete(self, webhook_id: str, cliente_id: str) -> bool:
        """Delete a webhook."""
        # Mock implementation
        return True

    def log_call(
        self,
        webhook_id: str,
        evento: str,
        status_code: int,
        duracion_ms: int,
        respuesta: Optional[str] = None,
        error: Optional[str] = None,
    ) -> WebhookCall:
        """Log a webhook call."""
        call_id = str(uuid.uuid4())
        now = datetime.utcnow()

        call = {
            "id": call_id,
            "webhook_id": webhook_id,
            "evento": evento,
            "status_code": status_code,
            "respuesta": respuesta,
            "error": error,
            "timestamp": now,
            "duracion_ms": duracion_ms,
        }

        return WebhookCall(**call)

    def get_call_history(
        self, webhook_id: str, limit: int = 10
    ) -> List[WebhookCall]:
        """Get recent webhook call history."""
        # Mock implementation
        return []
