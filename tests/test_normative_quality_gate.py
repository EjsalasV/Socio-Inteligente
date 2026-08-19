from __future__ import annotations

from pathlib import Path

from backend.services import rag_chat_service
from backend.services.normative_quality_service import (
    INDEX_VERSION,
    active_markdown_files,
    apply_quality_gate,
    source_signature,
    redact_unsupported_normative_units,
    validate_normative_output,
)


def _verified_metadata() -> dict[str, str]:
    return {
        "tipo_contenido": "oficial",
        "estado_revision": "verificado",
        "autoridad": "IAASB",
        "version": "NIA 315 Revisada 2019",
        "jurisdiccion": "Internacional",
        "vigente_desde": "2021-12-15",
        "url_oficial": "https://www.iaasb.org/publications/example",
        "localizador": "parrafos 25-26",
        "licencia": "permiso_otorgado_para_ia para el corpus de prueba",
        "aplicacion_local": "Aplicable en Ecuador para el periodo de prueba",
        "revisado_por": "Profesional de prueba",
        "rol_revisor": "Socio de auditoria",
        "fecha_revision": "2026-08-09",
        "alcance_revision": "Autoridad, version, vigencia, aplicacion y localizador",
        "evidencia_revision": "TEST-REVIEW-001",
    }


def test_incomplete_normative_source_is_orientation_only() -> None:
    metadata = apply_quality_gate({"norma": "NIA 315", "version": "vigente"}, "data/conocimiento_normativo/nias/nia_315.md")

    assert metadata["tipo_contenido"] == "pendiente_revision"
    assert metadata["estado_revision"] == "pendiente"
    assert metadata["citation_eligible"] is False
    assert "version_no_identificable" in metadata["quality_issues"]


def test_unverified_normative_obligation_is_blocked() -> None:
    pending = apply_quality_gate({"norma": "NIA 240"}, "data/conocimiento_normativo/nias/nia_240.md")

    validation = validate_normative_output(
        "Fraude (NIA 240): la presuncion sobre ingresos es obligatoria.",
        [pending],
    )

    assert validation.allowed is False
    assert any(issue.startswith("atribucion_sin_fuente") for issue in validation.issues)


def test_unsupported_quantitative_selection_is_blocked() -> None:
    validation = validate_normative_output(
        "Revisa las ultimas 10 facturas de diciembre y las primeras 10 facturas de enero.",
        [],
    )

    assert validation.allowed is False
    assert "seleccion_cuantitativa_sin_base" in validation.issues


def test_redaction_removes_only_unsupported_normative_unit() -> None:
    answer = "Solicita el auxiliar de cartera. La NIA 240 exige revisar fraude. Documenta la conclusion humana."
    validation = validate_normative_output(answer, [])

    redacted = redact_unsupported_normative_units(answer, validation.issues)

    assert "Solicita el auxiliar" in redacted
    assert "NIA 240" not in redacted
    assert "Documenta la conclusion" in redacted
    assert validate_normative_output(redacted, []).allowed is True


def test_complete_verified_source_is_citation_eligible() -> None:
    metadata = apply_quality_gate(_verified_metadata(), "data/conocimiento_normativo/nias/nia_315.md")

    assert metadata["citation_eligible"] is True
    assert metadata["quality_issues"] == []


def test_verified_label_without_review_evidence_does_not_enable_citations() -> None:
    raw = _verified_metadata()
    for field in ("revisado_por", "rol_revisor", "fecha_revision", "alcance_revision", "evidencia_revision"):
        raw.pop(field)

    metadata = apply_quality_gate(raw, "data/conocimiento_normativo/nias/nia_315.md")

    assert metadata["citation_eligible"] is False
    assert "falta_revisado_por" in metadata["quality_issues"]
    assert "falta_evidencia_revision" in metadata["quality_issues"]


def test_restricted_source_without_safe_ingestion_mode_is_flagged() -> None:
    metadata = apply_quality_gate(
        {
            "licencia": "Copyright IFAC; permiso escrito pendiente",
            "modo_ingesta": "full_text",
        },
        "data/conocimiento_normativo/nias/nia_240.md",
    )

    assert "ingesta_restringida_sin_metadata_only" in metadata["quality_issues"]


def test_metadata_only_ingestion_excludes_protected_body() -> None:
    metadata = {
        "norma": "NIA 240",
        "autoridad": "IAASB",
        "version": "Manual 2025",
        "vigente_desde": "2009-12-15",
        "aplicacion_local": "Ecuador bajo SCVS",
        "url_oficial": "https://www.iaasb.org/example",
        "licencia": "Copyright IFAC; permiso escrito pendiente",
        "modo_ingesta": "metadata_only",
        "temas": ["fraude", "ingresos"],
    }

    text = rag_chat_service._ingestion_text(metadata, "TEXTO PROTEGIDO QUE NO DEBE INDEXARSE")

    assert "TEXTO PROTEGIDO" not in text
    assert "NIA 240" in text
    assert "excluido del indice" in text


def test_legacy_international_source_is_safe_by_default() -> None:
    metadata = {
        "norma": "NIA 200",
        "autoridad": "IAASB",
        "version": "no declarada",
        "licencia": "",
    }

    text = rag_chat_service._ingestion_text(
        metadata,
        "CUERPO INTERNACIONAL HEREDADO",
        "data/conocimiento_normativo/nias/nia_200.md",
    )

    assert metadata["modo_ingesta"] == "metadata_only"
    assert "CUERPO INTERNACIONAL HEREDADO" not in text


