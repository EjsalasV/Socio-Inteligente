"""Webhook model for event-driven integrations."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class WebhookBase(BaseModel):
    """Base webhook schema."""
    evento: str = Field(..., description="Event type: hallazgo_creado|alert_critico|reporte_emitido|gate_fallido")
    url: HttpUrl
    headers: Optional[dict] = Field(default_factory=dict, description="Custom headers (JSON)")
    activo: bool = Field(default=True)


class WebhookCreate(WebhookBase):
    """Create webhook schema."""
    cliente_id: str


class WebhookUpdate(BaseModel):
    """Update webhook schema."""
    evento: Optional[str] = None
    url: Optional[HttpUrl] = None
    headers: Optional[dict] = None
    activo: Optional[bool] = None


class WebhookResponse(WebhookBase):
    """Webhook response schema."""
    id: str
    cliente_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookCall(BaseModel):
    """Webhook call history schema."""
    id: str
    webhook_id: str
    evento: str
    status_code: int
    respuesta: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime
    duracion_ms: int

    class Config:
        from_attributes = True
