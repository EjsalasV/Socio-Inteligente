from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.repositories.file_repository import repo
from backend.services.mentor_conversation_service import get_mentor_session, reply_to_mentor


def test_socratic_session_is_isolated_and_not_audit_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clients = tmp_path / "clientes"
    (clients / "demo").mkdir(parents=True)
    monkeypatch.setattr(repo, "data_clientes", clients)

    def fake_llm(system: str, user: str) -> tuple[str, dict[str, str]]:
        assert "socrática" in system
        assert "Mi hipótesis" in user
        return json.dumps({
            "feedback": "Relacionaste la variación con corte.",
            "strength": "Formulaste una hipótesis verificable.",
            "reasoning_gap": "Falta definir evidencia contradictoria.",
            "follow_up_question": "¿Qué documento refutaría tu hipótesis?",
            "hint": "Piensa en fechas antes y después del cierre.",
            "progress_stage": "test",
            "ready_to_continue": True,
            "safety_note": "No es una conclusión.",
        }), {"model": "fake"}

    result = reply_to_mentor("demo", account_context={"account_name": "Ventas"}, auditor_response="Mi hipótesis es un problema de corte.", learning_role="semi", user_id="ana", llm_call=fake_llm)
    session = get_mentor_session("demo", result["session_id"], "ana")
    assert result["turns_remaining"] == 7
    assert session is not None
    assert session["memory_classification"] == "educational_dialogue_not_audit_evidence"
    assert get_mentor_session("demo", result["session_id"], "otro") is None
    assert "recommended_resources" in result["turn"]["mentor"]


def test_empty_auditor_response_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clients = tmp_path / "clientes"
    (clients / "demo").mkdir(parents=True)
    monkeypatch.setattr(repo, "data_clientes", clients)

    with pytest.raises(ValueError, match="Escribe tu razonamiento"):
        reply_to_mentor(
            "demo",
            account_context={"account_name": "Ventas"},
            auditor_response="   ",
            learning_role="semi",
            user_id="ana",
        )
