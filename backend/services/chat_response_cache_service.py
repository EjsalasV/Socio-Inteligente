"""
Servicio de caché para respuestas completas de chat RAG.

Almacena respuestas generadas por el LLM con TTL configurable.
Usa Redis si está disponible, fallback a in-memory dict con TTL.
"""

from __future__ import annotations

import hashlib
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


_NAMESPACE = "rag:responses:v1"


def _as_bool(value: str | None, default: bool) -> bool:
    txt = str(value or "").strip().lower()
    if not txt:
        return default
    if txt in {"1", "true", "yes", "si", "on"}:
        return True
    if txt in {"0", "false", "no", "off"}:
        return False
    return default


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _cache_ttl_seconds() -> int:
    raw = str(os.getenv("CHAT_RESPONSE_CACHE_TTL_SECONDS") or "3600").strip()
    try:
        parsed = int(raw)
    except Exception:
        parsed = 3600
    return max(30, min(parsed, 86400))


def build_response_cache_key(
    cliente_id: str,
    query: str,
    mode: str = "chat",
) -> str:
    """Construye clave única para la respuesta usando SHA256."""
    normalized_cliente = _normalize_text(cliente_id) or "global"
    payload = {
        "cliente_id": normalized_cliente,
        "query": _normalize_text(query),
        "mode": str(mode or "chat").strip().lower(),
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{normalized_cliente}:{mode}:{digest[:16]}"


@dataclass
class _MemoryItem:
    expires_at: float
    payload: str


class _InMemoryTTLCache:
    """Caché en memoria con expiración por TTL."""

    def __init__(self, max_entries: int = 1000) -> None:
        self._data: dict[str, _MemoryItem] = {}
        self._lock = threading.Lock()
        self._max_entries = max_entries

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
            if len(self._data) >= self._max_entries:
                now = time.time()
                expired_keys = [k for k, v in self._data.items() if v.expires_at <= now]
                for k in expired_keys:
                    self._data.pop(k, None)
            if len(self._data) >= self._max_entries:
                return
            self._data[key] = _MemoryItem(expires_at=expires_at, payload=payload)

    def invalidate_prefix(self, prefix: str) -> int:
        with self._lock:
            targets = [k for k in self._data.keys() if k.startswith(prefix)]
            for key in targets:
                self._data.pop(key, None)
            return len(targets)


class _ChatResponseCache:
    """Caché de respuestas de chat con Redis o fallback en-memory."""

    def __init__(self) -> None:
        self.enabled = _as_bool(os.getenv("CHAT_RESPONSE_CACHE_ENABLED"), default=True)
        self.ttl_seconds = _cache_ttl_seconds()
        self._memory = _InMemoryTTLCache(max_entries=1000)
        self._redis = None
        self._redis_prefix = f"{_NAMESPACE}:"

        redis_url = str(os.getenv("CHAT_RESPONSE_CACHE_REDIS_URL") or os.getenv("REDIS_URL") or "").strip()
        if not self.enabled or not redis_url or redis is None:
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

    def _full_key(self, cache_key: str) -> str:
        return f"{self._redis_prefix}{cache_key}"

    def get(self, cache_key: str) -> dict[str, Any] | None:
        """Retorna respuesta cacheada o None."""
        if not self.enabled:
            return None
        full_key = self._full_key(cache_key)

        if self._redis is not None:
            try:
                payload = self._redis.get(full_key)
                if payload:
                    loaded = json.loads(payload)
                    if isinstance(loaded, dict):
                        return loaded
            except Exception:
                pass

        payload = self._memory.get(full_key)
        if not payload:
            return None
        try:
            loaded = json.loads(payload)
        except Exception:
            return None
        return loaded if isinstance(loaded, dict) else None

    def set(self, cache_key: str, value: dict[str, Any]) -> None:
        """Guarda respuesta en caché."""
        if not self.enabled:
            return
        full_key = self._full_key(cache_key)
        try:
            payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        except Exception:
            return

        if self._redis is not None:
            try:
                self._redis.setex(full_key, self.ttl_seconds, payload)
            except Exception:
                # Fallback a memoria si Redis no disponible
                self._memory.set(full_key, payload, self.ttl_seconds)
            return

        self._memory.set(full_key, payload, self.ttl_seconds)

    def invalidate_prefix(self, prefix: str) -> int:
        """Invalida todas las claves con un prefijo."""
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


_CACHE: _ChatResponseCache | None = None


def _get_cache() -> _ChatResponseCache:
    global _CACHE
    if _CACHE is None:
        _CACHE = _ChatResponseCache()
    return _CACHE


def get_cached_response(cache_key: str) -> dict[str, Any] | None:
    """Obtiene respuesta cacheada si existe y no expiró."""
    return _get_cache().get(cache_key)


def set_cached_response(cache_key: str, response: dict[str, Any]) -> None:
    """Guarda respuesta en caché."""
    _get_cache().set(cache_key, response)


def invalidate_chat_cache_for_cliente(cliente_id: str) -> int:
    """Invalida todas las respuestas cacheadas para un cliente."""
    normalized_cliente = _normalize_text(cliente_id)
    if not normalized_cliente:
        return 0
    return _get_cache().invalidate_prefix(f"{normalized_cliente}:")


def invalidate_chat_cache_all() -> int:
    """Invalida todo el caché de respuestas."""
    return _get_cache().invalidate_prefix("")


def reset_chat_response_cache_for_tests() -> None:
    """Reset para testing."""
    global _CACHE
    _CACHE = _ChatResponseCache()
