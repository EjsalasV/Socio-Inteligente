from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from backend.auth import create_access_token
from backend.main import app


def _auth_headers() -> dict[str, str]:
    token, _ = create_access_token(
        sub="pagination-tester",
        org_id="org_demo",
        allowed_clientes=["*"],
        role="admin",
    )
    return {"Authorization": f"Bearer {token}"}


def _fake_tasks() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for i in range(1, 11):
        area = "130" if i <= 5 else "140"
        out.append(
            {
                "id": f"t-{i}",
                "area_code": area,
                "area_name": "Cuentas por Cobrar" if area == "130" else "Efectivo",
                "title": f"Tarea {i}",
                "nia_ref": "NIA 500" if i % 2 == 0 else "NIA 505",
                "prioridad": "alta" if i <= 3 else "media",
                "required": True,
                "done": i % 3 == 0,
                "evidence_note": "ok" if i % 4 == 0 else "",
            }
        )
    return out


def test_workpapers_pagination_returns_page_slice(monkeypatch) -> None:
    from backend.routes import workpapers as route

    monkeypatch.setattr(route, "_generate_tasks", lambda cliente_id: _fake_tasks())
    monkeypatch.setattr(route, "_merge_saved_tasks", lambda cliente_id, generated: generated)
    monkeypatch.setattr(route, "_quality_gates", lambda cliente_id, tasks: ([], route.CoverageSummary()))
    monkeypatch.setattr(route, "write_workpapers", lambda cliente_id, tasks: None)

    client = TestClient(app)
    res = client.get("/papeles-trabajo/cliente_demo?page=2&page_size=3", headers=_auth_headers())
    assert res.status_code == 200, res.text
    payload = res.json()["data"]

    assert payload["tasks_page"] == 2
    assert payload["tasks_page_size"] == 3
    assert payload["tasks_total"] == 10
    assert payload["tasks_total_all"] == 10
    assert payload["tasks_has_more"] is True
    assert len(payload["tasks"]) == 3
    assert payload["tasks"][0]["id"] == "t-4"


def test_workpapers_pagination_supports_filters(monkeypatch) -> None:
    from backend.routes import workpapers as route

    monkeypatch.setattr(route, "_generate_tasks", lambda cliente_id: _fake_tasks())
    monkeypatch.setattr(route, "_merge_saved_tasks", lambda cliente_id, generated: generated)
    monkeypatch.setattr(route, "_quality_gates", lambda cliente_id, tasks: ([], route.CoverageSummary()))
    monkeypatch.setattr(route, "write_workpapers", lambda cliente_id, tasks: None)

    client = TestClient(app)
    res = client.get("/papeles-trabajo/cliente_demo?page=1&page_size=0&area_code=140&q=nia%20500", headers=_auth_headers())
    assert res.status_code == 200, res.text
    payload = res.json()["data"]
    assert payload["tasks_has_more"] is False
    assert payload["tasks_total"] > 0
    assert all(task["area_code"] == "140" for task in payload["tasks"])
    assert all("NIA 500" in task["nia_ref"] for task in payload["tasks"])
