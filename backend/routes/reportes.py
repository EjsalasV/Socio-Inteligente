from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import append_hallazgo, read_hallazgos, read_memo, write_memo
from backend.routes.dashboard import get_dashboard
from backend.routes.workpapers import _generate_tasks, _merge_saved_tasks, _quality_gates
from backend.schemas import ApiResponse, PdfSummaryResponse, ReportMemoResponse, UserContext
from backend.services.rag_chat_service import generate_chat_response

router = APIRouter(prefix="/reportes", tags=["reportes"])
ROOT = Path(__file__).resolve().parents[2]
EXPORTS_DIR = ROOT / "data" / "exports"
REPORTS_META_DIR = ROOT / "data" / "clientes"


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _history_path(cliente_id: str) -> Path:
    return REPORTS_META_DIR / cliente_id / "reportes_historial.json"


def _read_history(cliente_id: str) -> list[dict[str, Any]]:
    path = _history_path(cliente_id)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [x for x in payload if isinstance(x, dict)]


def _append_history(cliente_id: str, record: dict[str, Any]) -> None:
    history = _read_history(cliente_id)
    history.append(record)
    path = _history_path(cliente_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history[-50:], ensure_ascii=False, indent=2), encoding="utf-8")


def _report_requirements(cliente_id: str, user: UserContext) -> dict[str, Any]:
    dashboard = get_dashboard(cliente_id=cliente_id, user=user)
    top_areas = list(dashboard.top_areas or [])
    hallazgos = read_hallazgos(cliente_id).strip()
    generated = _generate_tasks(cliente_id)
    merged = _merge_saved_tasks(cliente_id, generated)
    gates, coverage = _quality_gates(cliente_id, merged)
    gates_map = {g.code: g.status for g in gates}

    missing_sections: list[str] = []
    if not top_areas:
        missing_sections.append("No hay areas priorizadas para el resumen ejecutivo.")
    if not hallazgos:
        missing_sections.append("No existe conclusion tecnica en hallazgos.")
    if gates_map.get("REPORT") != "ok":
        missing_sections.append("Gate REPORT debe estar en estado ok para emitir informe.")
    if coverage.total_assertions > 0 and coverage.coverage_pct <= 0:
        missing_sections.append("No existe cobertura de afirmaciones documentada para las areas del cliente.")

    can_emit_final = len(missing_sections) == 0
    can_emit_draft = bool(top_areas)
    return {
        "dashboard": dashboard,
        "top_areas": top_areas,
        "hallazgos": hallazgos,
        "gates": gates,
        "gates_map": gates_map,
        "coverage": coverage,
        "missing_sections": missing_sections,
        "can_emit_draft": can_emit_draft,
        "can_emit_final": can_emit_final,
    }


def _ensure_required_sections(cliente_id: str, user: UserContext, *, final_mode: bool) -> tuple[Any, list[Any], str]:
    report = _report_requirements(cliente_id, user)
    dashboard = report["dashboard"]
    top_areas = report["top_areas"]
    hallazgos = report["hallazgos"]
    missing_sections = report["missing_sections"]
    can_emit_draft = bool(report["can_emit_draft"])
    can_emit_final = bool(report["can_emit_final"])
    gates_map = report["gates_map"]

    if final_mode and not can_emit_final:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Faltan secciones obligatorias para generar el PDF final.",
                "errors": missing_sections,
                "gates": gates_map,
            },
        )
    if (not final_mode) and (not can_emit_draft):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "No hay informacion minima para emitir borrador interno.",
                "errors": ["No hay areas priorizadas para el resumen ejecutivo."],
                "gates": gates_map,
            },
        )
    if not hallazgos:
        hallazgos = "Borrador interno sin conclusion consolidada aun. Completar hallazgos para emision final."
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


def _build_memo_fallback(*, dashboard: Any, top_areas: list[Any], hallazgos: str) -> str:
    areas = ", ".join([f"{x.codigo} ({x.nombre})" for x in top_areas[:3]]) if top_areas else "sin areas destacadas"
    short_h = hallazgos.strip()
    if len(short_h) > 900:
        short_h = short_h[:900] + "..."
    return (
        f"Memo Ejecutivo - {dashboard.nombre_cliente}\n\n"
        f"Riesgo global: {dashboard.riesgo_global}.\n"
        f"Materialidad de planeacion: {dashboard.materialidad_global:,.2f}.\n"
        f"Areas prioritarias: {areas}.\n\n"
        "Recomendacion:\n"
        "1) Cerrar procedimientos pendientes en areas altas.\n"
        "2) Documentar evidencia de soporte y conclusion por area.\n"
        "3) Validar consistencia entre TB, Mayor y revelaciones.\n\n"
        f"Contexto de hallazgos:\n{short_h}"
    )


