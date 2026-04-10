from __future__ import annotations

import json
import logging
import os
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_int(value: str | None, default: int, *, minimum: int = 1, maximum: int = 100_000) -> int:
    try:
        parsed = int(str(value or "").strip() or default)
    except Exception:
        parsed = default
    return max(minimum, min(maximum, parsed))


def _pctl(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    sorted_values = sorted(values)
    rank = (len(sorted_values) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = rank - lower
    return float(sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight)


class ObservabilityStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.window_size = _as_int(os.getenv("OBSERVABILITY_WINDOW_SIZE"), 2000)
        self.top_paths = _as_int(os.getenv("OBSERVABILITY_TOP_PATHS"), 25, maximum=200)
        self.log_format = (os.getenv("APP_LOG_FORMAT") or "json").strip().lower()
        self._requests: deque[dict[str, Any]] = deque(maxlen=self.window_size)
        self._errors: dict[str, dict[str, Any]] = {}

    def log(self, logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
        payload = {"ts": _iso_now(), "event": str(event or "event"), **fields}
        if self.log_format == "json":
            logger.log(level, json.dumps(payload, ensure_ascii=False, default=str))
            return
        flat = " ".join(f"{k}={v}" for k, v in payload.items())
        logger.log(level, flat)

    def record_request(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        request_id: str,
    ) -> None:
        row = {
            "ts": _iso_now(),
            "method": str(method or "").upper(),
            "path": str(path or ""),
            "status_code": int(status_code),
            "duration_ms": float(max(duration_ms, 0.0)),
            "request_id": str(request_id or ""),
        }
        with self._lock:
            self._requests.append(row)

    def record_error(
        self,
        *,
        code: str,
        method: str,
        path: str,
        status_code: int,
        request_id: str,
        message: str = "",
    ) -> None:
        key = str(code or "UNKNOWN_ERROR").strip().upper()
        now = _iso_now()
        with self._lock:
            current = self._errors.get(key, {"count": 0})
            current["count"] = int(current.get("count") or 0) + 1
            current["last_seen"] = now
            current["last_method"] = str(method or "").upper()
            current["last_path"] = str(path or "")
            current["last_status_code"] = int(status_code)
            current["last_request_id"] = str(request_id or "")
            if message:
                current["last_message"] = str(message)[:300]
            self._errors[key] = current

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            requests_rows = list(self._requests)
            errors_rows = {k: dict(v) for k, v in self._errors.items()}

        latencies = [float(item.get("duration_ms") or 0.0) for item in requests_rows]
        total_requests = len(requests_rows)
        total_errors = sum(1 for item in requests_rows if int(item.get("status_code") or 0) >= 400)
        error_rate_pct = (total_errors / total_requests * 100.0) if total_requests else 0.0

        by_path: dict[str, dict[str, Any]] = {}
        for item in requests_rows:
            path = str(item.get("path") or "")
            if not path:
                continue
            row = by_path.setdefault(
                path,
                {"path": path, "count": 0, "errors": 0, "durations": []},
            )
            row["count"] += 1
            if int(item.get("status_code") or 0) >= 400:
                row["errors"] += 1
            row["durations"].append(float(item.get("duration_ms") or 0.0))

        paths_out: list[dict[str, Any]] = []
        for row in by_path.values():
            durations = [float(x) for x in row.get("durations", [])]
            count = int(row.get("count") or 0)
            errors = int(row.get("errors") or 0)
            avg = (sum(durations) / count) if count else 0.0
            paths_out.append(
                {
                    "path": row.get("path"),
                    "count": count,
                    "errors": errors,
                    "error_rate_pct": round((errors / count * 100.0), 2) if count else 0.0,
                    "avg_ms": round(avg, 2),
                    "p95_ms": round(_pctl(durations, 0.95), 2),
                    "max_ms": round(max(durations) if durations else 0.0, 2),
                }
            )
        paths_out.sort(key=lambda x: int(x.get("count") or 0), reverse=True)

        errors_out: list[dict[str, Any]] = []
        for code, row in errors_rows.items():
            errors_out.append(
                {
                    "code": code,
                    "count": int(row.get("count") or 0),
                    "last_seen": str(row.get("last_seen") or ""),
                    "last_method": str(row.get("last_method") or ""),
                    "last_path": str(row.get("last_path") or ""),
                    "last_status_code": int(row.get("last_status_code") or 0),
                    "last_request_id": str(row.get("last_request_id") or ""),
                    "last_message": str(row.get("last_message") or ""),
                }
            )
        errors_out.sort(key=lambda x: int(x.get("count") or 0), reverse=True)

        latency_avg = (sum(latencies) / len(latencies)) if latencies else 0.0

        return {
            "window_size": self.window_size,
            "captured_requests": total_requests,
            "totals": {
                "requests": total_requests,
                "errors": total_errors,
                "error_rate_pct": round(error_rate_pct, 2),
            },
            "latency_ms": {
                "avg": round(latency_avg, 2),
                "p50": round(_pctl(latencies, 0.50), 2),
                "p95": round(_pctl(latencies, 0.95), 2),
                "max": round(max(latencies) if latencies else 0.0, 2),
            },
            "by_path": paths_out[: self.top_paths],
            "errors_by_code": errors_out,
        }


store = ObservabilityStore()
