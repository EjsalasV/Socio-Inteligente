from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from backend.auth import create_access_token
from backend.main import app
from backend.routes import chat


def _headers() -> dict[str, str]:
    token, _ = create_access_token(
        sub="alpha-tester",
        org_id="org_demo",
        allowed_clientes=["*"],
        role="senior",
    )
    return {"Authorization": f"Bearer {token}"}


def test_alpha_feedback_requires_existing_trace(monkeypatch) -> None:
    monkeypatch.setattr(chat, "read_quality_trace", lambda _cliente_id: [{"trace_id": "trace-1"}])
    stored: list[dict] = []
    monkeypatch.setattr(chat, "append_pilot_feedback", lambda _cliente_id, event: stored.append(event))
    monkeypatch.setattr(chat, "record_metric_event", lambda *_args, **_kwargs: None)

    response = TestClient(app).post(
        "/chat/cliente_alpha/feedback",
        headers=_headers(),
        json={"trace_id": "trace-1", "outcome": "incorrect", "issue_type": "fact", "comment": "Dato no sustentado"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["recorded"] is True
    assert stored[0]["trace_id"] == "trace-1"


def test_alpha_session_survey_and_metrics(monkeypatch) -> None:
    stored: list[dict] = []
    monkeypatch.setattr(chat, "append_pilot_feedback", lambda _cliente_id, event: stored.append(event))

    client = TestClient(app)
    survey = client.post(
        "/chat/cliente_alpha/pilot-survey",
        headers=_headers(),
        json={
            "conversation_id": "conv-1",
            "time_saved_minutes": 30,
            "understanding_before": 2,
            "understanding_after": 4,
            "would_reuse": True,
            "willing_to_pay": True,
        },
    )

    assert survey.status_code == 200
    assert stored[0]["outcome"] == "session_survey"

    monkeypatch.setattr(chat, "read_quality_trace", lambda _cliente_id: [{"controls": {"publication": "published", "quality_repair_used": True}}])
    monkeypatch.setattr(chat, "read_pilot_feedback", lambda _cliente_id: stored)
    metrics = client.get("/chat/cliente_alpha/pilot-metrics", headers=_headers())

    assert metrics.status_code == 200
    data = metrics.json()["data"]
    assert data["average_time_saved_minutes"] == 30.0
    assert data["average_learning_delta"] == 2.0
    assert data["willing_to_pay_rate_pct"] == 100.0
