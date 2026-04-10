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
except Exception:  # pragma: no cover - fallback when dependency is unavailable
    redis = None  # type: ignore


_NAMESPACE = "rag:chunks:v1"


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


def _normalize_temas(value: str | list[str] | None) -> list[str]:
    if isinstance(value, str):
        normalized = _normalize_text(value)
        return [normalized] if normalized else []
    if isinstance(value, list):
        out = {_normalize_text(item) for item in value}
        return sorted([item for item in out if item])
    return []


def _cache_ttl_seconds() -> int:
    raw = str(os.getenv("RAG_CACHE_TTL_SECONDS") or "3600").strip()
    try:
        parsed = int(raw)
    except Exception:
        parsed = 3600
    return max(30, min(parsed, 86400))


def build_rag_cache_key(
    *,
    cliente_id: str,
    query: str,
    top_k: int,
    marco: str | None = None,
    etapa: str | None = None,
    afirmacion: str | None = None,
    tipo: str | None = None,
    temas: str | list[str] | None = None,
    index_signature: str = "",
) -> str:
    normalized_cliente = _normalize_text(cliente_id) or "global"
    payload = {
        "cliente_id": normalized_cliente,
        "query": _normalize_text(query),
        "top_k": int(top_k),
        "marco": _normalize_text(marco),
        "etapa": _normalize_text(etapa),
        "afirmacion": _normalize_text(afirmacion),
        "tipo": _normalize_text(tipo),
        "temas": _normalize_temas(temas),
        "index_signature": str(index_signature or "").strip(),
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha1(canonical.encode("utf-8")).hexdigest()
    return f"{normalized_cliente}:{digest}"


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
            targets = [k for k in self._data.keys() if k.startswith(prefix)]
            for key in targets:
                self._data.pop(key, None)
            return len(targets)


class _RagContextCache:
    def __init__(self) -> None:
        self.enabled = _as_bool(os.getenv("RAG_CACHE_ENABLED"), default=True)
        self.ttl_seconds = _cache_ttl_seconds()
        self._memory = _InMemoryTTLCache()
        self._redis = None
        self._redis_prefix = f"{_NAMESPACE}:"

        redis_url = str(os.getenv("RAG_CACHE_REDIS_URL") or os.getenv("REDIS_URL") or "").strip()
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

    def get(self, cache_key: str) -> list[dict[str, Any]] | None:
        if not self.enabled:
            return None
        full_key = self._full_key(cache_key)

        if self._redis is not None:
            try:
                payload = self._redis.get(full_key)
                if payload:
                    loaded = json.loads(payload)
                    if isinstance(loaded, list):
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
        return loaded if isinstance(loaded, list) else None

    def set(self, cache_key: str, value: list[dict[str, Any]]) -> None:
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
                # Fallback local when Redis is unavailable.
                self._memory.set(full_key, payload, self.ttl_seconds)
            return

        self._memory.set(full_key, payload, self.ttl_seconds)

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


_CACHE: _RagContextCache | None = None


def _get_cache() -> _RagContextCache:
    global _CACHE
    if _CACHE is None:
        _CACHE = _RagContextCache()
    return _CACHE


def get_cached_chunks(cache_key: str) -> list[dict[str, Any]] | None:
    return _get_cache().get(cache_key)


def set_cached_chunks(cache_key: str, chunks: list[dict[str, Any]]) -> None:
    _get_cache().set(cache_key, chunks)


def invalidate_rag_cache_for_cliente(cliente_id: str) -> int:
    normalized_cliente = _normalize_text(cliente_id)
    if not normalized_cliente:
        return 0
    return _get_cache().invalidate_prefix(f"{normalized_cliente}:")


def invalidate_rag_cache_all() -> int:
    return _get_cache().invalidate_prefix("")


def reset_rag_cache_for_tests() -> None:
    global _CACHE
    _CACHE = _RagContextCache()
