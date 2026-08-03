from __future__ import annotations

from pathlib import Path

import pytest

from backend.repositories.file_repository import repo
from backend.services.context_document_service import store_document
from backend.services.entity_profile_service import (
    build_profile_draft,
    confirm_profile_draft,
    update_pending_item,
    update_profile_answers,
)


@pytest.fixture()
def isolated_profile_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_clientes = tmp_path / "data" / "clientes"
    data_clientes.mkdir(parents=True)
    monkeypatch.setattr(repo, "data_clientes", data_clientes)
    return data_clientes


def test_profile_draft_is_transparent_and_adaptive(isolated_profile_storage: Path) -> None:
    client_dir = isolated_profile_storage / "cliente_demo"
    client_dir.mkdir()
    (client_dir / "perfil.yaml").write_text(
        """schema_version: v1
cliente:
  nombre_legal: Empresa XYZ
  sector: Servicios
  pais: Ecuador
encargo:
  anio_activo: 2025
  marco_referencial: NIIF para PYMES
  fase_actual: planificacion
materialidad:
  estado_materialidad: preliminar
  final: {}
riesgo_global:
  nivel: medio
""",
        encoding="utf-8",
    )
    (client_dir / "tb.xlsx").write_bytes(b"trial")
    store_document(
        "cliente_demo",
        filename="Informe 2024.md",
        content=b"# Informe anterior\n\nLa entidad presta servicios profesionales.",
        document_type="prior_financial_statements",
        period="2024",
    )

    draft = build_profile_draft("cliente_demo")

    assert draft["status"] == "needs_answers"
    assert any(source["type"] == "prior_financial_statements" for source in draft["sources"])
    assert any(question["id"] == "activity_continues" for question in draft["questions"])
    assert not any(question["id"] == "main_activity" for question in draft["questions"])
    assert "Ningún riesgo" in draft["transparency_note"]


def test_profile_requires_critical_answers_before_confirmation(isolated_profile_storage: Path) -> None:
    client_dir = isolated_profile_storage / "cliente_demo"
    client_dir.mkdir()
    draft = build_profile_draft("cliente_demo")

    with pytest.raises(ValueError, match="preguntas críticas"):
        confirm_profile_draft("cliente_demo", "auditor")

    answers = {question_id: "Confirmado" for question_id in draft["unanswered_critical"]}
    updated = update_profile_answers("cliente_demo", answers)
    assert updated["unanswered_critical"] == []

    confirmed = confirm_profile_draft("cliente_demo", "auditor")
    assert confirmed["status"] == "confirmed"
    assert confirmed["confirmed_by"] == "auditor"


def test_partial_information_can_continue_as_provisional(isolated_profile_storage: Path) -> None:
    client_dir = isolated_profile_storage / "cliente_parcial"
    client_dir.mkdir()
    draft = build_profile_draft("cliente_parcial")

    answers = {question_id: "Pendiente de confirmar durante planificación" for question_id in draft["unanswered_critical"]}
    updated = update_profile_answers("cliente_parcial", answers)

    assert updated["unanswered_critical"] == []
    assert set(updated["pending_confirmations"]) == set(answers)
    assert any("no se tratarán como hechos" in item for item in updated["limitations"])

    provisional = confirm_profile_draft("cliente_parcial", "auditor")
    assert provisional["status"] == "provisional"
    assert len(provisional["pending_items"]) == len(answers)
    assert provisional["pending_items"][0]["impact"]

    question_id = provisional["pending_items"][0]["question_id"]
    requested = update_pending_item(
        "cliente_parcial",
        question_id,
        status="requested",
        answer="Pendiente de confirmar durante planificación",
    )
    assert next(item for item in requested["pending_items"] if item["question_id"] == question_id)["status"] == "requested"

    resolved = update_pending_item(
        "cliente_parcial",
        question_id,
        status="confirmed",
        answer="La entidad presta servicios profesionales de consultoría.",
    )
    assert question_id not in resolved["pending_confirmations"]
    assert resolved["answers"][question_id].startswith("La entidad presta")
