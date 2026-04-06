from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

from backend.routes import reportes
from backend.schemas import InternalControlLetterRequest, NIIFPymesDraftRequest, UserContext
from backend.services import report_generation_service as rgs


def _user(role: str = "manager") -> UserContext:
    return UserContext(
        sub="tester",
        org_id="org_demo",
        allowed_clientes=["bf_holding_2025", "cliente_demo"],
        role=role,
    )


def test_internal_control_request_max_findings_bounds() -> None:
    req = InternalControlLetterRequest(max_findings=25)
    assert req.max_findings == 25
    with pytest.raises(Exception):
        InternalControlLetterRequest(max_findings=0)


def test_niif_request_enum_and_defaults() -> None:
    req = NIIFPymesDraftRequest()
    assert req.ifrs_for_smes_version in {"2015", "2025"}
    assert req.include_policy_section is True


def test_build_and_render_internal_control_letter_structure() -> None:
    doc = rgs.build_internal_control_letter(
        company_name="ACME S.A.",
        period_end="2025-12-31",
        recipient="Gerencia General",
        findings=[
            {
                "id": "OBS-01",
                "titulo": "Segregacion de funciones",
                "area": "Tesoreria",
                "prioridad": "alta",
                "condicion": "No existe segregacion formal.",
                "criterio": "Politica interna de control.",
                "causa": "Estructura reducida.",
                "efecto": "Riesgo de error material.",
                "recomendacion": "Definir matriz de autorizaciones.",
                "respuesta_gerencia": "",
            }
        ],
        include_management_response=True,
    )
    md = rgs.render_internal_control_letter_markdown(doc)
    assert "BORRADOR" in md
    assert "Segregacion de funciones" in md
    assert "Comentarios de la Administración" in md
    assert "ASPECTOS DE MAYOR INTERÉS" in md


def test_internal_control_finding_classification_and_pending_comment() -> None:
    doc = rgs.build_internal_control_letter(
        company_name="ACME S.A.",
        period_end="2025-12-31",
        recipient="Gerencia General",
        findings=[
            {
                "id": "OBS-01",
                "titulo": "Riesgo alto",
                "prioridad": "alta",
                "observacion": "obs alta",
                "recomendacion": "rec alta",
                "comentarios_administracion": "",
            },
            {
                "id": "OBS-02",
                "titulo": "Riesgo medio",
                "prioridad": "media",
                "observacion": "obs media",
                "recomendacion": "rec media",
                "comentarios_administracion": "ok",
            },
        ],
        include_management_response=True,
    )
    major = doc.get("major_interest_findings") or []
    control = doc.get("internal_control_findings") or []
    assert len(major) == 1
    assert len(control) == 1
    assert (major[0].get("comentarios_administracion") or "") == "[[PENDIENTE]]"


def test_internal_control_letter_with_zero_findings_keeps_structure() -> None:
    doc = rgs.build_internal_control_letter(
        company_name="ACME S.A.",
        period_end="2025-12-31",
        recipient="Gerencia General",
        findings=[],
        include_management_response=True,
    )
    assert "cover" in doc
    assert "contenido" in doc
    assert "letter_intro" in doc
    assert isinstance(doc.get("major_interest_findings"), list)
    assert isinstance(doc.get("internal_control_findings"), list)
    md = rgs.render_internal_control_letter_markdown(doc)
    assert "ASPECTOS DE MAYOR INTERÉS" in md
    assert "ASPECTOS DE CONTROL INTERNO" in md


def test_internal_control_letter_uses_recipient_in_locked_template() -> None:
    doc = rgs.build_internal_control_letter(
        company_name="ACME S.A.",
        period_end="2025-12-31",
        recipient="Gerencia Financiera",
        findings=[],
        include_management_response=True,
    )
    recipient_block = ((doc.get("letter_intro") or {}) if isinstance(doc.get("letter_intro"), dict) else {}).get("recipient_block")
    assert "Gerencia Financiera" in str(recipient_block or "")


