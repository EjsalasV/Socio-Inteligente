from __future__ import annotations

from pathlib import Path
from typing import Iterable
import unicodedata

# Raw byte replacements for common cp1252 artifacts found in UTF-8-broken files.
_BYTE_REPLACEMENTS: dict[bytes, bytes] = {
    b"\x91": b"'",
    b"\x92": b"'",
    b"\x93": b'"',
    b"\x94": b'"',
    b"\x96": b"-",
    b"\x97": b"-",
    b"\x85": b"...",
    b"\xa0": b" ",
}

# Unicode punctuation replacements to normalize to keyboard-safe chars.
_TEXT_REPLACEMENTS: dict[str, str] = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u2026": "...",
    "\u00a0": " ",
    "\ufeff": "",  # remove BOM if present in text
    "\ufffd": "-",  # replacement char from broken decodes
}

_ALLOWED_EXTENSIONS = {".py", ".yaml", ".yml", ".md"}


def _iter_target_files(root_paths: Iterable[Path]) -> Iterable[Path]:
    for root in root_paths:
        if not root.exists() or not root.is_dir():
            continue
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in _ALLOWED_EXTENSIONS:
                yield p


def sanitize_text(text: str) -> str:
    sanitized = text
    for old, new in _TEXT_REPLACEMENTS.items():
        sanitized = sanitized.replace(old, new)
    sanitized = unicodedata.normalize("NFKC", sanitized)
    return sanitized


def sanitize_file(path: Path) -> bool:
    raw = path.read_bytes()

    # Replace frequent invalid bytes first to improve decode success.
    fixed_raw = raw
    for old, new in _BYTE_REPLACEMENTS.items():
        fixed_raw = fixed_raw.replace(old, new)

    # Decode robustly. Prefer UTF-8, then cp1252 as fallback.
    try:
        text = fixed_raw.decode("utf-8")
    except UnicodeDecodeError:
        text = fixed_raw.decode("cp1252", errors="replace")

    sanitized_text = sanitize_text(text)

    # Write in UTF-8 without BOM and with normalized LF newlines.
    output_bytes = sanitized_text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")

    if output_bytes != raw:
        path.write_bytes(output_bytes)
        return True
    return False


def sanitize_workspace(base_dir: Path | None = None) -> dict[str, int]:
    base = Path(base_dir) if base_dir else Path.cwd()
    roots = [base / "app", base / "data"]

    scanned = 0
    changed = 0
    for file_path in _iter_target_files(roots):
        scanned += 1
        if sanitize_file(file_path):
            changed += 1

    return {"scanned": scanned, "changed": changed}


def main() -> None:
    summary = sanitize_workspace()
    print(f"Sanitizer completed. scanned={summary['scanned']} changed={summary['changed']}")


if __name__ == "__main__":
    main()
