from __future__ import annotations

from backend.services import rag_cache_service, rag_chat_service


def test_build_rag_cache_key_is_stable_for_temas_order() -> None:
    key_a = rag_cache_service.build_rag_cache_key(
        cliente_id="Cliente_X",
        query="Riesgo de efectivo",
        top_k=5,
        marco="NIIF_PYMES",
        etapa="ejecucion",
        afirmacion="existencia",
        tipo="NIA",
        temas=["control interno", "efectivo"],
        index_signature="idx:1",
    )
    key_b = rag_cache_service.build_rag_cache_key(
        cliente_id="cliente_x",
        query="riesgo de    efectivo",
        top_k=5,
        marco="niif_pymes",
        etapa="EJECUCION",
        afirmacion="Existencia",
        tipo="nia",
        temas=["efectivo", "control interno"],
        index_signature="idx:1",
    )
    assert key_a == key_b


def test_retrieve_context_chunks_uses_cache_and_invalidates(monkeypatch) -> None:
    monkeypatch.setenv("RAG_CACHE_ENABLED", "true")
    monkeypatch.setenv("RAG_CACHE_TTL_SECONDS", "3600")
    monkeypatch.delenv("RAG_CACHE_REDIS_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    rag_cache_service.reset_rag_cache_for_tests()

    calls = {"count": 0}

    def _fake_retrieve(*args, **kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        return [
            rag_chat_service.RetrievedChunk(
                source="data/conocimiento_normativo/nias/nia_315.md",
                excerpt="Texto de prueba para cache RAG.",
                score=8.5,
                metadata={"norma": "NIA 315", "marco": "ambos"},
            )
        ]

    monkeypatch.setattr(rag_chat_service, "_retrieve_chunks", _fake_retrieve)
    monkeypatch.setattr(rag_chat_service, "_rag_index_signature", lambda: "idx-v1")

    first = rag_chat_service.retrieve_context_chunks("cliente_cache", "riesgo de efectivo", top_k=4)
    second = rag_chat_service.retrieve_context_chunks("cliente_cache", "riesgo de efectivo", top_k=4)
    assert calls["count"] == 1
    assert first == second

    invalidated = rag_cache_service.invalidate_rag_cache_for_cliente("cliente_cache")
    assert invalidated >= 1

    third = rag_chat_service.retrieve_context_chunks("cliente_cache", "riesgo de efectivo", top_k=4)
    assert calls["count"] == 2
    assert third == first