def test_generate_niif_draft_fallback_metadata() -> None:
    out = rgs.generate_niif_pymes_draft(
        "cliente_demo",
        ifrs_for_smes_version="2025",
        early_adoption=False,
        include_policy_section=True,
        requested_by="tester",
    )
    meta = out.get("generation_metadata") or {}
    assert meta.get("source") in {"fallback", "llm"}
    assert meta.get("template_mode") in {"custom", "default", "fallback"}
    assert "document" in out
    assert "sections" in (out.get("document") or {})
    assert "content" in out
    artifacts = out.get("artifacts") or []
    assert len(artifacts) >= 2
    assert any(a.get("artifact_type") == "docx" for a in artifacts if isinstance(a, dict))


def test_route_rejects_early_adoption_for_2015(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reportes, "authorize_cliente_access", lambda cliente_id, user: None)
    payload = NIIFPymesDraftRequest(ifrs_for_smes_version="2015", early_adoption=True)
    with pytest.raises(HTTPException) as exc:
        reportes.post_niif_pymes_draft("cliente_demo", payload=payload, user=_user())
    assert exc.value.status_code == 422


def test_route_normalizes_empty_recipient(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reportes, "authorize_cliente_access", lambda cliente_id, user: None)

    def _fake_generate(*args, **kwargs):
        return {
            "content": "ok",
            "document": {"header": {"title": "x"}},
            "path": "x.md",
            "findings_count": 0,
            "recipient": "Gerencia General",
            "generation_metadata": {
                "source": "fallback",
                "provider": "fallback",
                "model": "",
                "prompt_id": "",
                "prompt_version": "",
                "generated_at": datetime.now(timezone.utc),
                "requested_by": "tester",
                "input_payload": {"recipient": "Gerencia General"},
            },
        }

    monkeypatch.setattr(reportes, "generate_internal_control_letter", _fake_generate)
    monkeypatch.setattr(
        reportes,
        "_register_generated_document",
        lambda **kwargs: {
            "document_version": 1,
            "supersedes_version": None,
            "is_current": True,
            "state": "draft",
            "diff_from_previous": {},
        },
    )
    payload = InternalControlLetterRequest(recipient="   ", include_management_response=True, max_findings=1)
    out = reportes.post_internal_control_letter("cliente_demo", payload=payload, user=_user())
    assert out.data["recipient"] == "Gerencia General"
    assert out.data["state"] == "draft"


def test_transition_rules_require_docx_for_approval() -> None:
    cliente_id = "cliente_demo"
    registry = {
        "documents": {
            "carta_control_interno": {
                "document_type": "carta_control_interno",
                "versions": [
                    {
                        "document_version": 1,
                        "is_current": True,
                        "state": "reviewed",
                        "artifacts": [{"artifact_type": "markdown"}],
                    }
                ],
            }
        }
    }
    reportes._write_registry(cliente_id, registry)
    with pytest.raises(HTTPException) as exc:
        reportes._transition_document_state(
            cliente_id=cliente_id,
            document_type="carta_control_interno",
            target_state="approved",
            changed_by="tester",
            changed_role="gerente",
        )
    assert exc.value.status_code == 422


def test_transition_staff_cannot_mark_reviewed() -> None:
    cliente_id = "cliente_demo"
    registry = {
        "documents": {
            "carta_control_interno": {
                "document_type": "carta_control_interno",
                "versions": [{"document_version": 1, "is_current": True, "state": "draft", "artifacts": []}],
            }
        }
    }
    reportes._write_registry(cliente_id, registry)
    with pytest.raises(HTTPException) as exc:
        reportes._transition_document_state(
            cliente_id=cliente_id,
            document_type="carta_control_interno",
            target_state="reviewed",
            changed_by="u_staff",
            changed_role="staff",
        )
    assert exc.value.status_code == 403


