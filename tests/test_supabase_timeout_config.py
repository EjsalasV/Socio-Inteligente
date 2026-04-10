from __future__ import annotations

from typing import Any

import requests

from backend.repositories.supabase_memory import SupabaseMemoryStore


class _FakeResponse:
    def __init__(self, *, status_code: int, text: str, payload: Any) -> None:
        self.status_code = status_code
        self.text = text
        self._payload = payload

    def json(self) -> Any:
        return self._payload


def _set_base_env(monkeypatch) -> None:
    monkeypatch.setenv("USE_SUPABASE_MEMORY", "1")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-key")


def test_supabase_uses_connect_and_read_timeout_env(monkeypatch):
    _set_base_env(monkeypatch)
    monkeypatch.setenv("SUPABASE_TIMEOUT_SECONDS", "8")
    monkeypatch.setenv("SUPABASE_TIMEOUT_CONNECT_SECONDS", "1.5")
    monkeypatch.setenv("SUPABASE_TIMEOUT_READ_SECONDS", "3.5")
    monkeypatch.setenv("SUPABASE_MAX_RETRIES", "0")

    captured_timeout = {"value": None}

    def fake_request(*args, **kwargs):
        captured_timeout["value"] = kwargs.get("timeout")
        return _FakeResponse(status_code=200, text="[]", payload=[])

    monkeypatch.setattr(requests, "request", fake_request)
    store = SupabaseMemoryStore()

    rows = store.fetch_rows("users")
    assert rows == []
    assert captured_timeout["value"] == (1.5, 3.5)


def test_supabase_opens_circuit_and_degrades_to_local(monkeypatch):
    _set_base_env(monkeypatch)
    monkeypatch.setenv("SUPABASE_MAX_RETRIES", "0")
    monkeypatch.setenv("SUPABASE_CIRCUIT_FAIL_THRESHOLD", "1")
    monkeypatch.setenv("SUPABASE_CIRCUIT_OPEN_SECONDS", "60")

    called = {"count": 0}

    def failing_request(*args, **kwargs):
        called["count"] += 1
        raise requests.Timeout("simulated timeout")

    monkeypatch.setattr(requests, "request", failing_request)
    store = SupabaseMemoryStore()

    first = store.fetch_rows("users")
    assert first == []
    assert called["count"] == 1

    # Circuit is open: should not call requests again, returns fallback result fast.
    second = store.fetch_rows("users")
    assert second == []
    assert called["count"] == 1


def test_supabase_retries_once_then_recovers(monkeypatch):
    _set_base_env(monkeypatch)
    monkeypatch.setenv("SUPABASE_MAX_RETRIES", "1")
    monkeypatch.setenv("SUPABASE_RETRY_BACKOFF_SECONDS", "0")
    monkeypatch.setenv("SUPABASE_CIRCUIT_FAIL_THRESHOLD", "10")

    called = {"count": 0}

    def flaky_request(*args, **kwargs):
        called["count"] += 1
        if called["count"] == 1:
            raise requests.Timeout("first attempt fails")
        return _FakeResponse(status_code=200, text='[{"cliente_id":"demo"}]', payload=[{"cliente_id": "demo"}])

    monkeypatch.setattr(requests, "request", flaky_request)
    store = SupabaseMemoryStore()

    clientes = store.list_clientes()
    assert clientes == ["demo"]
    assert called["count"] == 2
