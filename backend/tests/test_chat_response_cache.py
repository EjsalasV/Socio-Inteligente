"""Tests para chat_response_cache_service (FASE 5)."""

from __future__ import annotations

from backend.services.chat_response_cache_service import (
    build_response_cache_key,
    get_cached_response,
    set_cached_response,
    invalidate_chat_cache_for_cliente,
    reset_chat_response_cache_for_tests,
)


class TestChatResponseCache:
    def setup_method(self):
        """Reset caché antes de cada test."""
        reset_chat_response_cache_for_tests()

    def test_cache_key_generation(self):
        """Test que la clave se genera consistentemente."""
        key1 = build_response_cache_key("client-1", "¿Cuál es el riesgo?", mode="chat")
        key2 = build_response_cache_key("client-1", "¿Cuál es el riesgo?", mode="chat")

        assert key1 == key2
        assert "client-1" in key1
        assert "chat" in key1

    def test_cache_set_and_get(self):
        """Test que se puede guardar y recuperar del caché."""
        key = build_response_cache_key("client-1", "test query", mode="chat")
        response = {"answer": "Respuesta de prueba", "sources": []}

        set_cached_response(key, response)
        cached = get_cached_response(key)

        assert cached is not None
        assert cached["answer"] == "Respuesta de prueba"

    def test_cache_miss(self):
        """Test que retorna None si no existe."""
        key = build_response_cache_key("client-1", "query inexistente", mode="chat")
        cached = get_cached_response(key)

        assert cached is None