def test_transition_gerente_can_approve_from_reviewed() -> None:
    cliente_id = "cliente_demo"
    registry = {
        "documents": {
            "carta_control_interno": {
                "document_type": "carta_control_interno",
                "versions": [
                    {
                        "document_version": 2,
                        "is_current": True,
                        "state": "reviewed",
                        "artifacts": [{"artifact_type": "docx"}],
                        "generation_metadata": {
                            "source": "fallback",
                            "template_mode": "default",
                            "template_version": "v1",
                            "document_type": "carta_control_interno",
                            "requested_by": "u_senior",
                            "generated_at": datetime.now(timezone.utc).isoformat(),
                            "required_sections": ["cover", "contenido", "letter_intro", "major_interest_findings", "internal_control_findings", "closing"],
                        },
                        "document_snapshot": {
                            "cover": {"period_end": "2025-12-31", "ruc": "1234567890001"},
                            "contenido": "ok",
                            "letter_intro": "ok",
                            "major_interest_findings": [],
                            "internal_control_findings": [],
                            "findings": [{"id": "OBS-01", "titulo": "Hallazgo demo"}],
                            "closing": "ok",
                        },
                    }
                ],
            }
        }
    }
    reportes._write_registry(cliente_id, registry)
    reportes._initialize_section_links_for_version(
        cliente_id=cliente_id,
        document_type="carta_control_interno",
        document_version=2,
        sections=[
            {"section_id": "hallazgo:OBS-01", "section_title": "Hallazgo demo", "is_required": True, "status": "pending", "sources": []},
        ],
    )
    reportes.post_document_section_evidence(
        cliente_id,
        "carta_control_interno",
        "hallazgo:OBS-01",
        payload={"source_type": "supporting_document", "source_id": "wp_01", "reference": "WP-01", "label": "Cedula hallazgos"},
        user=_user(role="senior"),
    )
    updated = reportes._transition_document_state(
        cliente_id=cliente_id,
        document_type="carta_control_interno",
        target_state="approved",
        changed_by="u_gerente",
        changed_role="gerente",
        reason="Revision completada",
    )
    assert updated.get("state") == "approved"
    history = updated.get("state_history") or []
    assert history[-1]["from_state"] == "reviewed"
    assert history[-1]["to_state"] == "approved"


def test_transition_only_socio_can_issue() -> None:
    cliente_id = "cliente_demo"
    registry = {
        "documents": {
            "carta_control_interno": {
                "document_type": "carta_control_interno",
                "versions": [
                    {
                        "document_version": 3,
                        "is_current": True,
                        "state": "approved",
                        "artifacts": [{"artifact_type": "docx"}],
                        "generation_metadata": {
                            "source": "fallback",
                            "template_mode": "default",
                            "template_version": "v1",
                            "document_type": "carta_control_interno",
                            "requested_by": "u_senior",
                            "generated_at": datetime.now(timezone.utc).isoformat(),
                            "required_sections": ["cover", "contenido", "letter_intro", "major_interest_findings", "internal_control_findings", "closing"],
                        },
                        "document_snapshot": {
                            "cover": {"period_end": "2025-12-31", "ruc": "1234567890001"},
                            "contenido": "ok",
                            "letter_intro": "ok",
                            "major_interest_findings": [],
                            "internal_control_findings": [],
                            "findings": [{"id": "OBS-02", "titulo": "Hallazgo demo emision"}],
                            "closing": "ok",
                        },
                    }
                ],
            }
        }
    }
    reportes._write_registry(cliente_id, registry)
    reportes._initialize_section_links_for_version(
        cliente_id=cliente_id,
        document_type="carta_control_interno",
        document_version=3,
        sections=[
            {"section_id": "hallazgo:OBS-02", "section_title": "Hallazgo demo emision", "is_required": True, "status": "pending", "sources": []},
        ],
    )
    reportes.post_document_section_evidence(
        cliente_id,
        "carta_control_interno",
        "hallazgo:OBS-02",
        payload={"source_type": "supporting_document", "source_id": "wp_issued", "reference": "WP-02", "label": "Soporte emisión"},
        user=_user(role="senior"),
    )
    with pytest.raises(HTTPException) as exc:
        reportes._transition_document_state(
            cliente_id=cliente_id,
            document_type="carta_control_interno",
            target_state="issued",
            changed_by="u_gerente",
            changed_role="gerente",
        )
    assert exc.value.status_code == 403

    updated = reportes._transition_document_state(
        cliente_id=cliente_id,
        document_type="carta_control_interno",
        target_state="issued",
        changed_by="u_socio",
        changed_role="socio",
    )
    assert updated.get("state") == "issued"


