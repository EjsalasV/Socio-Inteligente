from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
METRICS_DIR = ROOT / "data" / "metrics"
METRICS_EVENTS = METRICS_DIR / "events.jsonl"


def record_metric_event(event_type: str, *, cliente_id: str = "", area_codigo: str = "", payload: dict[str, Any] | None = None) -> None:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": str(event_type or "").strip(),
        "cliente_id": str(cliente_id or "").strip(),
        "area_codigo": str(area_codigo or "").strip(),
        "payload": payload or {},
    }
    with METRICS_EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_metric_events() -> list[dict[str, Any]]:
    if not METRICS_EVENTS.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in METRICS_EVENTS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out
