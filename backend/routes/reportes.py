from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends

from backend.auth import authorize_cliente_access, get_current_user
from backend.schemas import ApiResponse, PdfSummaryResponse, UserContext

router = APIRouter(prefix="/reportes", tags=["reportes"])
ROOT = Path(__file__).resolve().parents[2]


@router.get("/{cliente_id}/executive-pdf", response_model=ApiResponse)
def get_executive_pdf(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)

    exports_dir = ROOT / "data" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    fake_pdf = exports_dir / f"{cliente_id}_executive_summary.pdf"
    if not fake_pdf.exists():
        fake_pdf.write_bytes(b"%PDF-1.4\n% placeholder report\n")

    payload = PdfSummaryResponse(
        cliente_id=cliente_id,
        report_name=fake_pdf.name,
        generated_at=datetime.now(timezone.utc),
        path=str(fake_pdf),
    )
    return ApiResponse(data=payload.model_dump())
