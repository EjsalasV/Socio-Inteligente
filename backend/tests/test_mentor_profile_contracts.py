from __future__ import annotations

import os

os.environ.setdefault("CI", "1")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-for-contracts")

from typing import Callable

import pytest
from fastapi.testclient import TestClient

from backend.auth import get_current_user
from backend.main import app
from backend.routes import entity_profile as entity_profile_routes
from backend.routes import mentor as mentor_routes
from backend.schemas import UserContext


CLIENTE_ID = "demo"


def make_user(*, allowed_clientes: list[str], user_id: str = "mentor-user", sub: str = "mentor-user") -> UserContext:
    return UserContext(
        sub=sub,
        org_id="org_demo",
        allowed_clientes=allowed_clientes,
        role="auditor",
        user_id=user_id,
        display_name="Mentor QA",
    )


@pytest.fixture
def api_client() -> TestClient:
    app.dependency_overrides.clear()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def override_current_user(user: UserContext) -> Callable[[], UserContext]:
    return lambda: user


def assert_error_envelope(response, expected_code: str, expected_status: int) -> None:
    assert response.status_code == expected_status
    body = response.json()
    assert body["status"] == "error"
    assert body["code"] == expected_code
    assert isinstance(body["message"], str)
    assert isinstance(body["action_hint"], str)
    assert isinstance(body["retryable"], bool)
    assert isinstance(body["details"], dict)


