from __future__ import annotations

import os
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUSPICIOUS_SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),  # OpenAI/DeepSeek-like keys
    re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}\b"),  # Google API keys
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),  # GitHub tokens
]


def _find_secret_like_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    hits: list[str] = []
    for idx, line in enumerate(lines, start=1):
        for pattern in SUSPICIOUS_SECRET_PATTERNS:
            if pattern.search(line):
                hits.append(f"{path.name}:{idx}")
                break
    return hits


def test_env_example_no_tiene_claves_reales():
    hits = _find_secret_like_lines(PROJECT_ROOT / ".env.example")
    assert not hits, f"Se detectaron posibles secretos en .env.example: {hits}"


def test_env_no_tiene_claves_reales_en_ci():
    if os.getenv("CI", "").lower() not in {"1", "true", "yes"}:
        return
    env_path = PROJECT_ROOT / ".env"
    hits = _find_secret_like_lines(env_path)
    assert not hits, f"Se detectaron posibles secretos en .env: {hits}"