def test_quality_check_has_score_and_semaphore() -> None:
    version = {
        "state": "reviewed",
        "artifacts": [{"artifact_type": "docx"}],
        "generation_metadata": {
            "source": "fallback",
            "template_mode": "default",
            "template_version": "v1",
            "document_type": "carta_control_interno",
            "requested_by": "u1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "required_sections": ["cover", "contenido", "letter_intro", "major_interest_findings", "internal_control_findings", "closing"],
        },
        "document_snapshot": {
            "cover": {"period_end": "2025-12-31", "ruc": "1234567890001"},
            "contenido": "ok",
            "letter_intro": "ok",
            "major_interest_findings": [],
            "internal_control_findings": [],
            "findings": [],
            "closing": "ok",
        },
    }
    qc = reportes._quality_check_version(version)
    assert isinstance(qc.get("score"), int)
    assert qc.get("semaphore") in {"red", "yellow", "green"}


def test_issue_endpoint_generates_pdf_artifact(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(reportes, "authorize_cliente_access", lambda cliente_id, user: None)
    docx_path = tmp_path / "doc.docx"
    docx_path.write_bytes(b"fake-docx")
    registry = {
        "documents": {
            "carta_control_interno": {
                "document_type": "carta_control_interno",
                "versions": [
                    {
                        "document_version": 4,
                        "is_current": True,
                        "state": "issued",
                        "artifacts": [{"artifact_type": "docx", "artifact_path": str(docx_path)}],
                        "generation_metadata": {"template_version": "v1"},
                    }
                ],
            }
        }
    }
    monkeypatch.setattr(
        reportes,
        "_transition_document_state",
        lambda **kwargs: {"document_version": 4, "state": "issued", "artifacts": [{"artifact_type": "docx", "artifact_path": str(docx_path)}]},
    )
    monkeypatch.setattr(reportes, "_read_registry", lambda cliente_id: registry)
    monkeypatch.setattr(reportes, "_write_registry", lambda cliente_id, payload: None)
    monkeypatch.setattr(reportes, "_emit_pdf_from_docx", lambda **kwargs: b"%PDF-1.4 fake")

    out = reportes.post_document_issue("cliente_demo", "carta_control_interno", payload={}, user=_user(role="socio"))
    assert out.data["state"] == "issued"
    assert out.data["pdf_artifact_hash"]


def test_section_links_create_and_read() -> None:
    cliente_id = "cliente_demo"
    registry = {
        "documents": {
            "niif_pymes_borrador": {
                "document_type": "niif_pymes_borrador",
                "versions": [
                    {
                        "document_version": 1,
                        "is_current": True,
                        "state": "draft",
                        "document_snapshot": {"sections": [{"id": "nota_1", "title": "Informacion general", "content": "x"}]},
                        "artifacts": [],
                        "generation_metadata": {"required_sections": ["nota_1"]},
                    }
                ],
            }
        }
    }
    reportes._write_registry(cliente_id, registry)
    reportes._initialize_section_links_for_version(
        cliente_id=cliente_id,
        document_type="niif_pymes_borrador",
        document_version=1,
        sections=[{"section_id": "nota_1", "section_title": "Informacion general", "is_required": True, "status": "pending", "sources": []}],
    )
    out = reportes.post_document_section_evidence(
        cliente_id,
        "niif_pymes_borrador",
        "nota_1",
        payload={"source_type": "trial_balance", "source_id": "tb_2025_v3", "reference": "AR-110101", "label": "Saldo CxC"},
        user=_user(role="staff"),
    )
    assert out.data["section"]["status"] in {"supported", "pending", "missing_required_support"}
    sections = reportes.get_document_sections(cliente_id, "niif_pymes_borrador", user=_user(role="staff"))
    assert sections.data["coverage"]["total_sections"] >= 1


def test_evidence_gate_endpoint_blocks_when_critical_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reportes, "authorize_cliente_access", lambda cliente_id, user: None)
    cliente_id = "cliente_demo"
    registry = {
        "documents": {
            "niif_pymes_borrador": {
                "document_type": "niif_pymes_borrador",
                "versions": [
                    {
                        "document_version": 5,
                        "is_current": True,
                        "state": "reviewed",
                        "artifacts": [{"artifact_type": "docx"}],
                        "generation_metadata": {
                            "source": "fallback",
                            "template_mode": "default",
                            "template_version": "v1",
                            "document_type": "niif_pymes_borrador",
                            "requested_by": "u_senior",
                            "generated_at": datetime.now(timezone.utc).isoformat(),
                            "required_sections": ["base_preparacion", "notas_especificas"],
                        },
                        "document_snapshot": {
                            "sections": [
                                {"id": "base_preparacion", "title": "Base de preparación"},
                                {"id": "notas_especificas", "title": "Notas específicas"},
                            ]
                        },
                    }
                ],
            }
        }
    }
    reportes._write_registry(cliente_id, registry)
    reportes._initialize_section_links_for_version(
        cliente_id=cliente_id,
        document_type="niif_pymes_borrador",
        document_version=5,
        sections=[
            {"section_id": "base_preparacion", "section_title": "Base de preparación", "is_required": True, "status": "pending", "sources": []},
            {"section_id": "notas_especificas", "section_title": "Notas específicas", "is_required": True, "status": "pending", "sources": []},
        ],
    )
    out = reportes.get_document_evidence_gate(cliente_id, "niif_pymes_borrador", user=_user(role="senior"))
    assert out.data["can_approve"] is False
    assert out.data["can_issue"] is False
    assert out.data["coverage_percent"] < out.data["minimum_required"]
    assert len(out.data["blocking_sections"]) >= 1


