#!/usr/bin/env python3
"""
Repara mojibake en archivos markdown de data/conocimiento_normativo.

Uso:
  python fix_encoding.py
  python fix_encoding.py --backups-only
  python fix_encoding.py --path data/conocimiento_normativo/metodologia/_backup
"""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_BASE = ROOT / "data" / "conocimiento_normativo"
MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ï»¿", "Ãƒ", "Ã‚")


def looks_broken(text: str) -> bool:
    return any(marker in text for marker in MOJIBAKE_MARKERS)


def repair_text(text: str) -> str:
    """
    Intenta revertir una o varias capas de mojibake tipico UTF-8 -> latin1/cp1252.
    """
    fixed = text.replace("\ufeff", "").replace("ï»¿", "")

    for _ in range(3):
        if not looks_broken(fixed):
            break

        repaired = None
        for source_encoding in ("latin-1", "cp1252"):
            try:
                candidate = fixed.encode(source_encoding).decode("utf-8")
            except Exception:
                continue

            if candidate and candidate != fixed:
                repaired = candidate
                break

        if not repaired or repaired == fixed:
            break

        fixed = repaired.replace("\ufeff", "").replace("ï»¿", "")

    return fixed


def fix_file(filepath: Path) -> tuple[bool, str]:
    try:
        original = filepath.read_text(encoding="utf-8")
    except Exception as exc:
        return False, f"read_error: {exc}"

    repaired = repair_text(original)
    if looks_broken(repaired) and not repaired.count("Ã") < original.count("Ã"):
        return True, "unchanged"
    if repaired == original:
        return True, "unchanged"

    try:
        filepath.write_text(repaired, encoding="utf-8", newline="\n")
    except Exception as exc:
        return False, f"write_error: {exc}"

    return True, "fixed"


def iter_target_files(base_path: Path, backups_only: bool) -> list[Path]:
    files = sorted(base_path.rglob("*.md"))
    if backups_only:
        files = [path for path in files if "_backup" in path.parts]
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description="Arregla encoding de markdown normativo")
    parser.add_argument("--path", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--backups-only", action="store_true")
    args = parser.parse_args()

    base_path = args.path
    if not base_path.is_absolute():
        base_path = ROOT / base_path

    if not base_path.exists():
        raise SystemExit(f"Ruta no existe: {base_path}")

    files = iter_target_files(base_path, args.backups_only)
    print(f"Analizando {len(files)} archivos en {base_path}")

    fixed = 0
    unchanged = 0
    failed = 0

    for filepath in files:
        success, status = fix_file(filepath)
        relative = filepath.relative_to(ROOT)
        if not success:
            failed += 1
            print(f"[ERROR] {relative}: {status}")
            continue

        if status == "fixed":
            fixed += 1
            print(f"[FIXED] {relative}")
        else:
            unchanged += 1

    print()
    print(f"Fixed: {fixed}")
    print(f"Unchanged: {unchanged}")
    print(f"Failed: {failed}")


if __name__ == "__main__":
    main()
