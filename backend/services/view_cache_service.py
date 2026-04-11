from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from typing import Any

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


_NAMESPACE = "view:payload:v1"


def _as_bool(value: str | None, default: bool) -> bool:
    txt = str(value or "").strip().lower()
    if not txt:
        return default
    if txt in {"1", "true", "yes", "si", "on"}:
        return True
    if txt in {"0", "false", "no", "off"}:
        return False
    return default


@dataclass
class _MemoryItem:
    expires_at: float
    payload: str


class _InMemoryTTLCache:
    def __init__(self) -> None:
        self._data: dict[str, _MemoryItem] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> str | None:
        now = time.time()
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            if item.expires_at <= now:
                self._data.pop(key, None)
                return None
            return item.payload

    def set(self, key: str, payload: str, ttl_seconds: int) -> None:
        expires_at = time.time() + max(1, ttl_seconds)
        with self._lock:
            self._data[key] = _MemoryItem(expires_at=expires_at, payload=payload)

    def invalidate_prefix(self, prefix: str) -> int:
        with self._lock:
            keys = [k for k in self._data.keys() if k.startswith(prefix)]
            for k in keys:
                self._data.pop(k, None)
            return len(keys)


class _ViewCache:
    def __init__(self) -> None:
        self.enabled = _as_bool(os.getenv("VIEW_CACHE_ENABLED"), default=True)
        self._memory = _InMemoryTTLCache()
        self._redis = None
        self._redis_prefix = f"{_NAMESPACE}:"

        redis_url = str(os.getenv("VIEW_CACHE_REDIS_URL") or os.getenv("REDIS_URL") or "").strip()
        if not self.enabled or not redis_url or redis is None:
            return
        try:
            self._redis = redis.Redis.from_url(  # type: ignore[attr-defined]
                redis_url,
                decode_responses=True,
                socket_connect_timeout=0.8,
                socket_timeout=0.8,
            )
            self._redis.ping()
        except Exception:
            self._redis = None

    def _full_key(self, key: str) -> str:
        return f"{self._redis_prefix}{key}"

    def get(self, key: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        full_key = self._full_key(key)
        payload: str | None = None

        if self._redis is not None:
            try:
                payload = self._redis.get(full_key)
            except Exception:
                payload = None

        if not payload:
            payload = self._memory.get(full_key)
        if not payload:
            return None
        try:
            loaded = json.loads(payload)
        except Exception:
            return None
        return loaded if isinstance(loaded, dict) else None

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        if not self.enabled:
            return
        full_key = self._full_key(key)
        try:
            payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        except Exception:
            return

        if self._redis is not None:
            try:
                self._redis.setex(full_key, max(1, ttl_seconds), payload)
            except Exception:
                self._memory.set(full_key, payload, ttl_seconds)
            return
        self._memory.set(full_key, payload, ttl_seconds)

    def invalidate_prefix(self, prefix: str) -> int:
        if not self.enabled:
            return 0
        full_prefix = self._full_key(prefix)
        removed = self._memory.invalidate_prefix(full_prefix)
        if self._redis is None:
            return removed
        try:
            cursor = 0
            pattern = f"{full_prefix}*"
            while True:
                cursor, keys = self._redis.scan(cursor=cursor, match=pattern, count=200)
                if keys:
                    removed += int(self._redis.delete(*keys) or 0)
                if cursor == 0:
                    break
        except Exception:
            pass
        return removed


_CACHE: _ViewCache | None = None


def _get_cache() -> _ViewCache:
    global _CACHE
    if _CACHE is None:
        _CACHE = _ViewCache()
    return _CACHE


def get_cached_view(cache_key: str) -> dict[str, Any] | None:
    return _get_cache().get(cache_key)


def set_cached_view(cache_key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
    _get_cache().set(cache_key, payload, ttl_seconds)


def invalidate_view_cache_for_cliente(cliente_id: str) -> int:
    cid = str(cliente_id or "").strip()
    if not cid:
        return 0
    removed = 0
    removed += _get_cache().invalidate_prefix(f"dashboard:{cid}:")
    removed += _get_cache().invalidate_prefix(f"risk:{cid}:")
    return removed

