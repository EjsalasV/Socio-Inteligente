"""
Run: python scripts/fix_encoding.py
Fixes BOM and common mojibake in .py/.yaml/.yml/.md/.txt files under the repo.
"""

from __future__ import annotations

from pathlib import Path

EXTENSIONS = {".py", ".yaml", ".yml", ".md", ".txt"}
ROOT = Path(__file__).resolve().parent.parent

MOJIBAKE_MAP = {
    "\ufeff": "",
    "Ã¡": "Ã¡",
    "Ã©": "Ã©",
    "Ã­": "Ã­",
    "Ã³": "Ã³",
    "Ãº": "Ãº",
    "Ã": "Ã",
    "Ã‰": "Ã‰",
    "Ã": "Ã",
    "Ã“": "Ã“",
    "Ãš": "Ãš",
    "Ã±": "Ã±",
    "Ã‘": "Ã‘",
    "Â¿": "Â¿",
    "Â¡": "Â¡",
    "Ã¼": "Ã¼",
    "Ãœ": "Ãœ",
    "Ã¤": "Ã¤",
    "Ã„": "Ã„",
    "Ã¶": "Ã¶",
    "Ã–": "Ã–",
    "-": "-",
    "-": "-",
    "'": "'",
    "'": "'",
    """: '"',
    """: '"',
    "...": "...",
}

SKIP_DIRS = {"node_modules", ".next", "__pycache__", ".git", "venv", ".venv"}


def fix_file(path: Path) -> bool:
    try:
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1", errors="replace")

        original = text
        for bad, good in MOJIBAKE_MAP.items():
            text = text.replace(bad, good)

        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        if normalized != original:
            path.write_text(normalized, encoding="utf-8", newline="\n")
            return True
        return False
    except Exception as exc:
        print(f"  ERROR {path}: {exc}")
        return False


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def main() -> None:
    fixed: list[Path] = []
    skipped = 0

    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue
        if should_skip(path):
            continue
        if fix_file(path):
            fixed.append(path)
        else:
            skipped += 1

    print(f"\nFixed: {len(fixed)}")
    for item in fixed:
        print(f"  {item.relative_to(ROOT)}")
    print(f"\nNo changes: {skipped}")


if __name__ == "__main__":
    main()
