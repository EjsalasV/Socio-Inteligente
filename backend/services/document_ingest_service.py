from __future__ import annotations

import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _strip_xml(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return ""
    try:
        reader = PdfReader(str(path))
        chunks: list[str] = []
        for page in reader.pages[:80]:
            txt = page.extract_text() or ""
            if txt.strip():
                chunks.append(txt.strip())
        return "\n\n".join(chunks).strip()
    except Exception:
        return ""


def _extract_docx(path: Path) -> str:
    try:
        with zipfile.ZipFile(path, "r") as zf:
            raw = zf.read("word/document.xml").decode("utf-8", errors="ignore")
        return _strip_xml(raw)
    except Exception:
        return ""


def _extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".csv"}:
        try:
            return path.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            return ""
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)
    return ""


def ingest_document_for_rag(cliente_id: str, file_path: Path) -> dict[str, Any]:
    text = _extract_text(file_path)
    docs_text_dir = file_path.parent.parent / "documentos_text"
    docs_text_dir.mkdir(parents=True, exist_ok=True)
    out_file = docs_text_dir / f"{file_path.stem}.md"

    if not text:
        out_file.write_text(
            (
                f"# Documento {file_path.name}\n\n"
                f"cliente_id: {cliente_id}\n"
                f"ingested_at: {datetime.now(timezone.utc).isoformat()}\n"
                "status: metadata_only\n"
                "note: no se pudo extraer texto util para RAG.\n"
            ),
            encoding="utf-8",
        )
        return {"indexed": False, "text_chars": 0, "path": str(out_file)}

    normalized = re.sub(r"\n{3,}", "\n\n", text).strip()
    content = (
        f"# Documento {file_path.name}\n\n"
        f"cliente_id: {cliente_id}\n"
        f"ingested_at: {datetime.now(timezone.utc).isoformat()}\n"
        f"source_file: {file_path.name}\n\n"
        f"{normalized}\n"
    )
    out_file.write_text(content, encoding="utf-8")
    return {"indexed": True, "text_chars": len(normalized), "path": str(out_file)}
