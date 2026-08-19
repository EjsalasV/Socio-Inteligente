from pathlib import Path

from backend.schemas import ChatFeedbackRequest, PilotSurveyRequest


ROOT = Path(__file__).resolve().parents[1]


def test_alpha_privacy_rule_forbids_training_with_client_files() -> None:
    policy = (ROOT / "legal" / "POLITICA_PRIVACIDAD.md").read_text(encoding="utf-8").lower()

    assert "no usa expedientes" in policy
    assert "entrenar modelos" in policy
    assert "datos ficticios o anonimizados" in policy


def test_alpha_acceptance_guide_covers_pilot_scope_and_feedback() -> None:
    guide = (ROOT / "docs" / "GUIA_ACEPTACION_ALPHA_INGRESOS_CXC.md").read_text(encoding="utf-8").lower()

    assert "ingresos y cuentas por cobrar" in guide
    assert "15. consultar la traza" in guide
    assert "disposicion a volver a usar y pagar" in guide


def test_alpha_feedback_contracts_enforce_bounded_metrics() -> None:
    feedback = ChatFeedbackRequest(trace_id="trace-1", outcome="incorrect", issue_type="fact")
    survey = PilotSurveyRequest(
        time_saved_minutes=25,
        understanding_before=2,
        understanding_after=4,
        would_reuse=True,
        willing_to_pay=False,
    )

    assert feedback.outcome == "incorrect"
    assert survey.understanding_after > survey.understanding_before
