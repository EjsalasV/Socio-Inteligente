from __future__ import annotations


class RagBackendUnavailableError(RuntimeError):
    """Raised when the RAG backend (e.g., ChromaDB) is unavailable."""
