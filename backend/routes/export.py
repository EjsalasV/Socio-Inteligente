"""
Export route for generating and downloading reports by role.
"""
from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import append_audit_log
from backend.schemas import ApiResponse, UserContext
from backend.services.export_service import generate_pdf

LOGGER = logging.getLogger("socio_ai.export")

router = APIRouter(prefix="/api", tags=["export"])


@router.post("/reportes/{cliente_id}/export", response_model=ApiResponse)
def post_export_reporte(
    cliente_id: str,
    request_body: dict,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Export/generate a PDF report.

    DEPRECATED: Use POST /api/reportes/{cliente_id}/export/stream instead for direct download.

    Request body:
    {
        "report_type": "resumen_ejecutivo" | "informe_completo" | "hallazgos",
        "role": "junior" | "semi" | "senior" | "socio",
        "incluir_comparativa": true | false,
        "fecha_periodo": "2025-01" (optional)
    }

    Returns:
    {
        "url": "https://s3.../Reporte_Socio_202501.pdf",
        "nombre": "Reporte_Socio_202501.pdf",
        "tamanio_kb": 125,
        "generado_en_ms": 1500
    }
    """
    authorize_cliente_access(cliente_id, user)

    try:
        report_type = request_body.get("report_type", "resumen_ejecutivo")
        role = request_body.get("role", user.role or "junior")
        fecha_periodo = request_body.get("fecha_periodo")
        incluir_comparativa = request_body.get("incluir_comparativa", False)

        # Validate report type
        if report_type not in {"resumen_ejecutivo", "informe_completo", "hallazgos"}:
            raise ValueError(f"Report type '{report_type}' not supported")

        # Validate role
        if role not in {"junior", "semi", "senior", "socio"}:
            role = "junior"

        # Generate PDF
        pdf_bytes = generate_pdf(
            cliente_id=cliente_id,
            report_type=report_type,
            role=role,
            fecha_periodo=fecha_periodo,
        )

        # In a real implementation, upload to S3 and return signed URL
        # For now, we'll generate filename and log
        from datetime import datetime
        now = datetime.now()
        filename = f"Reporte_{role.capitalize()}_{now.strftime('%Y%m%d_%H%M%S')}.pdf"

        # Log export in audit trail
        append_audit_log(
            user_id=user.sub,
            cliente_id=cliente_id,
            endpoint="POST /api/reportes/{cliente_id}/export",
            extra={
                "report_type": report_type,
                "role": role,
                "incluir_comparativa": incluir_comparativa,
                "filename": filename,
                "tamanio_bytes": len(pdf_bytes),
            },
        )

        return ApiResponse(data={
            "filename": filename,
            "tamanio_bytes": len(pdf_bytes),
            "tamanio_kb": len(pdf_bytes) // 1024,
            "report_type": report_type,
            "role": role,
            "generado_en": "via_stream",
        })

    except ValueError as e:
        LOGGER.warning("Validation error in export: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except ImportError as e:
        LOGGER.error("Missing dependency for PDF generation: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation not available. Install weasyprint.",
        ) from e
    except Exception as e:
        LOGGER.error("Export error for cliente_id=%s: %s", cliente_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report",
        ) from e


@router.post("/reportes/{cliente_id}/export/stream")
async def post_export_reporte_stream(
    cliente_id: str,
    request_body: dict,
    user: UserContext = Depends(get_current_user),
):
    """
    Export/generate a PDF report and return as downloadable file.

    Request body:
    {
        "report_type": "resumen_ejecutivo" | "informe_completo" | "hallazgos",
        "role": "junior" | "semi" | "senior" | "socio",
        "incluir_comparativa": true | false,
        "fecha_periodo": "2025-01" (optional)
    }

    Returns: PDF file stream (application/pdf)
    """
    authorize_cliente_access(cliente_id, user)

    try:
        report_type = request_body.get("report_type", "resumen_ejecutivo")
        role = request_body.get("role", user.role or "junior")
        fecha_periodo = request_body.get("fecha_periodo")

        # Validate
        if report_type not in {"resumen_ejecutivo", "informe_completo", "hallazgos"}:
            raise ValueError(f"Report type '{report_type}' not supported")

        if role not in {"junior", "semi", "senior", "socio"}:
            role = "junior"

        # Generate PDF
        pdf_bytes = generate_pdf(
            cliente_id=cliente_id,
            report_type=report_type,
            role=role,
            fecha_periodo=fecha_periodo,
        )

        from datetime import datetime
        now = datetime.now()
        filename = f"Reporte_{role.capitalize()}_{now.strftime('%Y%m%d_%H%M%S')}.pdf"

        # Log export
        append_audit_log(
            user_id=user.sub,
            cliente_id=cliente_id,
            endpoint="POST /api/reportes/{cliente_id}/export/stream",
            extra={
                "report_type": report_type,
                "role": role,
                "filename": filename,
                "tamanio_bytes": len(pdf_bytes),
            },
        )

        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except ValueError as e:
        LOGGER.warning("Validation error in export stream: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except ImportError as e:
        LOGGER.error("Missing dependency for PDF generation: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation not available",
        ) from e
    except Exception as e:
        LOGGER.error("Export stream error for cliente_id=%s: %s", cliente_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report",
        ) from e
