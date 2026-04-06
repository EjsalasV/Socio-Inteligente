from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from backend.auth import create_access_token
from backend.main import app


def _auth_headers(*, role: str = "staff", allowed_clientes: list[str] | None = None) -> dict[str, str]:
    token, _ = create_access_token(
        sub="robustness-tester",
        org_id="org_demo",
        allowed_clientes=allowed_clientes or ["*"],
        role=role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    ("method", "path", "payload", "role"),
    [
        ("post", "/reportes/cliente_demo/documentos/carta_control_interno/estado", {}, "staff"),
        ("post", "/reportes/cliente_demo/documentos/carta_control_interno/estado", {"target_state": "issued"}, "staff"),
        ("post", "/reportes/cliente_demo/documentos/carta_control_interno/estado", {"target_state": "invalid_state"}, "socio"),
        ("post", "/reportes/cliente_demo/documentos/carta_control_interno/emitir", {"reason": 12345}, "staff"),
        ("post", "/reportes/cliente_demo/documentos/carta_control_interno/secciones/hallazgo:OBS-01/evidencia", {"label": "x"}, "senior"),
        ("post", "/reportes/cliente_demo/documentos/carta_control_interno/secciones/hallazgo:OBS-01/evidencia", {"source_type": "workpaper", "source_id": "", "label": "x"}, "senior"),
        ("post", "/reportes/cliente_demo/carta-control-interno", {"recipient": "", "max_findings": 999}, "manager"),
        ("post", "/reportes/cliente_demo/niif-pymes-borrador", {"ifrs_for_smes_version": "2099", "early_adoption": True}, "manager"),
        ("get", "/reportes/cliente_demo/documentos/carta_control_interno/quality-check", None, "senior"),
        ("get", "/reportes/cliente_demo/documentos/carta_control_interno/evidence-gate", None, "senior"),
    ],
)
def test_critical_document_endpoints_fail_closed_not_500(
    method: str,
    path: str,
    payload: dict | None,
    role: str,
) -> None:
    client = TestClient(app)
    headers = _auth_headers(role=role, allowed_clientes=["*"])

    if method == "post":
        res = client.post(path, headers=headers, json=payload)
    else:
        res = client.get(path, headers=headers)

    assert res.status_code < 500, f"Endpoint returned 5xx for {method.upper()} {path}: {res.status_code} {res.text}"
    assert res.status_code in {200, 400, 401, 403, 404, 409, 422}


def test_rejects_non_json_content_type_on_state_transition() -> None:
    client = TestClient(app)
    headers = _auth_headers(role="gerente", allowed_clientes=["*"])
    res = client.post(
        "/reportes/cliente_demo/documentos/carta_control_interno/estado",
        headers={**headers, "Content-Type": "text/plain"},
        content="target_state=approved",
    )
    assert res.status_code in {400, 415, 422}
