from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _strip_xml(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _extract_pdf_native(path: Path) -> tuple[str, int, int]:
    try:
        from pypdf import PdfReader
    except Exception:
        return "", 0, 0
    try:
        reader = PdfReader(str(path))
        chunks: list[str] = []
        pages_with_text = 0
        pages = list(reader.pages[:120])
        for page_number, page in enumerate(pages, start=1):
            txt = page.extract_text() or ""
            if txt.strip():
                pages_with_text += 1
                chunks.append(f"## Pagina {page_number}\n\n{txt.strip()}")
        return "\n\n".join(chunks).strip(), len(pages), pages_with_text
    except Exception:
        return "", 0, 0


def _extract_pdf_ocr(path: Path, page_count: int) -> tuple[str, int]:
    """OCR opcional. Si Poppler/Tesseract no existen, la carga sigue con advertencia."""
    pdftoppm = shutil.which("pdftoppm")
    tesseract = shutil.which("tesseract")
    if pdftoppm and pdftoppm.lower().endswith((".cmd", ".bat")):
        wrapper = Path(pdftoppm).resolve()
        candidates: list[Path] = []
        for parent in wrapper.parents:
            candidates.extend(parent.glob("native/poppler/**/pdftoppm.exe"))
        if candidates:
            pdftoppm = str(candidates[0])
    if not pdftoppm or not tesseract:
        return "", 0
    chunks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="socioai_ocr_") as temp_dir:
        prefix = Path(temp_dir) / "page"
        try:
            subprocess.run(
                [pdftoppm, "-jpeg", "-r", "200", "-f", "1", "-l", str(min(page_count or 120, 120)), str(path), str(prefix)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=180,
            )
            images = sorted(Path(temp_dir).glob("page-*.jpg"))
            for page_number, image in enumerate(images, start=1):
                result = subprocess.run(
                    [tesseract, str(image), "stdout", "-l", "spa+eng"],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=45,
                )
                if result.stdout.strip():
                    chunks.append(f"## Pagina {page_number}\n\n{result.stdout.strip()}")
        except (OSError, subprocess.SubprocessError):
            return "", 0
    return "\n\n".join(chunks).strip(), len(chunks)


def _extract_pdf(path: Path) -> tuple[str, dict[str, Any]]:
    native, page_count, native_pages = _extract_pdf_native(path)
    # Una pagina escaneada suele producir menos de 80 caracteres utilizables.
    needs_ocr = page_count > 0 and (native_pages < page_count or len(native) < page_count * 80)
    if needs_ocr:
        ocr_text, ocr_pages = _extract_pdf_ocr(path, page_count)
        if len(ocr_text) > len(native):
            return ocr_text, {
                "extraction_method": "ocr",
                "page_count": page_count,
                "pages_with_text": ocr_pages,
                "ocr_used": True,
            }
    return native, {
        "extraction_method": "native" if native else "metadata_only",
        "page_count": page_count,
        "pages_with_text": native_pages,
        "ocr_used": False,
        "ocr_recommended": needs_ocr and not native,
    }


def _extract_docx(path: Path) -> str:
    try:
        with zipfile.ZipFile(path, "r") as zf:
            raw = zf.read("word/document.xml").decode("utf-8", errors="ignore")
        return _strip_xml(raw)
    except Exception:
        return ""


def _extract_xlsx(path: Path) -> str:
    """Extrae una vista acotada de Excel sin enviar el libro completo al LLM."""
    try:
        import openpyxl
    except Exception:
        return ""
    try:
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sections: list[str] = []
        remaining_rows = 2500
        for sheet in workbook.worksheets[:20]:
            if remaining_rows <= 0:
                break
            rows: list[str] = []
            for row in sheet.iter_rows(values_only=True):
                values = [str(value).strip() for value in row[:40] if value not in (None, "")]
                if values:
                    rows.append(" | ".join(values))
                    remaining_rows -= 1
                if remaining_rows <= 0:
                    break
            if rows:
                sections.append(f"## Hoja {sheet.title}\n\n" + "\n".join(rows))
        workbook.close()
        return "\n\n".join(sections).strip()
    except Exception:
        return ""


def _extract_text(path: Path) -> tuple[str, dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".csv"}:
        try:
            return path.read_text(encoding="utf-8", errors="ignore").strip(), {"extraction_method": "native"}
        except Exception:
            return "", {"extraction_method": "metadata_only"}
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path), {"extraction_method": "native"}
    if suffix == ".xlsx":
        return _extract_xlsx(path), {"extraction_method": "native"}
    return "", {"extraction_method": "metadata_only"}


def ingest_document_for_rag(
    cliente_id: str,
    file_path: Path,
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text, extraction = _extract_text(file_path)
    docs_text_dir = file_path.parent.parent / "documentos_text"
    docs_text_dir.mkdir(parents=True, exist_ok=True)
    out_file = docs_text_dir / f"{file_path.stem}.md"

    meta = metadata or {}
    metadata_lines = "\n".join(
        f"{key}: {str(value).strip()}"
        for key, value in meta.items()
        if str(value or "").strip()
    )
    if metadata_lines:
        metadata_lines += "\n"

    if not text:
        out_file.write_text(
            (
                f"# Documento {file_path.name}\n\n"
                f"cliente_id: {cliente_id}\n"
                f"ingested_at: {datetime.now(timezone.utc).isoformat()}\n"
                f"{metadata_lines}"
                "status: metadata_only\n"
                "note: no se pudo extraer texto util para RAG.\n"
            ),
            encoding="utf-8",
        )
        return {"indexed": False, "text_chars": 0, "path": str(out_file), **extraction}

    normalized = re.sub(r"\n{3,}", "\n\n", text).strip()
    content = (
        f"# Documento {file_path.name}\n\n"
        f"cliente_id: {cliente_id}\n"
        f"ingested_at: {datetime.now(timezone.utc).isoformat()}\n"
        f"source_file: {file_path.name}\n\n"
        f"{metadata_lines}\n"
        f"{normalized}\n"
    )
    out_file.write_text(content, encoding="utf-8")
    return {"indexed": True, "text_chars": len(normalized), "path": str(out_file), **extraction}
