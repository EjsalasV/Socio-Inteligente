"""
Vector store ChromaDB para la base de conocimiento normativo.
Gestiona la indexación y búsqueda semántica de documentos.
"""
from __future__ import annotations

import os
import tempfile
from typing import Any

_MODELO_CACHE: Any = None
_MODELO_NOMBRE = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _get_modelo():
    """Returns cached SentenceTransformer instance."""
    global _MODELO_CACHE
    if _MODELO_CACHE is None:
        try:
            from sentence_transformers import SentenceTransformer

            print("[RAG] Cargando modelo de embeddings...")
            _MODELO_CACHE = SentenceTransformer(_MODELO_NOMBRE)
            print("[RAG] Modelo cargado y cacheado.")
        except ImportError:
            raise ImportError(
                "sentence-transformers no instalado. "
                "Ejecuta: pip install sentence-transformers"
            )
    return _MODELO_CACHE


def _get_chroma_path() -> str:
    """
    Returns writable path for ChromaDB.
    Uses /tmp on Streamlit Cloud (read-only filesystem),
    uses ./chroma locally.
    """
    # Check if running on Streamlit Cloud
    env = os.environ.get("SOCIOAI_ENV", "development")
    if env == "production":
        return os.path.join(tempfile.gettempdir(), "socioai_chroma")

    # Local development
    chroma_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "chroma"
    )
    os.makedirs(chroma_dir, exist_ok=True)
    return chroma_dir


def _get_client():
    import chromadb

    return chromadb.PersistentClient(path=_get_chroma_path())


def _get_collection(client=None):
    if client is None:
        client = _get_client()
    return client.get_or_create_collection(
        name="socioai_normativa",
        metadata={"hnsw:space": "cosine"},
    )


def indexar_documentos(documentos: list[dict[str, Any]]) -> int:
    """
    Indexa documentos en ChromaDB usando embeddings.

    Returns:
        Número de documentos indexados.
    """
    if not documentos:
        return 0

    try:
        modelo = _get_modelo()

        textos = [d["texto"] for d in documentos]
        ids = [d["id"] for d in documentos]
        metadatas = [
            {
                "fuente": d.get("fuente", ""),
                "titulo": d.get("titulo", ""),
                "archivo": d.get("archivo", ""),
                "chunk_idx": str(d.get("chunk_idx", 0)),
            }
            for d in documentos
        ]

        print(f"[RAG] Generando embeddings para {len(textos)} chunks...")
        embeddings = modelo.encode(textos, show_progress_bar=True).tolist()

        coleccion = _get_collection()

        batch_size = 50
        for i in range(0, len(textos), batch_size):
            coleccion.upsert(
                ids=ids[i : i + batch_size],
                documents=textos[i : i + batch_size],
                embeddings=embeddings[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

        total = coleccion.count()
        print(f"[RAG] Indexacion completa. Total en vector store: {total}")
        return total

    except Exception as e:
        print(f"[RAG] Error indexando: {e}")
        return 0


def buscar_normativa(
    consulta: str,
    n_resultados: int = 4,
    fuente_filtro: str | None = None,
) -> list[dict[str, Any]]:
    """
    Busca en la base normativa usando similaridad semántica.

    Args:
        consulta: Texto de la pregunta o consulta.
        n_resultados: Número de chunks a recuperar.
        fuente_filtro: Filtrar por fuente (ej: 'NIA', 'Tributario Ecuador').

    Returns:
        Lista de chunks relevantes con metadata.
    """
    try:
        coleccion = _get_collection()
        if coleccion.count() == 0:
            return []

        modelo = _get_modelo()
        embedding_consulta = modelo.encode([consulta]).tolist()

        where = {"fuente": fuente_filtro} if fuente_filtro else None

        kwargs: dict[str, Any] = {
            "query_embeddings": embedding_consulta,
            "n_results": min(n_resultados, coleccion.count()),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        resultados = coleccion.query(**kwargs)

        salida: list[dict[str, Any]] = []
        docs = resultados.get("documents", [[]])[0]
        metas = resultados.get("metadatas", [[]])[0]
        dists = resultados.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, dists):
            relevancia = round(1 - float(dist), 4)
            if relevancia >= 0.2:
                salida.append(
                    {
                        "texto": doc,
                        "fuente": meta.get("fuente", ""),
                        "titulo": meta.get("titulo", ""),
                        "relevancia": relevancia,
                    }
                )

        return salida

    except Exception as e:
        print(f"[RAG] Error buscando: {e}")
        return []


def esta_indexado() -> bool:
    """Verifica si ya existe contenido en el vector store."""
    try:
        coleccion = _get_collection()
        return coleccion.count() > 0
    except Exception:
        return False


def total_indexado() -> int:
    """Retorna el número de chunks indexados."""
    try:
        return _get_collection().count()
    except Exception:
        return 0
