from backend.services.entity_profile_service import _is_pending_answer
from backend.services.rag_chat_service import _strip_repair_preamble


def test_concrete_finding_status_is_not_treated_as_unanswered() -> None:
    answer = (
        "Se evidenció una mejora parcial; varias deficiencias continúan pendientes, "
        "principalmente las relacionadas con cuentas por cobrar."
    )

    assert _is_pending_answer(answer) is False


def test_genuine_uncertainty_remains_pending() -> None:
    assert _is_pending_answer("Falta confirmar quién realiza la aprobación final.") is True
    assert _is_pending_answer("Pendiente") is True


def test_internal_repair_preamble_is_not_published() -> None:
    assert _strip_repair_preamble("Claro, aquí tienes la respuesta reescrita:\nContenido final") == "Contenido final"
