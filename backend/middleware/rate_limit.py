"""Rate limiting middleware configuration (Redis-aware).

This module configures slowapi to use Redis when available and falls back to
in-memory storage in local/dev scenarios.
"""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from slowapi import Limiter
from slowapi.util import get_remote_address

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency in local dev
    redis = None  # type: ignore


def _rate_limit_key(request) -> str:
    """Use X-Forwarded-For first when app is behind proxies."""
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        first_ip = forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip
    return get_remote_address(request)


def _storage_uri() -> str:
    explicit = str(os.getenv("RATE_LIMIT_STORAGE_URI") or "").strip()
    if explicit:
        return explicit
    redis_url = str(os.getenv("RATE_LIMIT_REDIS_URL") or os.getenv("REDIS_URL") or "").strip()
    if redis_url and redis is not None:
        try:
            probe = redis.Redis.from_url(  # type: ignore[attr-defined]
                redis_url,
                decode_responses=True,
                socket_connect_timeout=0.35,
                socket_timeout=0.35,
            )
            probe.ping()
            return redis_url
        except Exception:
            pass
    return "memory://"


_ACTIVE_STORAGE_URI = _storage_uri()

# Global slowapi limiter.
limiter = Limiter(
    key_func=_rate_limit_key,
    storage_uri=_ACTIVE_STORAGE_URI,
)

# Common endpoint limits.
LIMITS = {
    "login": "5/minute",
    "chat": "20/minute",
    "hallazgos": "10/minute",
    "uploads": "3/minute",
    "admin": "1/minute",
}


class _RateLimitMetricsStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._local: dict[str, int] = defaultdict(int)
        self._redis = None
        self._redis_prefix = "rate_limit:metrics:v1"
        self._active_date = datetime.now(timezone.utc).date().isoformat()
        redis_url = str(os.getenv("RATE_LIMIT_REDIS_URL") or os.getenv("REDIS_URL") or "").strip()
        if not redis_url or redis is None:
            return
        try:
            self._redis = redis.Redis.from_url(  # type: ignore[attr-defined]
                redis_url,
                decode_responses=True,
                socket_connect_timeout=1.0,
                socket_timeout=1.0,
            )
            self._redis.ping()
        except Exception:
            self._redis = None

    def _key(self, scope: str, outcome: str) -> str:
        day = datetime.now(timezone.utc).date().isoformat()
        return f"{self._redis_prefix}:{day}:{scope}:{outcome}"

    def increment(self, scope: str, outcome: str) -> None:
        normalized_scope = str(scope or "unknown").strip().lower() or "unknown"
        normalized_outcome = str(outcome or "unknown").strip().lower() or "unknown"
        key = self._key(normalized_scope, normalized_outcome)
        if self._redis is not None:
            try:
                pipe = self._redis.pipeline()
                pipe.incr(key, 1)
                pipe.expire(key, 7 * 24 * 3600)
                pipe.execute()
                return
            except Exception:
                pass
        with self._lock:
            self._local[key] += 1

    def snapshot(self) -> dict[str, Any]:
        day = datetime.now(timezone.utc).date().isoformat()
        prefix = f"{self._redis_prefix}:{day}:"
        out: dict[str, Any] = {"date": day, "storage": "memory", "metrics": {}}
        if self._redis is not None:
            try:
                keys = self._redis.keys(f"{prefix}*")
                metrics: dict[str, int] = {}
                if keys:
                    values = self._redis.mget(keys)
                    for raw_key, raw_value in zip(keys, values):
                        key = str(raw_key)
                        value = int(raw_value or 0)
                        parts = key.split(":")
                        if len(parts) < 6:
                            continue
                        scope = parts[-2]
                        outcome = parts[-1]
                        metrics[f"{scope}.{outcome}"] = value
                out["storage"] = "redis"
                out["metrics"] = metrics
                return out
            except Exception:
                pass
        with self._lock:
            metrics: dict[str, int] = {}
            for key, value in self._local.items():
                if not key.startswith(prefix):
                    continue
                parts = key.split(":")
                if len(parts) < 6:
                    continue
                scope = parts[-2]
                outcome = parts[-1]
                metrics[f"{scope}.{outcome}"] = int(value)
            out["metrics"] = metrics
            return out


_METRICS = _RateLimitMetricsStore()


def infer_scope_from_path(path: str) -> str | None:
    normalized = str(path or "").strip().lower()
    if normalized.startswith("/auth/login"):
        return "login"
    if normalized.startswith("/chat/"):
        return "chat"
    if normalized.startswith("/api/hallazgos/"):
        return "hallazgos"
    if normalized.startswith("/clientes/") and "/upload" in normalized:
        return "uploads"
    if normalized.startswith("/api/admin/"):
        return "admin"
    return None


def record_rate_limit_metric(scope: str, outcome: str) -> None:
    _METRICS.increment(scope, outcome)


def get_rate_limit_metrics_snapshot() -> dict[str, Any]:
    return _METRICS.snapshot()


def rate_limit_backend_name() -> str:
    if _ACTIVE_STORAGE_URI.startswith("redis"):
        return "redis"
    return "memory"
