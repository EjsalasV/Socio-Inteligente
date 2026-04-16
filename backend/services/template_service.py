"""Service for report template rendering and management."""
from typing import Any, Dict, Optional
from jinja2 import Environment, Template, TemplateSyntaxError
from backend.repositories.template_repository import TemplateRepository
from backend.models.report_template import (
    ReportTemplateCreate,
    ReportTemplateUpdate,
    ReportTemplateResponse,
)


class TemplateService:
    """Service for managing and rendering report templates."""

    def __init__(self, template_repo: TemplateRepository):
        """Initialize service with repository."""
        self.repo = template_repo
        self.jinja_env = Environment(
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def create_template(
        self, cliente_id: str, template_create: ReportTemplateCreate
    ) -> ReportTemplateResponse:
        """Create a new report template."""
        template_create.cliente_id = cliente_id
        return self.repo.create(template_create)

    def get_templates(self, cliente_id: str) -> list[ReportTemplateResponse]:
        """Get all templates for a client."""
        return self.repo.get_all_by_cliente(cliente_id)

    def get_template_by_id(
        self, cliente_id: str, template_id: str
    ) -> Optional[ReportTemplateResponse]:
        """Get a specific template."""
        return self.repo.get_by_id(template_id, cliente_id)

    def update_template(
        self,
        cliente_id: str,
        template_id: str,
        template_update: ReportTemplateUpdate,
    ) -> Optional[ReportTemplateResponse]:
        """Update a template."""
        return self.repo.update(template_id, cliente_id, template_update)

    def delete_template(self, cliente_id: str, template_id: str) -> bool:
        """Delete a template."""
        return self.repo.delete(template_id, cliente_id)

    def apply_template(
        self,
        cliente_id: str,
        template_id: str,
        data: Dict[str, Any],
    ) -> str:
        """Apply a template to data and render HTML."""
        try:
            template_obj = self.repo.get_by_id(template_id, cliente_id)
            if not template_obj:
                raise ValueError(f"Template {template_id} not found")

            # Extract template HTML/Jinja2 from estructura
            template_str = template_obj.estructura.get(
                "template", "<p>No template content</p>"
            )

            # Render template with Jinja2
            template = self.jinja_env.from_string(template_str)
            rendered = template.render(**data)

            return rendered
        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Template rendering failed: {str(e)}")

    def preview_template(
        self, template_estructura: Dict[str, Any], data: Dict[str, Any]
    ) -> str:
        """Preview a template with mock data."""
        try:
            template_str = template_estructura.get(
                "template", "<p>No template content</p>"
            )
            template = self.jinja_env.from_string(template_str)
            rendered = template.render(**data)
            return rendered
        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Template rendering failed: {str(e)}")

    def get_default_template(self, report_type: str) -> Optional[ReportTemplateResponse]:
        """Get default system template by type."""
        return self.repo.get_default_template(report_type)

    def validate_template_syntax(self, template_str: str) -> bool:
        """Validate Jinja2 template syntax."""
        try:
            self.jinja_env.from_string(template_str)
            return True
        except TemplateSyntaxError:
            return False

    def get_template_variables(self, template_str: str) -> list[str]:
        """Extract variable names from a Jinja2 template."""
        try:
            template = self.jinja_env.from_string(template_str)
            # Extract undeclared variables
            return list(template.module.__dict__.get("variables", []))
        except:
            return []
