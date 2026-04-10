from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "data" / "catalogos" / "runtime_config.yaml"

DEFAULTS: dict[str, Any] = {
    "risk_engine": {
        "weights": {
            "closing_entries": 3.0,
            "user_spike_factor": 40.0,
            "reversals": 2.0,
            "dormant_accounts": 2.0,
            "tb_mayor_gap_divisor": 8.0,
        },
        "caps": {
            "closing_entries": 12.0,
            "user_spike": 10.0,
            "reversals": 8.0,
            "dormant_accounts": 8.0,
            "tb_mayor_gap": 15.0,
            "mayor_boost_total": 25.0,
        },
    },
    "workflow": {
        "thresholds": {
            "exec_required_completion_pct": 70.0,
            "report_required_completion_pct": 95.0,
        }
    },
    "normativa": {
        "internal_prefixes": [
            "METODOLOGIA_",
            "INTERNAL_",
            "HIDDEN_",
        ]
    },
    "rate_limit": {
        "admin_writes_per_minute": 20,
        "normativa_refresh_per_minute": 3,
    },
}


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def get_runtime_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return DEFAULTS
    try:
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return DEFAULTS
    if not isinstance(data, dict):
        return DEFAULTS
    return _deep_merge(DEFAULTS, data)
