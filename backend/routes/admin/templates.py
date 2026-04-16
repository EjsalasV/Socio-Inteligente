"""API routes for report template management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.services.template_service import TemplateService
from backend.repositories.template_repository import TemplateRepository
from backend.models.report_template import (
    ReportTemplateCreate,
    ReportTemplateUpdate,
    ReportTemplateResponse,
)
from backend.auth import verify_token

router = APIRouter(prefix="/api/templates", tags=["templates"])


def get_template_service(session: Session = Depends(lambda: Session())) -> TemplateService:
    """Get template service dependency."""
    repo = TemplateRepository(session)
    return TemplateService(repo)


@router.get("/{cliente_id}", response_model=list[ReportTemplateResponse])
async def get_templates(
    cliente_id: str,
    template_service: TemplateService = Depends(get_template_service),
    token: dict = Depends(verify_token),
):
    """Get all templates for a client."""
    # Verify cliente access
    if token.get("cliente_id") != cliente_id and token.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    templates = template_service.get_templates(cliente_id)
    return templates


@router.post("/{cliente_id}", response_model=ReportTemplateResponse)
async def create_template(
    cliente_id: str,
    template_create: ReportTemplateCreate,
    template_service: TemplateService = Depends(get_template_service),
    token: dict = Depends(verify_token),
):
    """Create a new template (admin only)."""
    # Verify admin access
    if token.get("role") not in ["admin", "socio"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create templates",
        )

    template = template_service.create_template(cliente_id, template_create)
    return template


@router.put("/{cliente_id}/{template_id}", response_model=ReportTemplateResponse)
async def update_template(
    cliente_id: str,
    template_id: str,
    template_update: ReportTemplateUpdate,
    template_service: TemplateService = Depends(get_template_service),
    token: dict = Depends(verify_token),
):
    """Update a template (admin only)."""
    if token.get("role") not in ["admin", "socio"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    template = template_service.update_template(cliente_id, template_id, template_update)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    return template


@router.delete("/{cliente_id}/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    cliente_id: str,
    template_id: str,
    template_service: TemplateService = Depends(get_template_service),
    token: dict = Depends(verify_token),
):
    """Delete a template (admin only)."""
    if token.get("role") not in ["admin", "socio"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    success = template_service.delete_template(cliente_id, template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )


@router.post("/{cliente_id}/{template_id}/preview")
async def preview_template(
    cliente_id: str,
    template_id: str,
    data: dict = None,
    template_service: TemplateService = Depends(get_template_service),
    token: dict = Depends(verify_token),
):
    """Preview a template with sample data."""
    if not data:
        data = {
            "cliente_nombre": "Ejemplo Cliente",
            "periodo": "2024",
            "hallazgos": [],
        }

    try:
        html = template_service.apply_template(cliente_id, template_id, data)
        return {"html": html}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("/defaults/{report_type}")
async def get_default_template(
    report_type: str,
    template_service: TemplateService = Depends(get_template_service),
):
    """Get default template for report type."""
    template = template_service.get_default_template(report_type)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return template