def test_mentor_account_allows_authorized_cliente(api_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    user = make_user(allowed_clientes=[CLIENTE_ID])
    app.dependency_overrides[get_current_user] = override_current_user(user)
    monkeypatch.setattr(mentor_routes.identity_store, "get_preferences", lambda _sub: {"learning_role": "semi"})
    monkeypatch.setattr(
        mentor_routes,
        "generate_account_mentor_guide",
        lambda cliente_id, payload, learning_role, force: {
            "cliente_id": cliente_id,
            "learning_role": learning_role,
            "force": force,
            "payload": payload,
        },
    )

    response = api_client.post(
        f"/api/mentor/{CLIENTE_ID}/account",
        json={
            "area_code": "410",
            "area_name": "Ingresos",
            "account_code": "41001",
            "account_name": "Ventas locales",
            "current_balance": 1200.0,
            "prior_balance": 1000.0,
            "variation_pct": 20.0,
            "area_assertions": [],
            "area_accounts": [],
            "force": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["data"]["cliente_id"] == CLIENTE_ID
    assert body["data"]["learning_role"] == "semi"


def test_mentor_account_denies_unauthorized_cliente(api_client: TestClient) -> None:
    user = make_user(allowed_clientes=["otro-cliente"], user_id="mentor-user")
    app.dependency_overrides[get_current_user] = override_current_user(user)

    response = api_client.post(
        f"/api/mentor/{CLIENTE_ID}/account",
        json={
            "area_code": "410",
            "area_name": "Ingresos",
            "account_code": "41001",
            "account_name": "Ventas locales",
            "current_balance": 1200.0,
            "prior_balance": 1000.0,
            "variation_pct": 20.0,
            "area_assertions": [],
            "area_accounts": [],
            "force": False,
        },
    )

    assert_error_envelope(response, "HTTP_403", 403)
    assert response.json()["message"] == "Acceso denegado al cliente: demo"


def test_mentor_session_returns_stable_error_envelope_when_missing(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = make_user(allowed_clientes=[CLIENTE_ID])
    app.dependency_overrides[get_current_user] = override_current_user(user)
    monkeypatch.setattr(mentor_routes, "get_mentor_session", lambda *_args, **_kwargs: None)

    response = api_client.get(f"/api/mentor/{CLIENTE_ID}/sessions/missing")

    assert_error_envelope(response, "MENTOR_SESSION_NOT_FOUND", 404)
    assert response.json()["message"] == "Sesión no encontrada."


def test_mentor_reply_rejects_session_from_other_user(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = make_user(allowed_clientes=[CLIENTE_ID], user_id="mentor-user")
    app.dependency_overrides[get_current_user] = override_current_user(user)
    monkeypatch.setattr(mentor_routes.identity_store, "get_preferences", lambda _sub: {"learning_role": "semi"})
    monkeypatch.setattr(
        mentor_routes,
        "reply_to_mentor",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError("La sesión de mentoría pertenece a otro usuario.")),
    )

    response = api_client.post(
        f"/api/mentor/{CLIENTE_ID}/reply",
        json={
            "session_id": "session-other-user",
            "auditor_response": "Analizo el riesgo con evidencia suficiente.",
            "account_context": {"account_name": "Ventas locales"},
        },
    )

    assert_error_envelope(response, "MENTOR_SESSION_FORBIDDEN", 403)
    assert response.json()["message"] == "La sesión de mentoría pertenece a otro usuario."


def test_profile_confirm_requires_completed_profile(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = make_user(allowed_clientes=[CLIENTE_ID])
    app.dependency_overrides[get_current_user] = override_current_user(user)
    monkeypatch.setattr(
        entity_profile_routes,
        "confirm_profile_draft",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("Responde las preguntas críticas antes de confirmar el perfil.")),
    )

    response = api_client.post(f"/api/entity-profile/{CLIENTE_ID}/confirm")

    assert_error_envelope(response, "PROFILE_CONFIRMATION_INCOMPLETE", 422)
    assert response.json()["message"] == "Responde las preguntas críticas antes de confirmar el perfil."


def test_profile_decision_rejects_missing_hypothesis(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = make_user(allowed_clientes=[CLIENTE_ID])
    app.dependency_overrides[get_current_user] = override_current_user(user)
    monkeypatch.setattr(
        entity_profile_routes,
        "update_analysis_decision",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("La hipótesis indicada no existe.")),
    )

    response = api_client.put(
        f"/api/entity-profile/{CLIENTE_ID}/analysis/decision",
        json={
            "hypothesis_id": "risk-nonexistent",
            "status": "accepted",
            "edited_title": "",
            "edited_reason": "",
        },
    )

    assert_error_envelope(response, "INVALID_PROFILE_DECISION", 422)
    assert response.json()["message"] == "La hipótesis indicada no existe."


def test_invalid_payload_returns_validation_envelope(api_client: TestClient) -> None:
    user = make_user(allowed_clientes=[CLIENTE_ID])
    app.dependency_overrides[get_current_user] = override_current_user(user)

    response = api_client.post(
        f"/api/mentor/{CLIENTE_ID}/account",
        json={
            "area_code": "410",
            "area_name": "Ingresos",
            "account_code": "41001",
            "current_balance": 1200.0,
            "prior_balance": 1000.0,
            "variation_pct": 20.0,
            "area_assertions": [],
            "area_accounts": [],
        },
    )

    assert_error_envelope(response, "VALIDATION_ERROR", 422)
    details = response.json()["details"]
    assert isinstance(details.get("errors"), list)
    assert details["errors"]


@pytest.mark.parametrize(
    ("path", "payload", "error_code", "message"),
    [
        (
            "/api/mentor/demo/reply",
            {
                "session_id": "session-1",
                "auditor_response": "Respuesta razonada del auditor.",
                "account_context": {"account_name": "Ventas locales"},
            },
            "MENTOR_UNAVAILABLE",
            "La IA no devolvió una respuesta de mentoría válida.",
        ),
        (
            "/api/entity-profile/demo/analyze",
            {"force": False},
            "PROFILE_ANALYSIS_UNAVAILABLE",
            "La IA no devolvió un perfil estructurado válido.",
        ),
    ],
)
def test_empty_ai_responses_map_to_service_unavailable(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    payload: dict[str, object],
    error_code: str,
    message: str,
) -> None:
    user = make_user(allowed_clientes=[CLIENTE_ID])
    app.dependency_overrides[get_current_user] = override_current_user(user)
    monkeypatch.setattr(mentor_routes.identity_store, "get_preferences", lambda _sub: {"learning_role": "semi"})
    monkeypatch.setattr(
        mentor_routes,
        "reply_to_mentor",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("La IA no devolvió una respuesta de mentoría válida.")),
    )
    monkeypatch.setattr(
        entity_profile_routes,
        "analyze_entity_profile",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("La IA no devolvió un perfil estructurado válido.")),
    )

    response = api_client.post(path, json=payload)

    assert_error_envelope(response, error_code, 503)
    assert response.json()["message"] == message