@router.get("/{cliente_id}/executive-pdf", response_model=ApiResponse)
def get_executive_pdf(
    cliente_id: str,
    mode: str = Query("draft", pattern="^(draft|final)$"),
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)

    final_mode = mode == "final"
    dashboard, top_areas, hallazgos = _ensure_required_sections(cliente_id, user, final_mode=final_mode)
    html = _render_executive_html(dashboard=dashboard, top_areas=top_areas, hallazgos=hallazgos)
    pdf_bytes = _html_to_pdf_bytes(html)

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_name = f"{cliente_id}_executive_summary_{timestamp}.pdf"
    out_path = EXPORTS_DIR / report_name
    out_path.write_bytes(pdf_bytes)

    file_hash = hashlib.sha256(pdf_bytes).hexdigest()
    _append_history(
        cliente_id,
        {
            "kind": "executive_pdf",
            "report_name": report_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "path": str(out_path),
            "file_hash": file_hash,
            "size_bytes": len(pdf_bytes),
            "status": "success",
            "origin": "motor_html_pdf_final" if final_mode else "motor_html_pdf_draft",
        },
    )
    payload = PdfSummaryResponse(
        cliente_id=cliente_id,
        report_name=report_name,
        generated_at=datetime.now(timezone.utc),
        path=str(out_path),
        file_hash=file_hash,
        size_bytes=len(pdf_bytes),
    )
    return ApiResponse(data=payload.model_dump())


@router.get("/{cliente_id}/executive-pdf/file")
def get_executive_pdf_file(
    cliente_id: str,
    path: str = Query(...),
    user: UserContext = Depends(get_current_user),
) -> FileResponse:
    authorize_cliente_access(cliente_id, user)
    target = Path(path)
    if not target.is_absolute():
        target = (ROOT / target).resolve()
    else:
        target = target.resolve()

    exports_resolved = EXPORTS_DIR.resolve()
    if not str(target).startswith(str(exports_resolved)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ruta de archivo invalida.")
    if not target.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado.")
    return FileResponse(path=target, filename=target.name, media_type="application/pdf")


@router.post("/{cliente_id}/memo", response_model=ApiResponse)
def post_executive_memo(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    dashboard, top_areas, hallazgos = _ensure_required_sections(cliente_id, user, final_mode=False)
    query = (
        "Genera un memo ejecutivo de auditoria en espanol para socio firmante. "
        "Incluye: riesgo global, materialidad, top areas, recomendaciones accionables y siguiente paso."
    )
    rag = generate_chat_response(cliente_id, query)
    memo = str(rag.get("answer") or "").strip()
    provider = str(rag.get("provider") or "llm")
    if not memo:
        memo = _build_memo_fallback(dashboard=dashboard, top_areas=top_areas, hallazgos=hallazgos)

    write_memo(cliente_id, memo)
    marker = f"## Memo Ejecutivo ({datetime.now(timezone.utc).date().isoformat()})"
    append_hallazgo(cliente_id, f"{marker}\n\n{memo}")
    _append_history(
        cliente_id,
        {
            "kind": "executive_memo",
            "report_name": f"{cliente_id}_memo_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "path": "",
            "file_hash": hashlib.sha256(memo.encode("utf-8")).hexdigest(),
            "size_bytes": len(memo.encode("utf-8")),
            "status": "success",
            "origin": f"{provider}_rag" if str(rag.get("answer") or "").strip() else "fallback",
        },
    )

    payload = ReportMemoResponse(
        cliente_id=cliente_id,
        memo=memo,
        generated_at=datetime.now(timezone.utc),
        source=f"{provider}_rag" if str(rag.get("answer") or "").strip() else "fallback",
    )
    return ApiResponse(data=payload.model_dump())


@router.get("/{cliente_id}/memo", response_model=ApiResponse)
def get_executive_memo(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    memo = read_memo(cliente_id)
    payload = ReportMemoResponse(
        cliente_id=cliente_id,
        memo=memo,
        generated_at=datetime.now(timezone.utc),
        source="saved" if memo else "empty",
    )
    return ApiResponse(data=payload.model_dump())


@router.get("/{cliente_id}/historial", response_model=ApiResponse)
def get_report_history(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    generated = _generate_tasks(cliente_id)
    merged = _merge_saved_tasks(cliente_id, generated)
    gates, coverage = _quality_gates(cliente_id, merged)
    gate_map = {g.code: g.status for g in gates}
    history = _read_history(cliente_id)
    return ApiResponse(
        data={
            "cliente_id": cliente_id,
            "gates": [g.model_dump() for g in gates],
            "gate_status": gate_map,
            "coverage_summary": coverage.model_dump(),
            "items": history,
        }
    )


@router.get("/{cliente_id}/status", response_model=ApiResponse)
def get_report_status(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    report = _report_requirements(cliente_id, user)
    return ApiResponse(
        data={
            "cliente_id": cliente_id,
            "gates": [g.model_dump() for g in report.get("gates", [])],
            "missing_sections": report.get("missing_sections", []),
            "can_emit_draft": bool(report.get("can_emit_draft")),
            "can_emit_final": bool(report.get("can_emit_final")),
            "coverage_summary": report.get("coverage").model_dump() if report.get("coverage") else {},
        }
    )
