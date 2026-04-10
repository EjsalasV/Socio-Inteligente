from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from backend.main import app


def test_not_found_returns_structured_error_envelope() -> None:
    client = TestClient(app)
    response = client.get("/ruta/inexistente")
    assert response.status_code == 404
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["code"] == "HTTP_404"
    assert isinstance(payload.get("message"), str) and payload["message"]
    assert "action_hint" in payload
    assert "retryable" in payload
    assert isinstance(payload.get("details"), dict)


def test_validation_error_returns_structured_error_envelope() -> None:
    client = TestClient(app)
    response = client.post("/auth/login", json={"username": "demo"})
    assert response.status_code == 422
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["code"] == "VALIDATION_ERROR"
    assert isinstance(payload.get("details"), dict)
    assert "errors" in payload["details"]
