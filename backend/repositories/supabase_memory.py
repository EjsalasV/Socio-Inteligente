from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any

import requests

LOGGER = logging.getLogger("socio_ai.supabase_memory")


def _as_float(raw: str | None, default: float, *, minimum: float = 0.0) -> float:
    try:
        parsed = float(str(raw or "").strip() or default)
    except Exception:
        parsed = default
    if parsed < minimum:
        return minimum
    return parsed


def _as_int(raw: str | None, default: int, *, minimum: int = 0) -> int:
    try:
        parsed = int(str(raw or "").strip() or default)
    except Exception:
        parsed = default
    if parsed < minimum:
        return minimum
    return parsed


class SupabaseMemoryStore:
    def __init__(self) -> None:
        self.url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
        self.service_key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
        self.enabled = (os.getenv("USE_SUPABASE_MEMORY") or "0").strip().lower() in {"1", "true", "yes"}

        # Legacy single timeout stays supported.
        legacy_timeout = _as_float(os.getenv("SUPABASE_TIMEOUT_SECONDS"), 8.0, minimum=0.2)
        self.timeout_connect_seconds = _as_float(
            os.getenv("SUPABASE_TIMEOUT_CONNECT_SECONDS"),
            min(legacy_timeout, 2.0),
            minimum=0.1,
        )
        self.timeout_read_seconds = _as_float(
            os.getenv("SUPABASE_TIMEOUT_READ_SECONDS"),
            legacy_timeout,
            minimum=0.2,
        )
        self.timeout = legacy_timeout
        self.request_timeout = (self.timeout_connect_seconds, self.timeout_read_seconds)

        self.max_retries = _as_int(os.getenv("SUPABASE_MAX_RETRIES"), 1, minimum=0)
        self.retry_backoff_seconds = _as_float(os.getenv("SUPABASE_RETRY_BACKOFF_SECONDS"), 0.15, minimum=0.0)

        # Circuit breaker to degrade fast to local filesystem when Supabase is slow/unavailable.
        self.circuit_fail_threshold = _as_int(os.getenv("SUPABASE_CIRCUIT_FAIL_THRESHOLD"), 3, minimum=1)
        self.circuit_open_seconds = _as_float(os.getenv("SUPABASE_CIRCUIT_OPEN_SECONDS"), 30.0, minimum=1.0)
        self._failure_streak = 0
        self._open_until_monotonic = 0.0
        self._lock = threading.Lock()

    def is_configured(self) -> bool:
        return self._has_static_config() and not self._is_circuit_open()

    def _has_static_config(self) -> bool:
        return self.enabled and bool(self.url) and bool(self.service_key)

    @property
    def _base(self) -> str:
        return f"{self.url}/rest/v1"

    def _headers(self, *, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def _is_circuit_open(self) -> bool:
        with self._lock:
            if self._open_until_monotonic <= 0:
                return False
            if time.monotonic() >= self._open_until_monotonic:
                self._open_until_monotonic = 0.0
                self._failure_streak = 0
                return False
            return True

    def _mark_success(self) -> None:
        with self._lock:
            self._failure_streak = 0
            self._open_until_monotonic = 0.0

    def _mark_failure(self, reason: str) -> None:
        with self._lock:
            self._failure_streak += 1
            if self._failure_streak < self.circuit_fail_threshold:
                return
            self._open_until_monotonic = time.monotonic() + self.circuit_open_seconds
            LOGGER.warning(
                "supabase_memory.circuit_open reason=%s failures=%s open_for_s=%s",
                reason,
                self._failure_streak,
                self.circuit_open_seconds,
            )

    def _send(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any | None = None,
        prefer: str | None = None,
        expect_json: bool = True,
    ) -> tuple[bool, Any | None]:
        if not self._has_static_config():
            return False, None
        if self._is_circuit_open():
            return False, None

        attempts = 1 + self.max_retries
        for attempt in range(attempts):
            try:
                resp = requests.request(
                    method=method,
                    url=f"{self._base}/{path}",
                    params=params,
                    data=json.dumps(body) if body is not None else None,
                    headers=self._headers(prefer=prefer),
                    timeout=self.request_timeout,
                )
            except requests.Timeout:
                if attempt < attempts - 1:
                    time.sleep(self.retry_backoff_seconds * (attempt + 1))
                    continue
                self._mark_failure("timeout")
                return False, None
            except requests.RequestException:
                if attempt < attempts - 1:
                    time.sleep(self.retry_backoff_seconds * (attempt + 1))
                    continue
                self._mark_failure("request_exception")
                return False, None

            status = int(resp.status_code)
            if status >= 500 or status in {408, 429}:
                if attempt < attempts - 1:
                    time.sleep(self.retry_backoff_seconds * (attempt + 1))
                    continue
                self._mark_failure(f"status_{status}")
                return False, None
            if status >= 400:
                self._mark_failure(f"status_{status}")
                return False, None

            if not expect_json:
                self._mark_success()
                return True, None

            text = str(resp.text or "").strip()
            if not text:
                self._mark_success()
                return True, None
            try:
                payload = resp.json()
            except Exception:
                self._mark_failure("invalid_json")
                return False, None
            self._mark_success()
            return True, payload

        self._mark_failure("retry_exhausted")
        return False, None

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any | None = None,
    ) -> Any:
        ok, payload = self._send(
            method,
            path,
            params=params,
            body=body,
            prefer="return=representation",
            expect_json=True,
        )
        if not ok:
            return None
        return payload

    def fetch_single_json(self, table: str, filters: dict[str, str], json_field: str) -> dict[str, Any] | None:
        params = {"select": json_field, "limit": "1"}
        for key, value in filters.items():
            params[key] = f"eq.{value}"
        result = self._request("GET", table, params=params)
        if not isinstance(result, list) or not result:
            return None
        row = result[0] if isinstance(result[0], dict) else {}
        payload = row.get(json_field)
        return payload if isinstance(payload, dict) else None

    def fetch_rows(self, table: str, *, filters: dict[str, str] | None = None, select: str = "*") -> list[dict[str, Any]]:
        params: dict[str, str] = {"select": select}
        for key, value in (filters or {}).items():
            params[key] = f"eq.{value}"
        result = self._request("GET", table, params=params)
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]

    def upsert_row(self, table: str, payload: dict[str, Any], *, on_conflict: str) -> bool:
        ok, _ = self._send(
            "POST",
            table,
            params={"on_conflict": on_conflict},
            body=payload,
            prefer="resolution=merge-duplicates,return=representation",
            expect_json=False,
        )
        return ok

    def delete_where(self, table: str, filters: dict[str, str]) -> bool:
        params = {k: f"eq.{v}" for k, v in filters.items()}
        ok, _ = self._send(
            "DELETE",
            table,
            params=params,
            expect_json=False,
        )
        return ok

    def list_clientes(self) -> list[str]:
        params = {"select": "cliente_id", "order": "cliente_id.asc"}
        result = self._request("GET", "clientes", params=params)
        if not isinstance(result, list):
            return []
        out: list[str] = []
        for row in result:
            if isinstance(row, dict):
                cid = str(row.get("cliente_id") or "").strip()
                if cid:
                    out.append(cid)
        return out


store = SupabaseMemoryStore()
