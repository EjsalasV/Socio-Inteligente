from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import read_hallazgos
from backend.routes.dashboard import get_dashboard
from backend.routes.workpapers import _generate_tasks, _merge_saved_tasks, _quality_gates
from backend.schemas import ApiResponse, PdfSummaryResponse, UserContext

router = APIRouter(prefix="/reportes", tags=["reportes"])
ROOT = Path(__file__).resolve().parents[2]


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _ensure_required_sections(cliente_id: str, user: UserContext) -> tuple[Any, list[Any], str]:
    dashboard = get_dashboard(cliente_id=cliente_id, user=user)
    top_areas = list(dashboard.top_areas or [])
    hallazgos = read_hallazgos(cliente_id).strip()
    generated = _generate_tasks(cliente_id)
    merged = _merge_saved_tasks(cliente_id, generated)
    gates = _quality_gates(cliente_id, merged)
    gates_map = {g.code: g.status for g in gates}

    errors: list[str] = []
    if not top_areas:
        errors.append("No hay areas priorizadas para el resumen ejecutivo.")
    if not hallazgos:
        errors.append("No existe conclusion tecnica en hallazgos.")
    if gates_map.get("REPORT") != "ok":
        errors.append("Gate REPORT debe estar en estado ok para emitir informe.")
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Faltan secciones obligatorias para generar el PDF.", "errors": errors, "gates": gates_map},
        )
    return dashboard, top_areas, hallazgos


def _render_executive_html(*, dashboard: Any, top_areas: list[Any], hallazgos: str) -> str:
    rows = ""
    for item in top_areas[:6]:
        rows += (
            "<tr>"
            f"<td>{_safe_text(item.codigo)}</td>"
            f"<td>{_safe_text(item.nombre)}</td>"
            f"<td>{float(item.score_riesgo):.2f}</td>"
            f"<td>{_safe_text(item.prioridad).upper()}</td>"
            "</tr>"
        )

    return f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          body {{ font-family: Helvetica, Arial, sans-serif; color: #0f172a; font-size: 12px; }}
          .header {{ background: linear-gradient(135deg, #041627 0%, #1a2b3c 100%); color: #fff; padding: 22px; border-radius: 10px; }}
          .small {{ color: #64748b; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; }}
          .title {{ font-size: 27px; margin: 6px 0 0 0; }}
          .grid {{ margin-top: 16px; }}
          .card {{ border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; margin-bottom: 8px; }}
          table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
          th, td {{ border: 1px solid #cbd5e1; padding: 6px; text-align: left; }}
          th {{ background: #f1f5f9; }}
          .footer {{ margin-top: 24px; color: #64748b; font-size: 10px; }}
          pre {{ white-space: pre-wrap; line-height: 1.35; font-size: 11px; background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 8px; }}
        </style>
      </head>
      <body>
        <div class="header">
          <div class="small">Socio AI · Reporte Ejecutivo</div>
          <div class="title">{_safe_text(dashboard.nombre_cliente)}</div>
          <div>Periodo: {_safe_text(dashboard.periodo)} · Riesgo Global: {_safe_text(dashboard.riesgo_global).upper()}</div>
        </div>

        <div class="grid">
          <div class="card"><b>Materialidad de planeacion:</b> ${float(dashboard.materialidad_global):,.2f}</div>
          <div class="card"><b>Materialidad de ejecucion:</b> ${float(dashboard.materialidad_ejecucion):,.2f}</div>
          <div class="card"><b>Umbral trivial:</b> ${float(dashboard.umbral_trivial):,.2f}</div>
        </div>

        <h3>Top areas de riesgo</h3>
        <table>
          <thead>
            <tr><th>Area</th><th>Nombre</th><th>Score</th><th>Prioridad</th></tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>

        <h3>Conclusion tecnica</h3>
        <pre>{hallazgos}</pre>

        <div class="footer">
          Generado: {datetime.now(timezone.utc).isoformat()} · Socio AI Executive Report
        </div>
      </body>
    </html>
    """


def _html_to_pdf_bytes(html: str) -> bytes:
    try:
        from xhtml2pdf import pisa
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dependencia xhtml2pdf no disponible en backend.",
        ) from exc

    output = BytesIO()
    result = pisa.CreatePDF(src=html, dest=output)
    if result.err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo renderizar PDF.")
    return output.getvalue()


@router.get("/{cliente_id}/executive-pdf", response_model=ApiResponse)
def get_executive_pdf(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)

    dashboard, top_areas, hallazgos = _ensure_required_sections(cliente_id, user)
    html = _render_executive_html(dashboard=dashboard, top_areas=top_areas, hallazgos=hallazgos)
    pdf_bytes = _html_to_pdf_bytes(html)

    exports_dir = ROOT / "data" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_name = f"{cliente_id}_executive_summary_{timestamp}.pdf"
    out_path = exports_dir / report_name
    out_path.write_bytes(pdf_bytes)

    file_hash = hashlib.sha256(pdf_bytes).hexdigest()
    payload = PdfSummaryResponse(
        cliente_id=cliente_id,
        report_name=report_name,
        generated_at=datetime.now(timezone.utc),
        path=str(out_path),
        file_hash=file_hash,
        size_bytes=len(pdf_bytes),
    )
    return ApiResponse(data=payload.model_dump())