def test_transition_blocks_approve_without_critical_support() -> None:
    cliente_id = "cliente_demo"
    registry = {
        "documents": {
            "carta_control_interno": {
                "document_type": "carta_control_interno",
                "versions": [
                    {
                        "document_version": 6,
                        "is_current": True,
                        "state": "reviewed",
                        "artifacts": [{"artifact_type": "docx"}],
                        "generation_metadata": {
                            "source": "fallback",
                            "template_mode": "default",
                            "template_version": "v1",
                            "document_type": "carta_control_interno",
                            "requested_by": "u_senior",
                            "generated_at": datetime.now(timezone.utc).isoformat(),
                            "required_sections": ["cover", "contenido", "letter_intro", "major_interest_findings", "internal_control_findings", "closing"],
                        },
                        "document_snapshot": {
                            "cover": {"period_end": "2025-12-31", "ruc": "1234567890001"},
                            "contenido": "ok",
                            "letter_intro": "ok",
                            "major_interest_findings": [],
                            "internal_control_findings": [],
                            "findings": [{"id": "OBS-03", "titulo": "Hallazgo bloqueante"}],
                            "closing": "ok",
                        },
                    }
                ],
            }
        }
    }
    reportes._write_registry(cliente_id, registry)
    reportes._initialize_section_links_for_version(
        cliente_id=cliente_id,
        document_type="carta_control_interno",
        document_version=6,
        sections=[
            {"section_id": "hallazgo:OBS-03", "section_title": "Hallazgo bloqueante", "is_required": True, "status": "pending", "sources": []},
        ],
    )
    with pytest.raises(HTTPException) as exc:
        reportes._transition_document_state(
            cliente_id=cliente_id,
            document_type="carta_control_interno",
            target_state="approved",
            changed_by="u_gerente",
            changed_role="gerente",
        )
    assert exc.value.status_code == 422
    assert "No se puede aprobar" in str(exc.value.detail)


