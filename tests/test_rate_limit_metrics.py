from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from backend.auth import create_access_token
from backend.main import app
from backend.middleware.rate_limit import infer_scope_from_path, record_rate_limit_metric


def _auth_headers(*, role: str = "admin") -> dict[str, str]:
    token, _ = create_access_token(
        sub="rate-limit-metrics-tester",
        org_id="org_demo",
        allowed_clientes=["*"],
        role=role,
    )
    return {"Authorization": f"Bearer {token}"}


def test_infer_scope_from_path() -> None:
    assert infer_scope_from_path("/auth/login") == "login"
    assert infer_scope_from_path("/chat/cliente_x") == "chat"
    assert infer_scope_from_path("/api/hallazgos/estructurar") == "hallazgos"
    assert infer_scope_from_path("/clientes/abc/upload/tb") == "uploads"
    assert infer_scope_from_path("/api/admin/users") == "admin"
    assert infer_scope_from_path("/health") is None


def test_admin_rate_limit_metrics_endpoint_returns_snapshot() -> None:
    record_rate_limit_metric("login", "allowed")
    record_rate_limit_metric("login", "blocked")

    client = TestClient(app)
    response = client.get("/api/admin/rate-limit/metrics", headers=_auth_headers(role="admin"))
    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert payload["backend_slowapi"] in {"memory", "redis"}
    assert payload["backend_service"] in {"memory", "redis"}
    assert "snapshot" in payload
    assert "metrics" in payload["snapshot"]
