from __future__ import annotations

from pathlib import Path

from backend.services import rag_chat_service
from backend.services.normative_quality_service import (
    INDEX_VERSION,
    active_markdown_files,
    apply_quality_gate,
    source_signature,
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
    }


def test_incomplete_normative_source_is_orientation_only() -> None:
    metadata = apply_quality_gate({"norma": "NIA 315", "version": "vigente"}, "data/conocimiento_normativo/nias/nia_315.md")

    assert metadata["tipo_contenido"] == "pendiente_revision"
    assert metadata["estado_revision"] == "pendiente"
    assert metadata["citation_eligible"] is False
    assert "version_no_identificable" in metadata["quality_issues"]


def test_complete_verified_source_is_citation_eligible() -> None:
    metadata = apply_quality_gate(_verified_metadata(), "data/conocimiento_normativo/nias/nia_315.md")

    assert metadata["citation_eligible"] is True
    assert metadata["quality_issues"] == []


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
