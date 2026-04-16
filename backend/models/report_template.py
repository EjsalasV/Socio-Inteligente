"""Report Template model for customizable report generation."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ReportTemplateBase(BaseModel):
    """Base report template schema."""
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: Optional[str] = Field(None, max_length=1000)
    report_type: str = Field(..., description="Type: resumen|completo|hallazgos")
    estructura: dict = Field(default_factory=dict, description="Template structure (JSON/Jinja2)")
    activo: bool = Field(default=True)


class ReportTemplateCreate(ReportTemplateBase):
    """Create report template schema."""
    cliente_id: str


class ReportTemplateUpdate(BaseModel):
    """Update report template schema."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = Field(None, max_length=1000)
    report_type: Optional[str] = None
    estructura: Optional[dict] = None
    activo: Optional[bool] = None


class ReportTemplateResponse(ReportTemplateBase):
    """Report template response schema."""
    id: str
    cliente_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