def test_issue_blocks_when_ruc_missing_for_internal_control() -> None:
    cliente_id = "cliente_demo"
    registry = {
        "documents": {
            "carta_control_interno": {
                "document_type": "carta_control_interno",
                "versions": [
                    {
                        "document_version": 7,
                        "is_current": True,
                        "state": "approved",
                        "artifacts": [{"artifact_type": "docx"}],
                        "generation_metadata": {
                            "source": "fallback",
                            "template_mode": "default",
                            "template_version": "v1",
                            "document_type": "carta_control_interno",
                            "requested_by": "u_senior",
                            "generated_at": datetime.now(timezone.utc).isoformat(),
                            "required_sections": ["cover", "contenido", "letter_intro", "major_interest_findings", "internal_control_findings", "closing"],
                        },
                        "document_snapshot": {
                            "cover": {"period_end": "2025-12-31", "ruc": "[[PENDIENTE]]"},
                            "contenido": "ok",
                            "letter_intro": "ok",
                            "major_interest_findings": [],
                            "internal_control_findings": [],
                            "findings": [{"id": "OBS-07", "titulo": "Hallazgo"}],
                            "closing": "ok",
                        },
                    }
                ],
            }
        }
    }
    reportes._write_registry(cliente_id, registry)
    reportes._initialize_section_links_for_version(
        cliente_id=cliente_id,
        document_type="carta_control_interno",
        document_version=7,
        sections=[
            {"section_id": "hallazgo:OBS-07", "section_title": "Hallazgo", "is_required": True, "status": "pending", "sources": []},
        ],
    )
    reportes.post_document_section_evidence(
        cliente_id,
        "carta_control_interno",
        "hallazgo:OBS-07",
        payload={"source_type": "supporting_document", "source_id": "wp_issued", "reference": "WP-07", "label": "Soporte emisión"},
        user=_user(role="senior"),
    )
    with pytest.raises(HTTPException) as exc:
        reportes._transition_document_state(
            cliente_id=cliente_id,
            document_type="carta_control_interno",
            target_state="issued",
            changed_by="u_socio",
            changed_role="socio",
        )
    assert exc.value.status_code == 422
    assert "RUC" in str(exc.value.detail)


def test_link_evidence_validates_workpaper_exists() -> None:
    cliente_id = "cliente_demo"
    registry = {
        "documents": {
            "carta_control_interno": {
                "document_type": "carta_control_interno",
                "versions": [
                    {
                        "document_version": 8,
                        "is_current": True,
                        "state": "draft",
                        "document_snapshot": {"findings": [{"id": "OBS-08", "titulo": "Hallazgo"}]},
                        "artifacts": [],
                        "generation_metadata": {"required_sections": ["cover"]},
                    }
                ],
            }
        }
    }
    reportes._write_registry(cliente_id, registry)
    reportes._initialize_section_links_for_version(
        cliente_id=cliente_id,
        document_type="carta_control_interno",
        document_version=8,
        sections=[{"section_id": "hallazgo:OBS-08", "section_title": "Hallazgo", "is_required": True, "status": "pending", "sources": []}],
    )
    with pytest.raises(HTTPException) as exc:
        reportes.post_document_section_evidence(
            cliente_id,
            "carta_control_interno",
            "hallazgo:OBS-08",
            payload={"source_type": "workpaper", "source_id": "NO_EXISTE", "reference": "X", "label": "inválido"},
            user=_user(role="staff"),
        )
    assert exc.value.status_code == 422


