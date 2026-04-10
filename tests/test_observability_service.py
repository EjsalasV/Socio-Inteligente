from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from backend.auth import create_access_token
from backend.main import app
from backend.services.observability_service import ObservabilityStore


def _admin_headers() -> dict[str, str]:
    token, _ = create_access_token(
        sub="observability-admin",
        org_id="org_demo",
        allowed_clientes=["*"],
        role="admin",
    )
    return {"Authorization": f"Bearer {token}"}


def test_observability_store_aggregates_requests_and_errors() -> None:
    store = ObservabilityStore()
    store.record_request(method="GET", path="/health", status_code=200, duration_ms=30, request_id="r1")
    store.record_request(method="GET", path="/health", status_code=500, duration_ms=120, request_id="r2")
    store.record_request(method="POST", path="/api/admin/users", status_code=403, duration_ms=80, request_id="r3")
    store.record_error(
        code="INTERNAL_SERVER_ERROR",
        method="GET",
        path="/health",
        status_code=500,
        request_id="r2",
        message="boom",
    )
    snapshot = store.snapshot()

    assert snapshot["totals"]["requests"] == 3
    assert snapshot["totals"]["errors"] == 2
    assert snapshot["latency_ms"]["p95"] >= snapshot["latency_ms"]["p50"]
    assert any(item["path"] == "/health" for item in snapshot["by_path"])
    assert any(item["code"] == "INTERNAL_SERVER_ERROR" for item in snapshot["errors_by_code"])


def test_admin_rate_limit_metrics_includes_observability_snapshot() -> None:
    client = TestClient(app)
    response = client.get("/api/admin/rate-limit/metrics", headers=_admin_headers())
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "ok"
    data = payload.get("data") or {}
    observability = data.get("observability") or {}
    assert isinstance(observability.get("totals"), dict)
    assert isinstance(observability.get("latency_ms"), dict)
    assert isinstance(observability.get("by_path"), list)
