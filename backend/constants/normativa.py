from __future__ import annotations

from typing import Any

from backend.constants.runtime_config import get_runtime_config


def get_internal_norm_prefixes() -> list[str]:
    cfg = get_runtime_config()
    normativa_cfg = cfg.get("normativa", {}) if isinstance(cfg, dict) else {}
    raw = (
        normativa_cfg.get("internal_prefixes", [])
        if isinstance(normativa_cfg, dict)
        else []
    )
    out: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            txt = str(item or "").strip().upper()
            if txt:
                out.append(txt)
    if not out:
        out = ["METODOLOGIA_"]
    return out


def is_internal_norma(norma: Any) -> bool:
    txt = str(norma or "").strip().upper()
    if not txt:
        return False
    return any(txt.startswith(prefix) for prefix in get_internal_norm_prefixes())

