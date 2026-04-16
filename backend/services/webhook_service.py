"""Service for webhook management and event triggering."""
import time
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime
from urllib.parse import urlparse
import requests

from backend.repositories.webhook_repository import WebhookRepository
from backend.services.audit_logger_service import AuditLoggerService
from backend.models.webhook import WebhookCreate, WebhookUpdate, WebhookResponse

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for managing webhooks and triggering events."""

    VALID_EVENTOS = {
        "hallazgo_creado",
        "alert_critico",
        "reporte_emitido",
        "gate_fallido",
    }

    MAX_RETRIES = 3
    RETRY_BACKOFF = 2  # exponential backoff in seconds
    REQUEST_TIMEOUT = 5

    def __init__(
        self,
        webhook_repo: WebhookRepository,
        audit_logger: AuditLoggerService,
    ):
        """Initialize service with repository and logger."""
        self.repo = webhook_repo
        self.audit_logger = audit_logger

    def create_webhook(
        self, cliente_id: str, webhook_create: WebhookCreate
    ) -> WebhookResponse:
        """Create a new webhook."""
        # Validate URL
        if not self._validate_url(str(webhook_create.url)):
            raise ValueError("Invalid webhook URL (localhost or private IP not allowed)")

        webhook_create.cliente_id = cliente_id
        return self.repo.create(webhook_create)

    def get_webhooks(self, cliente_id: str) -> list[WebhookResponse]:
        """Get all webhooks for a client."""
        return self.repo.get_all_by_cliente(cliente_id)

    def get_webhook_by_id(
        self, cliente_id: str, webhook_id: str
    ) -> Optional[WebhookResponse]:
        """Get a specific webhook."""
        return self.repo.get_by_id(webhook_id, cliente_id)

    def update_webhook(
        self,
        cliente_id: str,
        webhook_id: str,
        webhook_update: WebhookUpdate,
    ) -> Optional[WebhookResponse]:
        """Update a webhook."""
        if webhook_update.url:
            if not self._validate_url(str(webhook_update.url)):
                raise ValueError(
                    "Invalid webhook URL (localhost or private IP not allowed)"
                )
        return self.repo.update(webhook_id, cliente_id, webhook_update)

    def delete_webhook(self, cliente_id: str, webhook_id: str) -> bool:
        """Delete a webhook."""
        return self.repo.delete(webhook_id, cliente_id)

    def test_webhook(self, cliente_id: str, webhook_id: str) -> Dict[str, Any]:
        """Test a webhook with dummy payload."""
        webhook = self.repo.get_by_id(webhook_id, cliente_id)
        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")

        # Create test payload
        test_payload = {
            "evento": webhook.evento,
            "timestamp": datetime.utcnow().isoformat(),
            "cliente_id": cliente_id,
            "test": True,
            "data": {"mensaje": "Payload de prueba"},
        }

        status_code, error = self._send_webhook_request(webhook, test_payload)
        return {
            "webhook_id": webhook_id,
            "status_code": status_code,
            "success": 200 <= status_code < 300,
            "error": error,
        }

    def trigger_webhook(
        self, cliente_id: str, evento: str, data: Dict[str, Any]
    ) -> None:
        """Trigger webhooks for a specific event."""
        if evento not in self.VALID_EVENTOS:
            logger.warning(f"Unknown event type: {evento}")
            return

        webhooks = self.repo.get_active_by_evento(cliente_id, evento)
        if not webhooks:
            return

        # Prepare payload
        payload = {
            "evento": evento,
            "timestamp": datetime.utcnow().isoformat(),
            "cliente_id": cliente_id,
            "data": data,
        }

        for webhook in webhooks:
            self._send_webhook_with_retries(webhook, payload, cliente_id)

    def get_webhook_history(
        self, cliente_id: str, webhook_id: str, limit: int = 10
    ) -> list:
        """Get webhook call history."""
        # Verify webhook belongs to cliente
        webhook = self.repo.get_by_id(webhook_id, cliente_id)
        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")

        return self.repo.get_call_history(webhook_id, limit)

    def _validate_url(self, url: str) -> bool:
        """Validate webhook URL is not localhost or private IP."""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""

            # Reject localhost
            if hostname in ["localhost", "127.0.0.1", "::1"]:
                return False

            # Reject private IP ranges
            private_ranges = [
                "10.",
                "172.16.",
                "172.17.",
                "172.18.",
                "172.19.",
                "172.20.",
                "172.21.",
                "172.22.",
                "172.23.",
                "172.24.",
                "172.25.",
                "172.26.",
                "172.27.",
                "172.28.",
                "172.29.",
                "172.30.",
                "172.31.",
                "192.168.",
                "169.254.",
            ]

            return not any(hostname.startswith(prefix) for prefix in private_ranges)
        except Exception:
            return False

    def _send_webhook_request(
        self, webhook: WebhookResponse, payload: Dict[str, Any]
    ) -> tuple[int, Optional[str]]:
        """Send webhook request and return status code and error."""
        try:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "SocioAI-Webhook/1.0",
                **(webhook.headers or {}),
            }

            start_time = time.time()
            response = requests.post(
                str(webhook.url),
                json=payload,
                headers=headers,
                timeout=self.REQUEST_TIMEOUT,
            )
            duration_ms = int((time.time() - start_time) * 1000)

            # Log call
            self.repo.log_call(
                webhook.id,
                webhook.evento,
                response.status_code,
                duration_ms,
                respuesta=response.text[:500] if response.text else None,
            )

            return response.status_code, None
        except requests.Timeout:
            return 504, "Request timeout"
        except requests.RequestException as e:
            return 500, str(e)
        except Exception as e:
            return 500, str(e)

    def _send_webhook_with_retries(
        self, webhook: WebhookResponse, payload: Dict[str, Any], cliente_id: str
    ) -> None:
        """Send webhook with exponential backoff retries."""
        for attempt in range(self.MAX_RETRIES):
            status_code, error = self._send_webhook_request(webhook, payload)

            if 200 <= status_code < 300:
                # Success
                self.audit_logger.log(
                    cliente_id=cliente_id,
                    action=f"webhook_triggered",
                    details={
                        "webhook_id": webhook.id,
                        "evento": webhook.evento,
                        "url": str(webhook.url),
                        "status": status_code,
                    },
                    affected_resource="webhook",
                )
                return

            # Log failure
            if attempt < self.MAX_RETRIES - 1:
                wait_time = self.RETRY_BACKOFF ** attempt
                logger.warning(
                    f"Webhook {webhook.id} failed (attempt {attempt + 1}/{self.MAX_RETRIES}): "
                    f"status {status_code}. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                # Final failure
                self.audit_logger.log(
                    cliente_id=cliente_id,
                    action="webhook_failed",
                    details={
                        "webhook_id": webhook.id,
                        "evento": webhook.evento,
                        "url": str(webhook.url),
                        "status": status_code,
                        "error": error,
                        "attempts": self.MAX_RETRIES,
                    },
                    affected_resource="webhook",
                )
                logger.error(
                    f"Webhook {webhook.id} failed after {self.MAX_RETRIES} attempts: {error}"
                )
