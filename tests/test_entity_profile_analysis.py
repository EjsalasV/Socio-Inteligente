from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.repositories.file_repository import repo
from backend.services.context_document_service import store_document
from backend.services.entity_profile_analysis_service import analyze_entity_profile, get_accepted_entity_context, update_analysis_decision
from backend.services.entity_profile_service import build_profile_draft


@pytest.fixture()
def profile_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    clients = tmp_path / "clientes"
    client = clients / "demo"
    client.mkdir(parents=True)
    monkeypatch.setattr(repo, "data_clientes", clients)
    (client / "perfil.yaml").write_text("cliente:\n  sector: Servicios\n", encoding="utf-8")
    build_profile_draft("demo")
    return client


def test_analysis_has_provenance_and_is_cached(profile_client: Path) -> None:
    store_document(
        "demo",
        filename="informe.md",
        content=b"# Nota 1\nLa entidad obtiene ingresos por servicios recurrentes.",
        document_type="prior_financial_statements",
        period="2024",
    )
    calls = 0

    def fake_llm(system: str, prompt: str) -> tuple[str, dict[str, str]]:
        nonlocal calls
        calls += 1
        assert "DOC-1" in prompt
        return json.dumps({
            "entity_summary": {"activity": "Servicios", "confidence": 0.8, "evidence_refs": ["DOC-1"]},
            "changes": [],
            "risk_hypotheses": [{"title": "Corte de ingresos", "confidence": 0.6, "evidence_refs": ["DOC-1"], "status": "proposed"}],
            "estimate_hypotheses": [],
            "missing_information": ["Contratos actuales"],
        }), {"provider": "test", "model": "fake", "input_tokens": "100"}

    first = analyze_entity_profile("demo", llm_call=fake_llm)
    second = analyze_entity_profile("demo", llm_call=fake_llm)

    assert calls == 1
    assert first == second
    assert first["sources"][0]["source_id"] == "DOC-1"
    assert first["risk_hypotheses"][0]["status"] == "proposed"
    assert first["input_chars"] <= 26000


def test_force_regenerates_analysis(profile_client: Path) -> None:
    calls = 0

    def fake_llm(_system: str, _prompt: str) -> tuple[str, dict[str, str]]:
        nonlocal calls
        calls += 1
        return json.dumps({"changes": [], "risk_hypotheses": [], "estimate_hypotheses": []}), {"model": "fake"}

    analyze_entity_profile("demo", llm_call=fake_llm)
    analyze_entity_profile("demo", force=True, llm_call=fake_llm)
    assert calls == 2


def test_only_accepted_hypotheses_reach_financial_context(profile_client: Path) -> None:
    def fake_llm(_system: str, _prompt: str) -> tuple[str, dict[str, str]]:
        return json.dumps({
            "changes": [],
            "risk_hypotheses": [
                {"title": "Corte de ingresos", "why_it_matters": "Contratos anuales", "evidence_refs": []},
                {"title": "Partes relacionadas", "why_it_matters": "Transacciones complejas", "evidence_refs": []},
            ],
            "estimate_hypotheses": [],
        }), {"model": "fake"}

    analysis = analyze_entity_profile("demo", llm_call=fake_llm)
    accepted_id = analysis["risk_hypotheses"][0]["id"]
    rejected_id = analysis["risk_hypotheses"][1]["id"]
    update_analysis_decision("demo", hypothesis_id=accepted_id, decision_status="accepted", decided_by="senior", edited_title="Corte contractual")
    update_analysis_decision("demo", hypothesis_id=rejected_id, decision_status="rejected", decided_by="senior")

    context = get_accepted_entity_context("demo")
    assert [item["title"] for item in context["risk_hypotheses"]] == ["Corte contractual"]
    assert context["risk_hypotheses"][0]["confirmed_by"] == "senior"
