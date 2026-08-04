from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.repositories.file_repository import repo
from backend.services.mentor_service import generate_account_mentor_guide


def test_mentor_adapts_role_uses_confirmed_context_and_caches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clients = tmp_path / "clientes"
    client = clients / "demo"
    client.mkdir(parents=True)
    monkeypatch.setattr(repo, "data_clientes", clients)
    (client / "entity_profile_draft.json").write_text(json.dumps({
        "analysis": {"risk_hypotheses": [{"id": "risk-1", "title": "Corte", "decision": {"status": "accepted", "decided_by": "senior"}}]}
    }), encoding="utf-8")
    calls = 0

    def fake_llm(system: str, user: str) -> tuple[str, dict[str, str]]:
        nonlocal calls
        calls += 1
        assert "Nivel del auditor: junior" in system
        assert "Corte" in user
        return json.dumps({
            "observation": "La cuenta aumentó.",
            "why_relevant": "La variación requiere explicación.",
            "guided_questions": ["¿Qué explica el cambio?"],
            "next_steps": ["Compara el auxiliar."],
            "watch_outs": [],
            "concepts": [{"term": "Corte", "explanation": "Registro en el período correcto."}],
            "mentor_challenge": "Explica qué evidencia refutaría tu hipótesis.",
            "no_conclusion_note": "No concluye error.",
        }), {"model": "fake", "input_tokens": "80"}

    payload = {"area_code": "410", "area_name": "Ingresos", "account_code": "4101", "account_name": "Ventas", "current_balance": 120, "prior_balance": 100, "variation_pct": 20, "area_assertions": []}
    first = generate_account_mentor_guide("demo", payload, learning_role="junior", llm_call=fake_llm)
    second = generate_account_mentor_guide("demo", payload, learning_role="junior", llm_call=fake_llm)
    assert calls == 1
    assert first == second
    assert first["learning_role"] == "junior"
    assert first["accepted_context_counts"]["risk_hypotheses"] == 1


@pytest.mark.parametrize(
    ("learning_role", "expected_phrase"),
    [
        ("junior", "Nivel del auditor: junior"),
        ("semi", "Nivel del auditor: semi"),
        ("senior", "Nivel del auditor: senior"),
        ("socio", "Nivel del auditor: socio"),
    ],
)
def test_mentor_prompt_reflects_learning_role(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    learning_role: str,
    expected_phrase: str,
) -> None:
    clients = tmp_path / "clientes"
    client = clients / "demo"
    client.mkdir(parents=True)
    monkeypatch.setattr(repo, "data_clientes", clients)

    captured: list[str] = []

    def fake_llm(system: str, user: str) -> tuple[str, dict[str, str]]:
        captured.append(system)
        return json.dumps({
            "observation": "OK",
            "why_relevant": "OK",
            "guided_questions": [],
            "next_steps": [],
            "watch_outs": [],
            "concepts": [],
            "mentor_challenge": "OK",
            "no_conclusion_note": "OK",
        }), {"model": "fake"}

    payload = {
        "area_code": "410",
        "area_name": "Ingresos",
        "account_code": "4101",
        "account_name": "Ventas",
        "current_balance": 120,
        "prior_balance": 100,
        "variation_pct": 20,
        "area_assertions": [],
    }

    result = generate_account_mentor_guide("demo", payload, learning_role=learning_role, llm_call=fake_llm)

    assert result["learning_role"] == learning_role
    assert captured and expected_phrase in captured[0]
