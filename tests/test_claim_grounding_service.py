from backend.services.claim_grounding_service import redact_unsupported_claim_units, validate_client_grounding


def _profile() -> dict:
    return {
        "cuestionario_auditoria": {
            "presion_resultados": False,
            "partes_relacionadas": False,
            "ingresos_complejos": False,
        }
    }


def test_confirmed_false_profile_fact_blocks_assertion() -> None:
    result = validate_client_grounding(
        "El corte de ingresos es inherentemente complejo para este cliente.",
        _profile(),
    )

    assert result.allowed is False
    assert any(issue.startswith("contradice_perfil:ingresos_complejos") for issue in result.issues)


def test_hypothesis_does_not_override_confirmed_false_fact() -> None:
    result = validate_client_grounding(
        "Debe investigarse si existen partes relacionadas; no esta confirmado.",
        _profile(),
    )

    assert result.allowed is True


def test_prior_period_amount_requires_temporal_label() -> None:
    chunks = [
        {
            "excerpt": "En 2024 existian cuentas antiguas por US$40,746.",
            "metadata": {
                "temporal_status": "antecedente_periodo_anterior",
                "document_period": "2024",
            },
        }
    ]

    blocked = validate_client_grounding("La cartera vencida actual es US$40,746.", _profile(), chunks)
    allowed = validate_client_grounding("El antecedente 2024 reporto US$40,746.", _profile(), chunks)

    assert blocked.allowed is False
    assert "importe_previo_como_actual:1" in blocked.issues
    assert allowed.allowed is True


def test_unsupported_process_fact_is_blocked_but_hypothesis_is_allowed() -> None:
    blocked = validate_client_grounding("El area tiene manejo de efectivo.", _profile())
    allowed = validate_client_grounding("Debe investigarse si el area tiene manejo de efectivo.", _profile())

    assert blocked.allowed is False
    assert any(issue.startswith("proceso_no_documentado:manejo_efectivo") for issue in blocked.issues)
    assert allowed.allowed is True


def test_redaction_removes_only_unsupported_client_fact() -> None:
    answer = (
        "Solicita el auxiliar de cartera. "
        "El cliente tiene partes relacionadas. "
        "La seleccion queda pendiente de poblacion y materialidad."
    )
    validation = validate_client_grounding(answer, _profile())

    redacted = redact_unsupported_claim_units(answer, validation.issues)

    assert "Solicita el auxiliar" in redacted
    assert "partes relacionadas" not in redacted
    assert "seleccion queda pendiente" in redacted
    assert validate_client_grounding(redacted, _profile()).allowed is True
