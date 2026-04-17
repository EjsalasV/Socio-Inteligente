from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from backend.auth import create_access_token
from backend.main import app


def _bearer(*, role: str = "staff", allowed_clientes: list[str] | None = None) -> dict[str, str]:
    token, _ = create_access_token(
        sub="security-tester",
        org_id="org_demo",
        allowed_clientes=allowed_clientes or ["cliente_demo"],
        role=role,
    )
    return {"Authorization": f"Bearer {token}"}


def test_protected_endpoint_requires_bearer_token() -> None:
    client = TestClient(app)
    res = client.get("/api/clientes")
    assert res.status_code == 401
    assert "Falta token bearer o cookie de sesion" in res.text


def test_invalid_token_is_rejected() -> None:
    client = TestClient(app)
    res = client.get("/api/clientes", headers={"Authorization": "Bearer invalid.token.value"})
    assert res.status_code == 401


def test_forbidden_when_cliente_not_allowed(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setenv("ALLOWED_CLIENTES", "cliente_autorizado")
    headers = _bearer(role="staff", allowed_clientes=["cliente_autorizado"])
    res = client.get("/perfil/cliente_no_autorizado", headers=headers)
    assert res.status_code == 403


def test_role_escalation_in_payload_is_ignored() -> None:
    client = TestClient(app)
    headers = _bearer(role="staff", allowed_clientes=["*"])
    payload = {"nombre": "Cliente X", "sector": "Retail", "role": "admin"}
    res = client.post("/api/clientes", headers=headers, json=payload)
    assert res.status_code == 403
    assert "Solo perfiles administradores" in res.text


def test_malicious_source_type_payload_is_rejected() -> None:
    client = TestClient(app)
    headers = _bearer(role="senior", allowed_clientes=["*"])
    payload = {
        "source_type": "'; DROP TABLE document_section_links; --",
        "source_id": "x1",
        "reference": "ref",
        "label": "ataque",
    }
    res = client.post(
        "/reportes/cliente_demo/documentos/carta_control_interno/secciones/hallazgo:OBS-01/evidencia",
        headers=headers,
        json=payload,
    )
    assert res.status_code == 422
    assert "source_type inv" in res.text


def test_cors_allows_configured_origin_and_blocks_unknown_origin() -> None:
    client = TestClient(app)

    allowed = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed.status_code in {200, 204}
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"

    blocked = client.options(
        "/health",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert blocked.status_code in {200, 400}
    assert blocked.headers.get("access-control-allow-origin") != "https://evil.example.com"


def test_cookie_auth_requires_csrf_for_mutation() -> None:
    client = TestClient(app)
    token, _ = create_access_token(
        sub="csrf-user",
        org_id="org_demo",
        allowed_clientes=["*"],
        role="staff",
        csrf_token="csrf-123",
    )
    res = client.post(
        "/api/clientes",
        cookies={"socio-auth": token},
        json={"nombre": "Cliente CSRF", "sector": "Retail"},
    )
    assert res.status_code == 403
    assert "CSRF_MISSING" in res.text


def test_cookie_auth_rejects_invalid_csrf_for_mutation() -> None:
    client = TestClient(app)
    token, _ = create_access_token(
        sub="csrf-user",
        org_id="org_demo",
        allowed_clientes=["*"],
        role="staff",
        csrf_token="csrf-123",
    )
    res = client.post(
        "/api/clientes",
        cookies={"socio-auth": token},
        headers={"X-CSRF-Token": "invalid"},
        json={"nombre": "Cliente CSRF", "sector": "Retail"},
    )
    assert res.status_code == 403
    assert "CSRF_INVALID" in res.text


def test_cookie_auth_accepts_valid_csrf_and_reaches_authorization_layer() -> None:
    client = TestClient(app)
    token, _ = create_access_token(
        sub="csrf-user",
        org_id="org_demo",
        allowed_clientes=["*"],
        role="staff",
        csrf_token="csrf-ok",
    )
    res = client.post(
        "/api/clientes",
        cookies={"socio-auth": token},
        headers={"X-CSRF-Token": "csrf-ok"},
        json={"nombre": "Cliente CSRF", "sector": "Retail"},
    )
    assert res.status_code == 403
    assert "Solo perfiles administradores" in res.text
