from __future__ import annotations

from pathlib import Path

import pytest

from backend.repositories.file_repository import repo
from backend.services.context_document_service import (
    delete_document,
    list_documents,
    store_document,
    validate_upload,
)


@pytest.fixture()
def isolated_client_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_clientes = tmp_path / "data" / "clientes"
    data_clientes.mkdir(parents=True)
    monkeypatch.setattr(repo, "data_clientes", data_clientes)
    return data_clientes


def test_context_document_lifecycle(isolated_client_storage: Path) -> None:
    row = store_document(
        "cliente_demo",
        filename="Estados financieros 2024.md",
        content=b"# Estados financieros\n\nActividad principal: servicios profesionales.",
        document_type="prior_financial_statements",
        period="2024",
        uploaded_by="auditor@example.com",
    )

    assert row["status"] == "available"
    assert row["document_type"] == "prior_financial_statements"
    assert row["period"] == "2024"
    assert row["ingestion"]["indexed"] is True

    documents = list_documents("cliente_demo")
    assert len(documents) == 1
    assert documents[0]["name"] == "Estados financieros 2024.md"

    derived = isolated_client_storage / "cliente_demo" / "documentos_text" / f"{row['id']}.md"
    assert derived.exists()
    derived_text = derived.read_text(encoding="utf-8")
    assert "document_type: prior_financial_statements" in derived_text
    assert "document_period: 2024" in derived_text

    assert delete_document("cliente_demo", row["id"]) is True
    assert list_documents("cliente_demo") == []
    assert not derived.exists()


@pytest.mark.parametrize(
    ("filename", "document_type", "period", "message"),
    [
        ("malware.exe", "other", "2024", "Formato no permitido"),
        ("informe.pdf", "unknown", "2024", "Tipo documental no soportado"),
        ("informe.pdf", "other", "24", "Periodo invalido"),
    ],
)
def test_context_document_validation(
    filename: str,
    document_type: str,
    period: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_upload(
            filename=filename,
            content=b"contenido",
            document_type=document_type,
            period=period,
        )


def test_context_document_rejects_empty_file() -> None:
    with pytest.raises(ValueError, match="vacio"):
        validate_upload(
            filename="informe.pdf",
            content=b"",
            document_type="prior_financial_statements",
            period="2024",
        )
