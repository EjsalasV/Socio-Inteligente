from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency in local dev
    redis = None  # type: ignore


@dataclass
class RateLimitExceeded(Exception):
    retry_after_seconds: int
    limit: int
    window_seconds: int


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def enforce(
        self,
        *,
        scope: str,
        subject: str,
        limit: int,
        window_seconds: int,
    ) -> None:
        if limit <= 0 or window_seconds <= 0:
            return
        now = time.time()
        key = (scope, subject)
        with self._lock:
            bucket = self._events[key]
            while bucket and (now - bucket[0]) > window_seconds:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0])))
                raise RateLimitExceeded(
                    retry_after_seconds=retry_after,
                    limit=limit,
                    window_seconds=window_seconds,
                )
            bucket.append(now)


class RedisBackedRateLimiter:
    _SCRIPT = """
    local key = KEYS[1]
    local now_ms = tonumber(ARGV[1])
    local window_ms = tonumber(ARGV[2])
    local limit = tonumber(ARGV[3])
    local member = ARGV[4]

    redis.call("ZREMRANGEBYSCORE", key, 0, now_ms - window_ms)
    local count = redis.call("ZCARD", key)
    if count >= limit then
      local oldest = redis.call("ZRANGE", key, 0, 0, "WITHSCORES")
      local retry = 1
      if oldest[2] ~= nil then
        retry = math.ceil((window_ms - (now_ms - tonumber(oldest[2]))) / 1000)
        if retry < 1 then retry = 1 end
      end
      return {0, retry, count}
    end

    redis.call("ZADD", key, now_ms, member)
    redis.call("EXPIRE", key, math.ceil(window_ms / 1000) + 2)
    return {1, 0, count + 1}
    """

    def __init__(self, redis_url: str) -> None:
        self._redis = redis.Redis.from_url(  # type: ignore[attr-defined]
            redis_url,
            decode_responses=True,
            socket_connect_timeout=1.0,
            socket_timeout=1.0,
        )
        self._redis.ping()
        self._key_prefix = "rate_limit:service:v1"
        self._sha = self._redis.script_load(self._SCRIPT)

    def enforce(
        self,
        *,
        scope: str,
        subject: str,
        limit: int,
        window_seconds: int,
    ) -> None:
        if limit <= 0 or window_seconds <= 0:
            return
        normalized_scope = str(scope or "unknown").strip().lower() or "unknown"
        normalized_subject = str(subject or "anonymous").strip().lower() or "anonymous"
        key = f"{self._key_prefix}:{normalized_scope}:{normalized_subject}"
        now_ms = int(time.time() * 1000)
        window_ms = int(window_seconds * 1000)
        member = f"{now_ms}:{time.time_ns()}"
        result = self._redis.evalsha(
            self._sha,
            1,
            key,
            str(now_ms),
            str(window_ms),
            str(limit),
            member,
        )
        allowed = int(result[0]) if isinstance(result, (list, tuple)) and len(result) > 0 else 1
        if allowed == 1:
            return
        retry_after = int(result[1]) if isinstance(result, (list, tuple)) and len(result) > 1 else 1
        raise RateLimitExceeded(
            retry_after_seconds=max(1, retry_after),
            limit=limit,
            window_seconds=window_seconds,
        )


class HybridRateLimiter:
    def __init__(self) -> None:
        self._memory = InMemoryRateLimiter()
        self._redis_limiter = None
        self._backend = "memory"

        redis_url = str(os.getenv("RATE_LIMIT_REDIS_URL") or os.getenv("REDIS_URL") or "").strip()
        if not redis_url or redis is None:
            return
        try:
            self._redis_limiter = RedisBackedRateLimiter(redis_url)
            self._backend = "redis"
        except Exception:
            self._redis_limiter = None
            self._backend = "memory"

    def enforce(
        self,
        *,
        scope: str,
        subject: str,
        limit: int,
        window_seconds: int,
    ) -> None:
        if self._redis_limiter is not None:
            try:
                self._redis_limiter.enforce(
                    scope=scope,
                    subject=subject,
                    limit=limit,
                    window_seconds=window_seconds,
                )
                return
            except RateLimitExceeded:
                raise
            except Exception:
                pass
        self._memory.enforce(
            scope=scope,
            subject=subject,
            limit=limit,
            window_seconds=window_seconds,
        )

    @property
    def backend(self) -> str:
        return self._backend


rate_limiter = HybridRateLimiter()
