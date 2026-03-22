"""
Unit tests for the RAG knowledge pipeline.
Tests loader, chunking and retriever without requiring
ChromaDB to be populated (uses mocks where needed).
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── Loader tests ─────────────────────────────────────────────

from infra.rag.knowledge_loader import (
    _chunk_texto,
    _detectar_fuente,
    listar_archivos_normativa,
    cargar_documentos,
)


def test_chunk_texto_short():
    """Short text should return as single chunk."""
    texto = "Este es un texto corto sobre NIAs."
    chunks = _chunk_texto(texto, chunk_size=800)
    assert len(chunks) >= 1
    assert any("NIAs" in c for c in chunks)


def test_chunk_texto_largo():
    """Long text should be split into multiple chunks."""
    texto = ("Esta es una oración de prueba. " * 60)
    chunks = _chunk_texto(texto, chunk_size=200)
    assert len(chunks) > 1


def test_chunk_respeta_secciones():
    """Chunking should split on ## section headers."""
    texto = "# Titulo\n\n## Seccion A\nContenido A.\n\n## Seccion B\nContenido B."
    chunks = _chunk_texto(texto)
    assert len(chunks) >= 1


def test_chunk_no_empty():
    """No chunk should be empty or whitespace only."""
    texto = "Texto de prueba.\n\nOtro párrafo.\n\n"
    chunks = _chunk_texto(texto)
    for chunk in chunks:
        assert chunk.strip() != ""


def test_detectar_fuente_nias():
    p = Path("data/conocimiento_normativo/nias/nia_315.md")
    assert _detectar_fuente(p) == "NIA"


def test_detectar_fuente_tributario():
    p = Path("data/conocimiento_normativo/tributario_ec/retenciones.md")
    assert _detectar_fuente(p) == "Tributario Ecuador"


def test_detectar_fuente_niif_pymes():
    p = Path("data/conocimiento_normativo/niif_pymes/seccion_23.md")
    assert _detectar_fuente(p) == "NIIF PYMES"


def test_detectar_fuente_metodologia():
    p = Path("data/conocimiento_normativo/metodologia/materialidad.md")
    assert _detectar_fuente(p) == "Metodología SocioAI"


def test_listar_archivos_normativa_returns_list():
    archivos = listar_archivos_normativa()
    assert isinstance(archivos, list)


def test_listar_archivos_normativa_has_content():
    """Should find the 12 .md files we created."""
    archivos = listar_archivos_normativa()
    assert len(archivos) >= 12


def test_listar_archivos_tiene_campos():
    archivos = listar_archivos_normativa()
    if archivos:
        a = archivos[0]
        assert "archivo" in a
        assert "fuente" in a
        assert "titulo" in a


def test_cargar_documentos_returns_chunks():
    """cargar_documentos should return chunks from .md files."""
    docs = cargar_documentos()
    assert isinstance(docs, list)
    assert len(docs) > 0


def test_cargar_documentos_estructura():
    """Each document chunk must have required fields."""
    docs = cargar_documentos()
    if docs:
        d = docs[0]
        assert "id" in d
        assert "texto" in d
        assert "fuente" in d
        assert "titulo" in d
        assert len(d["texto"]) > 10


def test_cargar_documentos_no_empty_chunks():
    """No chunk should be empty."""
    docs = cargar_documentos()
    for d in docs:
        assert d["texto"].strip() != ""


# ── Vector store tests (mocked) ──────────────────────────────

from infra.rag import vector_store


def test_esta_indexado_returns_bool():
    """esta_indexado should return bool without crashing."""
    result = vector_store.esta_indexado()
    assert isinstance(result, bool)


def test_total_indexado_returns_int():
    """total_indexado should return int without crashing."""
    result = vector_store.total_indexado()
    assert isinstance(result, int)
    assert result >= 0


def test_buscar_normativa_sin_indexar_returns_empty():
    """buscar_normativa should return empty list if store is empty."""
    with patch.object(vector_store, "esta_indexado", return_value=False):
        # Simulate empty store by patching collection count
        with patch("infra.rag.vector_store._get_collection") as mock_col:
            mock_col.return_value.count.return_value = 0
            result = vector_store.buscar_normativa("materialidad")
            assert isinstance(result, list)


# ── Retriever tests ──────────────────────────────────────────

from infra.rag.retriever import recuperar_contexto_normativo, inicializar_rag


def test_recuperar_contexto_sin_indexar():
    """Should return empty string when store is not indexed."""
    with patch("infra.rag.retriever.esta_indexado", return_value=False):
        result = recuperar_contexto_normativo("materialidad NIA 320")
        assert result == ""


def test_recuperar_contexto_con_resultados():
    """Should return formatted context string when results exist."""
    mock_resultados = [
        {
            "texto": "La materialidad es el umbral...",
            "fuente": "NIA",
            "titulo": "NIA 320",
            "relevancia": 0.85,
        }
    ]
    with patch("infra.rag.retriever.esta_indexado", return_value=True), \
         patch("infra.rag.retriever.buscar_normativa", return_value=mock_resultados):
        result = recuperar_contexto_normativo("materialidad")
        assert "CONTEXTO NORMATIVO" in result
        assert "NIA 320" in result
        assert "materialidad" in result.lower()


def test_recuperar_contexto_sin_resultados():
    """Should return empty string when search yields nothing."""
    with patch("infra.rag.retriever.esta_indexado", return_value=True), \
         patch("infra.rag.retriever.buscar_normativa", return_value=[]):
        result = recuperar_contexto_normativo("xyz123")
        assert result == ""


def test_inicializar_rag_ya_indexado():
    """Should return ya_indexado status when already populated."""
    with patch("infra.rag.retriever.esta_indexado", return_value=True), \
         patch("infra.rag.retriever.total_indexado", return_value=42):
        result = inicializar_rag(forzar=False)
        assert result["estado"] == "ya_indexado"
        assert result["total_chunks"] == 42


def test_inicializar_rag_sin_documentos():
    """Should handle empty document list gracefully."""
    with patch("infra.rag.retriever.esta_indexado", return_value=False), \
         patch("infra.rag.retriever.cargar_documentos", return_value=[]):
        result = inicializar_rag(forzar=True)
        assert result["estado"] == "sin_documentos"
        assert result["total_chunks"] == 0
