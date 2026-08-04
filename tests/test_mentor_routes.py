from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from backend.auth import create_access_token
from backend.main import app
from backend.repositories.file_repository import repo


def _auth_headers(*, role: str = "staff", allowed_clientes: list[str] | None = None) -> dict[str, str]:
    token, _ = create_access_token(
        sub="mentor-tester",
        org_id="org_demo",
        allowed_clientes=allowed_clientes or ["*"],
        role=role,
    )
    return {"Authorization": f"Bearer {token}"}


def test_account_mentor_uses_learning_role_and_passes_force_flag(
    tmp_path: Path,
    monkeypatch,
) -> None:
    clients = tmp_path / "clientes"
    (clients / "demo").mkdir(parents=True)
    monkeypatch.setattr(repo, "data_clientes", clients)
    monkeypatch.setattr("backend.routes.mentor.identity_store.get_preferences", lambda _sub: {"learning_role": "senior"})

    captured: dict[str, object] = {}

    def fake_generate(cliente_id: str, payload: dict[str, object], *, learning_role: str, force: bool = False, llm_call=None):
        captured["cliente_id"] = cliente_id
        captured["payload"] = payload
        captured["learning_role"] = learning_role
        captured["force"] = force
        return {
            "cliente_id": cliente_id,
            "learning_role": learning_role,
            "accepted_context_counts": {"risk_hypotheses": 2},
        }

    monkeypatch.setattr("backend.routes.mentor.generate_account_mentor_guide", fake_generate)
    client = TestClient(app)

    res = client.post(
        "/api/mentor/demo/account",
        headers=_auth_headers(),
        json={
            "area_code": "410",
            "area_name": "Ingresos",
            "account_code": "4101",
            "account_name": "Ventas",
            "current_balance": 120.0,
            "prior_balance": 100.0,
            "variation_pct": 20.0,
            "area_assertions": [],
            "area_accounts": [],
            "force": True,
        },
    )

    assert res.status_code == 200
    assert res.json()["data"]["learning_role"] == "senior"
    assert captured["cliente_id"] == "demo"
    assert captured["learning_role"] == "senior"
    assert captured["force"] is True
    assert "force" not in captured["payload"]


def test_mentor_reply_records_learning_and_session_endpoint_respects_access(
    tmp_path: Path,
    monkeypatch,
) -> None:
    clients = tmp_path / "clientes"
    (clients / "demo").mkdir(parents=True)
    monkeypatch.setattr(repo, "data_clientes", clients)
    monkeypatch.setattr("backend.routes.mentor.identity_store.get_preferences", lambda _sub: {"learning_role": "semi"})

    recorded: dict[str, object] = {}

    def fake_reply(
        cliente_id: str,
        *,
        account_context: dict[str, object],
        auditor_response: str,
        learning_role: str,
        user_id: str,
        session_id: str = "",
        llm_call=None,
    ) -> dict[str, object]:
        recorded["cliente_id"] = cliente_id
        recorded["learning_role"] = learning_role
        recorded["user_id"] = user_id
        recorded["session_id"] = session_id
        return {
            "session_id": session_id or "session-abc",
            "turn": {
                "mentor": {
                    "progress_stage": "analyze",
                    "ready_to_continue": True,
                    "recommended_resources": {
                        "procedures": [{"id": "P-101"}],
                        "norms": [{"code": "N-320"}],
                    },
                }
            },
        }

    def fake_record(user_id: str, *, progress_stage: str, ready_to_continue: bool, resource_codes: list[str]) -> None:
        recorded["record_user_id"] = user_id
        recorded["progress_stage"] = progress_stage
        recorded["ready_to_continue"] = ready_to_continue
        recorded["resource_codes"] = resource_codes

    monkeypatch.setattr("backend.routes.mentor.reply_to_mentor", fake_reply)
    monkeypatch.setattr("backend.routes.mentor.record_mentor_learning", fake_record)
    monkeypatch.setattr("backend.routes.mentor.get_mentor_session", lambda _cid, _sid, _sub: {"session_id": "session-abc", "turns_used": 3})
    client = TestClient(app)

    reply = client.post(
        "/api/mentor/demo/reply",
        headers=_auth_headers(),
        json={
            "session_id": "",
            "auditor_response": "Mi hipótesis es un error de corte.",
            "account_context": {"account_name": "Ventas"},
        },
    )
    assert reply.status_code == 200
    assert recorded["cliente_id"] == "demo"
    assert recorded["learning_role"] == "semi"
    assert recorded["progress_stage"] == "analyze"
    assert recorded["ready_to_continue"] is True
    assert recorded["resource_codes"] == ["P-101", "N-320"]

    session = client.get("/api/mentor/demo/sessions/session-abc", headers=_auth_headers())
    assert session.status_code == 200
    assert session.json()["data"]["session_id"] == "session-abc"

    monkeypatch.setattr("backend.routes.mentor.get_mentor_session", lambda _cid, _sid, _sub: None)
    forbidden = client.get("/api/mentor/demo/sessions/otra-sesion", headers=_auth_headers())
    assert forbidden.status_code == 404