def test_smoke_document_workflow_end_to_end(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Smoke test del flujo documental completo: draft -> reviewed -> approved -> issued."""
    cliente_id = "cliente_demo"
    monkeypatch.setattr(reportes, "authorize_cliente_access", lambda cliente_id, user: None)
    docx_path = tmp_path / "carta.docx"
    docx_path.write_bytes(b"fake-docx")

    def _fake_generate(*args, **kwargs):
        now = datetime.now(timezone.utc).isoformat()
        document = {
            "cover": {"company_name": "ACME S.A.", "period_end": "2025-12-31", "ruc": "1234567890001"},
            "contenido": {"major_interest_titles": ["Hallazgo crítico"], "control_titles": []},
            "letter_intro": {"city_and_date": "Quito, 5 de abril del 2026"},
            "major_interest_findings": [
                {
                    "id": "H1",
                    "titulo": "Hallazgo crítico",
                    "prioridad": "alta",
                    "categoria": "mayor_interes",
                    "observacion": "Observación de prueba",
                    "recomendacion": "Recomendación de prueba",
                    "comentarios_administracion": "Respuesta de prueba",
                }
            ],
            "internal_control_findings": [],
            "findings": [
                {
                    "id": "H1",
                    "titulo": "Hallazgo crítico",
                    "prioridad": "alta",
                    "categoria": "mayor_interes",
                    "observacion": "Observación de prueba",
                    "recomendacion": "Recomendación de prueba",
                    "comentarios_administracion": "Respuesta de prueba",
                }
            ],
            "closing": "Cierre de prueba",
        }
        return {
            "content": "Informe de prueba",
            "document": document,
            "path": str(docx_path),
            "findings_count": 1,
            "recipient": "Junta General de Accionistas",
            "generation_metadata": {
                "source": "fallback",
                "provider": "fallback",
                "model": "",
                "prompt_id": "test",
                "prompt_version": "v1",
                "document_type": "carta_control_interno",
                "template_mode": "default",
                "template_version": "v1",
                "placeholders_supported": [],
                "required_sections": [
                    "cover",
                    "contenido",
                    "letter_intro",
                    "major_interest_findings",
                    "internal_control_findings",
                    "closing",
                ],
                "optional_sections": ["findings"],
                "generated_at": now,
                "requested_by": "tester",
                "input_payload": {"recipient": "Junta General de Accionistas"},
            },
            "artifacts": [
                {"artifact_type": "markdown", "artifact_path": str(tmp_path / "carta.md"), "artifact_hash": "x1", "template_version": "v1", "size_bytes": 10},
                {"artifact_type": "docx", "artifact_path": str(docx_path), "artifact_hash": "x2", "template_version": "v1", "size_bytes": 20},
            ],
        }

    monkeypatch.setattr(reportes, "generate_internal_control_letter", _fake_generate)
    monkeypatch.setattr(reportes, "_emit_pdf_from_docx", lambda **kwargs: b"%PDF-1.4 fake")

    generated = reportes.post_internal_control_letter(
        cliente_id,
        payload=InternalControlLetterRequest(recipient="Junta General de Accionistas", include_management_response=True, max_findings=5),
        user=_user(role="staff"),
    )
    assert generated.data["state"] == "draft"

    sections_before = reportes.get_document_sections(cliente_id, "carta_control_interno", user=_user(role="staff"))
    assert sections_before.data["coverage"]["missing_required"] >= 1

    sections = sections_before.data.get("sections") or []
    for idx, sec in enumerate(sections, start=1):
        if not isinstance(sec, dict):
            continue
        section_id = str(sec.get("section_id") or "").strip()
        if not section_id:
            continue
        reportes.post_document_section_evidence(
            cliente_id,
            "carta_control_interno",
            section_id,
            payload={
                "source_type": "supporting_document",
                "source_id": f"doc-{idx}",
                "reference": f"REF-{idx}",
                "label": f"Soporte {idx}",
            },
            user=_user(role="staff"),
        )

    reviewed = reportes.post_document_state_transition(
        cliente_id,
        "carta_control_interno",
        payload={"target_state": "reviewed", "reason": "Smoke test reviewed"},
        user=_user(role="senior"),
    )
    assert reviewed.data["updated_version"]["state"] == "reviewed"

    approved = reportes.post_document_state_transition(
        cliente_id,
        "carta_control_interno",
        payload={"target_state": "approved", "reason": "Smoke test approved"},
        user=_user(role="gerente"),
    )
    assert approved.data["updated_version"]["state"] == "approved"

    issued = reportes.post_document_issue(
        cliente_id,
        "carta_control_interno",
        payload={"reason": "Smoke test issued"},
        user=_user(role="socio"),
    )
    assert issued.data["state"] == "issued"
    assert issued.data["pdf_artifact_hash"]
