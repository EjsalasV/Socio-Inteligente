from backend.services.normative_version_service import (
    build_profile_version_context,
    evaluate_matrix_review,
    resolve_normative_version,
)


def _resolve(**overrides):
    values = {
        "framework": "NIIF para PYMES",
        "period_start": "2026-01-01",
        "regulator": "scvs_general",
    }
    values.update(overrides)
    return resolve_normative_version(**values)


def test_missing_framework_and_period_blocks_resolution():
    result = resolve_normative_version(framework="", period_start="", regulator="scvs_general")

    assert result["status"] == "blocked_missing_context"
    assert len(result["questions"]) == 2
    assert result["citation_allowed"] is False


def test_unknown_or_special_regulator_is_outside_matrix_scope():
    result = _resolve(regulator="Superintendencia de Bancos")

    assert result["status"] == "outside_scope"
    assert "solo SCVS" in result["questions"][0]


def test_sme_uses_2015_edition_before_2027():
    result = _resolve(period_start="2026-01-01")

    assert result["status"] == "applicable"
    assert result["edition"] == "NIIF para las PYMES segunda edicion 2015"
    assert result["citation_allowed"] is False


def test_sme_uses_2025_edition_from_2027():
    result = _resolve(period_start="2027-01-01")

    assert result["status"] == "applicable"
    assert result["edition"] == "NIIF para las PYMES tercera edicion 2025"


def test_sme_early_adoption_requires_documented_evidence():
    blocked = _resolve(early_adoption=True)
    allowed = _resolve(
        early_adoption=True,
        evidence=["entity_election", "policy_disclosure"],
    )

    assert blocked["status"] == "blocked_early_adoption_evidence"
    assert blocked["missing_evidence"] == ["entity_election", "policy_disclosure"]
    assert allowed["status"] == "conditional_early_adoption"
    assert allowed["early_adoption"] is True


def test_full_ifrs_early_adoption_also_requires_issuer_permission():
    result = _resolve(
        framework="NIIF completas",
        early_adoption=True,
        evidence=["entity_election", "policy_disclosure"],
    )

    assert result["status"] == "blocked_early_adoption_evidence"
    assert result["missing_evidence"] == ["issuer_allows_early_adoption"]


def test_nia_240_switches_at_its_effective_date():
    previous = _resolve(framework="NIAs", standard="NIA 240", period_start="2026-01-01")
    revised = _resolve(framework="NIAs", standard="NIA 240", period_start="2026-12-15")

    assert previous["edition"] == "NIA 240 anterior a la revision de 2025"
    assert revised["edition"] == "NIA 240 Revisada 2025"


def test_nia_240_early_adoption_is_conditional_on_engagement_evidence():
    result = _resolve(
        framework="NIAs",
        standard="NIA 240",
        early_adoption=True,
        evidence=["engagement_adoption_decision", "jurisdiction_assessment"],
    )

    assert result["status"] == "conditional_early_adoption"
    assert result["citation_allowed"] is False


def test_other_pilot_isa_versions_do_not_apply_2026_proposals():
    nia_315 = _resolve(framework="NIAs", standard="NIA 315")
    nia_330 = _resolve(framework="NIAs", standard="NIA 330")
    nia_500 = _resolve(framework="NIAs", standard="NIA 500")

    assert nia_315["edition"] == "NIA 315 Revisada 2019"
    assert "propuesta 2026 no aplicable" in nia_330["edition"]
    assert "propuesta 2026 no aplicable" in nia_500["edition"]


def test_profile_context_infers_general_scvs_and_keeps_matrix_non_citable():
    context = build_profile_version_context(
        {
            "cliente": {"pais": "Ecuador"},
            "encargo": {
                "anio_activo": 2025,
                "marco_referencial": "NIIF para PYMES",
                "norma_auditoria": "NIAs",
            },
            "cuestionario_auditoria": {"regulado": False},
        }
    )

    assert "scvs_general_inferred" in context
    assert "segunda edicion 2015" in context
    assert "METODOLOGIA, NO CITA" in context


def test_regulated_profile_requires_regulator_confirmation():
    context = build_profile_version_context(
        {
            "cliente": {"pais": "Ecuador"},
            "encargo": {"anio_activo": 2025, "marco_referencial": "NIIF"},
            "cuestionario_auditoria": {"regulado": True},
        }
    )

    assert "Regulador: no confirmado" in context
    assert "outside_scope" in context
    assert "Confirmar regulador" in context


def test_current_matrix_review_is_pending_and_not_approved():
    result = evaluate_matrix_review()

    assert result["status"] == "pending"
    assert result["approved"] is False
    assert result["issues"] == []


def test_matrix_change_invalidates_a_previous_approval(tmp_path):
    matrix = tmp_path / "matrix.yaml"
    review = tmp_path / "review.yaml"
    matrix.write_text("matrix_version: 1\n", encoding="utf-8")
    review.write_text(
        "status: approved\n"
        "matrix_sha256: invalid\n"
        "reviewer_name: Revisor\n"
        "reviewer_role: Socio\n"
        "review_date: 2026-08-09\n"
        "scope: Matriz completa\n"
        "conclusion: Aprobada\n"
        "evidence_reference: ACTA-001\n",
        encoding="utf-8",
    )

    result = evaluate_matrix_review(matrix, review)

    assert result["approved"] is False
    assert "matrix_hash_mismatch" in result["issues"]
