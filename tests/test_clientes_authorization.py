"""Regresion: autorizacion por cliente en /api/clientes.

Cada usuario solo debe ver y operar los clientes asignados en su token
o en sus asignaciones del identity store.
"""
from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from backend.auth import create_access_token
from backend.main import app
from backend.models.audit import Audit
from backend.models.client import Client
from backend.utils.database import SessionLocal


def _bearer(*, role: str = "staff", allowed_clientes: list[str] | None = None) -> dict[str, str]:
    token, _ = create_access_token(
        sub="authz-tester",
        org_id="org_demo",
        allowed_clientes=allowed_clientes or [],
        role=role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def two_clients():
    """Crea dos clientes temporales en DB y los elimina al terminar."""
    suffix = uuid.uuid4().hex[:8]
    id_a = f"authz_a_{suffix}"
    id_b = f"authz_b_{suffix}"
    session = SessionLocal()
    try:
        a = Client(client_id=id_a, nombre="Cliente A", estado="ACTIVO")
        b = Client(client_id=id_b, nombre="Cliente B", estado="ACTIVO")
        session.add_all([a, b])
        session.commit()
        session.refresh(a)
        session.refresh(b)
        yield a, b
    finally:
        session.query(Audit).filter(Audit.client_id.in_([a.id, b.id])).delete(synchronize_session=False)
        session.query(Client).filter(Client.client_id.in_([id_a, id_b])).delete(synchronize_session=False)
        session.commit()
        session.close()


def test_listar_clientes_excludes_unassigned_clients(two_clients, monkeypatch) -> None:
    a, b = two_clients
    monkeypatch.setenv("ALLOWED_CLIENTES", a.client_id)
    client = TestClient(app)
    res = client.get("/api/clientes", headers=_bearer(allowed_clientes=[a.client_id]))
    assert res.status_code == 200
    ids = [c["client_id"] for c in res.json()["data"]["clientes"]]
    assert a.client_id in ids
    assert b.client_id not in ids


def test_listar_clientes_excludes_archived(two_clients, monkeypatch) -> None:
    a, b = two_clients
    monkeypatch.setenv("ALLOWED_CLIENTES", "*")
    session = SessionLocal()
    try:
        session.query(Client).filter(Client.client_id == b.client_id).update({"estado": "ARCHIVADO"})
        session.commit()
    finally:
        session.close()
    client = TestClient(app)
    res = client.get("/api/clientes", headers=_bearer(role="admin", allowed_clientes=["*"]))
    assert res.status_code == 200
    ids = [c["client_id"] for c in res.json()["data"]["clientes"]]
    assert a.client_id in ids
    assert b.client_id not in ids


def test_obtener_cliente_denied_for_unassigned(two_clients, monkeypatch) -> None:
    a, b = two_clients
    monkeypatch.setenv("ALLOWED_CLIENTES", a.client_id)
    client = TestClient(app)
    res = client.get(f"/api/clientes/{b.client_id}", headers=_bearer(allowed_clientes=[a.client_id]))
    assert res.status_code == 403


def test_listar_auditorias_denied_for_unassigned(two_clients, monkeypatch) -> None:
    a, b = two_clients
    monkeypatch.setenv("ALLOWED_CLIENTES", a.client_id)
    client = TestClient(app)
    res = client.get(
        f"/api/clientes/{b.client_id}/auditorias",
        headers=_bearer(allowed_clientes=[a.client_id]),
    )
    assert res.status_code == 403


def test_crear_auditoria_requires_management_role(two_clients, monkeypatch) -> None:
    a, _ = two_clients
    monkeypatch.setenv("ALLOWED_CLIENTES", a.client_id)
    client = TestClient(app)
    res = client.post(
        f"/api/clientes/{a.client_id}/auditorias?periodo=2099",
        headers=_bearer(role="staff", allowed_clientes=[a.client_id]),
    )
    assert res.status_code == 403
    assert "Solo perfiles administradores" in res.text


def test_crear_auditoria_denied_for_unassigned_even_with_role(two_clients, monkeypatch) -> None:
    a, b = two_clients
    monkeypatch.setenv("ALLOWED_CLIENTES", a.client_id)
    client = TestClient(app)
    res = client.post(
        f"/api/clientes/{b.client_id}/auditorias?periodo=2099",
        headers=_bearer(role="manager", allowed_clientes=[a.client_id]),
    )
    assert res.status_code == 403


def test_actualizar_auditoria_cross_client_is_not_found(two_clients, monkeypatch) -> None:
    """Una auditoria de un cliente no puede modificarse via la ruta de otro cliente."""
    a, b = two_clients
    monkeypatch.setenv("ALLOWED_CLIENTES", "*")
    session = SessionLocal()
    try:
        audit = Audit(
            client_id=a.id,
            codigo_auditoria=f"{a.client_id.upper()}_2099",
            periodo="2099",
            estado="PLANEACIÓN",
        )
        session.add(audit)
        session.commit()
        session.refresh(audit)
        audit_id = audit.id
    finally:
        session.close()

    client = TestClient(app)
    headers = _bearer(role="admin", allowed_clientes=["*"])
    res = client.put(
        f"/api/clientes/{b.client_id}/auditorias/{audit_id}?estado=FINALIZADO",
        headers=headers,
    )
    assert res.status_code == 404

    res_ok = client.put(
        f"/api/clientes/{a.client_id}/auditorias/{audit_id}?estado=FINALIZADO",
        headers=headers,
    )
    assert res_ok.status_code == 200