def test_internal_professional_interpretation_is_retrievable_but_not_citable() -> None:
    raw = {
        "norma": "NIA 315",
        "autoridad": "IAASB",
        "version": "NIA 315 Revisada 2019",
        "jurisdiccion": "internacional",
        "vigente_desde": "2021-12-15",
        "url_oficial": "https://www.iaasb.org/example",
        "licencia": "Copyright IFAC; permiso pendiente",
        "aplicacion_local": "Ecuador bajo SCVS",
        "modo_ingesta": "interpretacion_profesional",
        "origen_contenido": "interpretacion_profesional_interna",
    }
    metadata = apply_quality_gate(raw, "data/conocimiento_normativo/nias/nia_315.md")
    text = rag_chat_service._ingestion_text(
        metadata,
        "Nuestra guia practica relaciona alertas, riesgos y aseveraciones.",
        "data/conocimiento_normativo/nias/nia_315.md",
    )

    assert "Nuestra guia practica" in text
    assert "INTERPRETACION PROFESIONAL INTERNA" in text
    assert metadata["citation_eligible"] is False
    assert "ingesta_restringida_sin_metadata_only" not in metadata["quality_issues"]
    assert "ingesta_internacional_no_restringida" not in metadata["quality_issues"]

    chunks = rag_chat_service._split_chunks("nia_315.md", text, metadata)
    assert chunks
    assert all("INTERPRETACION PROFESIONAL INTERNA" in excerpt for _, excerpt, _ in chunks)


def test_active_files_exclude_backup_directories(tmp_path: Path) -> None:
    active = tmp_path / "nias" / "nia_315.md"
    backup = tmp_path / "_backup" / "nias" / "nia_315.md"
    active.parent.mkdir(parents=True)
    backup.parent.mkdir(parents=True)
    active.write_text("active", encoding="utf-8")
    backup.write_text("backup", encoding="utf-8")

    assert active_markdown_files(tmp_path) == [active]


def test_source_signature_changes_with_content(tmp_path: Path) -> None:
    source = tmp_path / "nias" / "nia_315.md"
    source.parent.mkdir(parents=True)
    source.write_text("first", encoding="utf-8")
    first = source_signature(tmp_path)
    source.write_text("second", encoding="utf-8")

    assert source_signature(tmp_path) != first


def test_index_rebuilds_when_active_source_changes(tmp_path: Path, monkeypatch) -> None:
    knowledge_root = tmp_path / "data" / "conocimiento_normativo"
    source = knowledge_root / "nias" / "nia_315.md"
    index_path = tmp_path / "data" / "rag" / "normativo_index.json"
    source.parent.mkdir(parents=True)
    source.write_text("# NIA 315\n\nContenido normativo suficientemente largo para generar un fragmento inicial.", encoding="utf-8")
    monkeypatch.setattr(rag_chat_service, "ROOT", tmp_path)
    monkeypatch.setattr(rag_chat_service, "KNOWLEDGE_ROOT", knowledge_root)
    monkeypatch.setattr(rag_chat_service, "RAG_INDEX_PATH", index_path)

    first = rag_chat_service._build_normative_index(force=False)
    source.write_text("# NIA 315\n\nContenido normativo modificado y suficientemente largo para regenerar el indice.", encoding="utf-8")
    second = rag_chat_service._build_normative_index(force=False)

    assert first["index_version"] == INDEX_VERSION
    assert first["source_signature"] != second["source_signature"]


def test_only_verified_sources_become_citations() -> None:
    verified = apply_quality_gate(_verified_metadata(), "data/conocimiento_normativo/nias/nia_315.md")
    pending = apply_quality_gate({"norma": "NIA 240"}, "data/conocimiento_normativo/nias/nia_240.md")
    chunks = [
        rag_chat_service.RetrievedChunk("verified.md", "Verified excerpt", 8.0, verified),
        rag_chat_service.RetrievedChunk("pending.md", "Pending excerpt", 7.0, pending),
    ]

    citations = rag_chat_service.build_verified_citations(chunks)

    assert len(citations) == 1
    assert citations[0]["source"] == "verified.md"
    assert citations[0]["estado_revision"] == "verificado"


def test_answer_only_exposes_verified_sources_it_references() -> None:
    verified = apply_quality_gate(_verified_metadata(), "data/conocimiento_normativo/nias/nia_315.md")
    second_verified = apply_quality_gate(
        {**_verified_metadata(), "version": "NIA 330", "localizador": "parrafo 6"},
        "data/conocimiento_normativo/nias/nia_330.md",
    )
    chunks = [
        rag_chat_service.RetrievedChunk("nia_315.md", "First excerpt", 8.0, verified),
        rag_chat_service.RetrievedChunk("nia_330.md", "Second excerpt", 7.0, second_verified),
    ]

    citations = rag_chat_service._citations_used_in_answer("Conclusion respaldada [FUENTE 2].", chunks)

    assert [citation["source"] for citation in citations] == ["nia_330.md"]


def test_web_fallback_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_AUDIT_WEB_FALLBACK", raising=False)
    assert rag_chat_service._web_fallback_enabled() is False
    monkeypatch.setenv("ENABLE_AUDIT_WEB_FALLBACK", "true")
    assert rag_chat_service._web_fallback_enabled() is True
