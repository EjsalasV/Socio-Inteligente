from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.repositories.file_repository import repo
from backend.services.document_ingest_service import ingest_document_for_rag


DOCUMENT_TYPES: dict[str, dict[str, str]] = {
    "prior_financial_statements": {
        "label": "Estados financieros auditados anteriores",
        "authority": "source_document",
    },
    "prior_internal_control": {
        "label": "Informe de control interno o carta a la gerencia anterior",
        "authority": "source_document",
    },
    "current_preliminary_financials": {
        "label": "Estados financieros preliminares actuales",
        "authority": "source_document",
    },
    "accounting_policy": {"label": "Politica contable", "authority": "source_document"},
    "contract": {"label": "Contrato", "authority": "source_document"},
    "other": {"label": "Otro documento de contexto", "authority": "source_document"},
}

DOCUMENT_ROLES = {
    "complete_report": "Informe completo",
    "audit_opinion": "Opinión del auditor",
    "financial_statements": "Estados financieros",
    "notes": "Notas a los estados financieros",
    "annex": "Anexo",
    "management_letter": "Carta de control interno",
    "other": "Otro",
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt", ".md", ".csv"}
MAX_FILE_SIZE_BYTES = 30 * 1024 * 1024
_SAFE_PERIOD = re.compile(r"^(20\d{2})(?:[-/]?(20\d{2}|0[1-9]|1[0-2]))?$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _manifest_path(cliente_id: str) -> Path:
    return repo.cliente_dir(cliente_id) / "documentos_manifest.json"


def _read_manifest(cliente_id: str) -> list[dict[str, Any]]:
    path = _manifest_path(cliente_id)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return payload if isinstance(payload, list) else []


def _write_manifest(cliente_id: str, rows: list[dict[str, Any]]) -> None:
    path = _manifest_path(cliente_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def document_type_options() -> list[dict[str, str]]:
    return [{"value": key, **value} for key, value in DOCUMENT_TYPES.items()]


def validate_upload(*, filename: str, content: bytes, document_type: str, period: str) -> None:
    if document_type not in DOCUMENT_TYPES:
        raise ValueError("Tipo documental no soportado.")
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Formato no permitido. Use PDF, DOCX, XLSX, TXT, MD o CSV.")
    if not content:
        raise ValueError("El archivo esta vacio.")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValueError("El archivo excede el limite de 30 MB.")
    if period and not _SAFE_PERIOD.match(period.strip()):
        raise ValueError("Periodo invalido. Use un ano como 2024.")


def store_document(
    cliente_id: str,
    *,
    filename: str,
    content: bytes,
    document_type: str,
    period: str = "",
    uploaded_by: str = "",
    document_role: str = "other",
    cutoff_date: str = "",
) -> dict[str, Any]:
    validate_upload(filename=filename, content=content, document_type=document_type, period=period)
    safe_original_name = Path(filename).name
    document_id = uuid4().hex
    suffix = Path(safe_original_name).suffix.lower()
    stored_name = f"{document_id}{suffix}"
    docs_dir = repo.cliente_dir(cliente_id) / "documentos"
    docs_dir.mkdir(parents=True, exist_ok=True)
    stored_path = docs_dir / stored_name
    stored_path.write_bytes(content)

    created_at = _now()
    definition = DOCUMENT_TYPES[document_type]
    try:
        ingestion = ingest_document_for_rag(
            cliente_id,
            stored_path,
            metadata={
                "document_id": document_id,
                "document_type": document_type,
                "document_label": definition["label"],
                "document_period": period,
                "original_name": safe_original_name,
                "authority": definition["authority"],
            },
        )
        complete = not ingestion.get("page_count") or ingestion.get("pages_with_text") == ingestion.get("page_count")
        status = "available" if ingestion.get("indexed") and complete else "available_with_warnings"
    except Exception as exc:  # El archivo se conserva; el usuario puede reprocesarlo despues.
        ingestion = {"indexed": False, "text_chars": 0, "error": str(exc)}
        status = "processing_failed"

    row: dict[str, Any] = {
        "id": document_id,
        "name": safe_original_name,
        "stored_as": stored_name,
        "document_type": document_type,
        "document_label": definition["label"],
        "period": period.strip(),
        "document_role": document_role if document_role in DOCUMENT_ROLES else "other",
        "document_role_label": DOCUMENT_ROLES.get(document_role, DOCUMENT_ROLES["other"]),
        "cutoff_date": cutoff_date.strip(),
        "authority": definition["authority"],
        "status": status,
        "size_bytes": len(content),
        "uploaded_at": created_at,
        "uploaded_by": uploaded_by,
        "ingestion": ingestion,
    }
    rows = _read_manifest(cliente_id)
    rows.append(row)
    _write_manifest(cliente_id, rows)
    return row


def reprocess_document(cliente_id: str, document_id: str) -> dict[str, Any] | None:
    rows = _read_manifest(cliente_id)
    target = next((row for row in rows if row.get("id") == document_id), None)
    if target is None:
        return None
    stored_as = str(target.get("stored_as") or "")
    path = repo.cliente_dir(cliente_id) / "documentos" / Path(stored_as).name
    if not path.exists():
        return None
    ingestion = ingest_document_for_rag(cliente_id, path, metadata={
        "document_id": document_id,
        "document_type": target.get("document_type"),
        "document_label": target.get("document_label"),
        "document_period": target.get("period"),
        "document_role": target.get("document_role"),
        "original_name": target.get("name"),
        "authority": target.get("authority"),
    })
    target["ingestion"] = ingestion
    complete = not ingestion.get("page_count") or ingestion.get("pages_with_text") == ingestion.get("page_count")
    target["status"] = "available" if ingestion.get("indexed") and complete else "available_with_warnings"
    target["reprocessed_at"] = _now()
    _write_manifest(cliente_id, rows)
    return target


def list_documents(cliente_id: str) -> list[dict[str, Any]]:
    rows = _read_manifest(cliente_id)
    return sorted(rows, key=lambda item: str(item.get("uploaded_at") or ""), reverse=True)


def delete_document(cliente_id: str, document_id: str) -> bool:
    rows = _read_manifest(cliente_id)
    target = next((row for row in rows if row.get("id") == document_id), None)
    if target is None:
        return False
    stored_as = str(target.get("stored_as") or "")
    if stored_as:
        path = repo.cliente_dir(cliente_id) / "documentos" / Path(stored_as).name
        if path.exists():
            path.unlink()
        derived = repo.cliente_dir(cliente_id) / "documentos_text" / f"{Path(stored_as).stem}.md"
        if derived.exists():
            derived.unlink()
    _write_manifest(cliente_id, [row for row in rows if row.get("id") != document_id])
    return True
