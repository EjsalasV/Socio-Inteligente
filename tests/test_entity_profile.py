from __future__ import annotations

from pathlib import Path

import pytest
from backend.auth import create_access_token

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


def _auth_headers() -> dict[str, str]:
    token, _ = create_access_token(
        sub="entity-profile-tester",
        org_id="org_demo",
        allowed_clientes=["*"],
        role="auditor",
    )
    return {"Authorization": f"Bearer {token}"}


def _prepare_profile(
    base_dir: Path,
    cliente_id: str,
    *,
    with_prior_financials: bool = False,
    with_prior_control: bool = False,
) -> Path:
    client_dir = base_dir / cliente_id
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
  alcance_estados: individual
materialidad:
  estado_materialidad: preliminar
  final: {}
riesgo_global:
  nivel: medio
""",
        encoding="utf-8",
    )
    (client_dir / "tb.xlsx").write_bytes(b"trial")
    if with_prior_financials:
        store_document(
            cliente_id,
            filename="Informe 2024.md",
            content=b"# Informe anterior\n\nLa entidad presta servicios profesionales.",
            document_type="prior_financial_statements",
            period="2024",
        )
    if with_prior_control:
        store_document(
            cliente_id,
            filename="Carta 2024.md",
            content=b"# Carta anterior\n\nSe comunicaron debilidades de control interno.",
            document_type="prior_internal_control",
            period="2024",
        )
    return client_dir


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


def test_questionnaire_advances_rounds_without_losing_answers(isolated_profile_storage: Path) -> None:
    _prepare_profile(
        isolated_profile_storage,
        "cliente_rondas",
        with_prior_financials=True,
        with_prior_control=True,
    )

    draft = build_profile_draft("cliente_rondas")
    round_one_questions = [question for question in draft["questions"] if question["round"] == 1]
    round_one_answers = {question["id"]: f"Respuesta inicial para {question['id']}" for question in round_one_questions}

    assert round_one_questions
    assert {question["round"] for question in draft["questions"]} == {1}

    first_round = update_profile_answers("cliente_rondas", round_one_answers)
    assert first_round["active_round"] == 2
    assert any(question["round"] == 2 for question in first_round["questions"])
    for question_id, answer in round_one_answers.items():
        assert first_round["answers"][question_id] == answer

    round_two_questions = [question for question in first_round["questions"] if question["round"] == 2]
    round_two_answers = {
        question["id"]: "Se aprueba y revisa el cobro con soportes de factura, contrato y conciliacion."
        for question in round_two_questions
    }

    second_round = update_profile_answers("cliente_rondas", round_two_answers)
    assert second_round["active_round"] == 3
    assert any(question["round"] == 3 for question in second_round["questions"])
    for question_id, answer in round_one_answers.items():
        assert second_round["answers"][question_id] == answer
    for question_id, answer in round_two_answers.items():
        assert second_round["answers"][question_id] == answer


def test_confirmation_error_preserves_answers_and_returns_to_questionnaire(
    client,
    isolated_profile_storage: Path,
) -> None:
    _prepare_profile(
        isolated_profile_storage,
        "cliente_error",
        with_prior_financials=True,
    )

    draft = build_profile_draft("cliente_error")
    first_question = draft["unanswered_critical"][0]
    response = client.put(
        "/api/entity-profile/cliente_error/answers",
        headers=_auth_headers(),
        json={"answers": {first_question: "Confirmado"}},
    )
    assert response.status_code == 200

    confirm = client.post(
        "/api/entity-profile/cliente_error/confirm",
        headers=_auth_headers(),
    )
    assert confirm.status_code == 422
    assert "PROFILE_CONFIRMATION_INCOMPLETE" in confirm.text

    draft_after = client.get(
        "/api/entity-profile/cliente_error/draft",
        headers=_auth_headers(),
    )
    assert draft_after.status_code == 200
    payload = draft_after.json()["data"]
    assert payload["answers"][first_question] == "Confirmado"
    assert payload["status"] == "needs_answers"


def test_confirmed_profile_stays_confirmable_after_full_rounds_and_edits(
    isolated_profile_storage: Path,
) -> None:
    _prepare_profile(
        isolated_profile_storage,
        "cliente_confirmado",
        with_prior_financials=True,
        with_prior_control=True,
    )

    draft = build_profile_draft("cliente_confirmado")
    round_one_questions = [question for question in draft["questions"] if question["round"] == 1]
    round_one_answers = {question["id"]: f"Respuesta segura para {question['id']}" for question in round_one_questions}
    first_round = update_profile_answers("cliente_confirmado", round_one_answers)

    round_two_questions = [question for question in first_round["questions"] if question["round"] == 2]
    round_two_answers = {
        "revenue_process_detail": "La entidad aprueba, factura y cobra con contrato, orden y conciliacion bancaria.",
        "revenue_measurement_model": "Precio fijo con tarifa y evidencia de calculo por contrato y factura.",
        "audit_approach_by_cycle": "Ingresos sustantivo, CxC controles evaluados, compras sustantivo, nomina sustantivo y consolidacion evaluada.",
        "estimates_breakdown": "Usa datos del sistema, supuestos documentados y revision mensual por gerencia.",
    }
    if any(question["id"] == "consolidation_components" for question in round_two_questions):
        round_two_answers["consolidation_components"] = "La controladora y sus subsidiarias se consolidan con perimetro definido."
        round_two_answers["consolidation_process"] = "La matriz la prepara contabilidad, la revisa finanzas y la aprueba gerencia."

    second_round = update_profile_answers("cliente_confirmado", round_two_answers)
    assert second_round["unanswered_critical"] == []
    assert second_round["pending_confirmations"] == []

    confirmed = confirm_profile_draft("cliente_confirmado", "auditor")
    assert confirmed["status"] == "confirmed"
    assert confirmed["confirmed_by"] == "auditor"

    edited = update_profile_answers(
        "cliente_confirmado",
        {"revenue_measurement_model": "Precio fijo con soporte de contrato y factura revisada."},
    )
    assert edited["answers"]["revenue_measurement_model"] == "Precio fijo con soporte de contrato y factura revisada."
    assert edited["answers"]["revenue_process_detail"] == round_two_answers["revenue_process_detail"]
    assert any(question["round"] >= 1 for question in edited["questions"])
