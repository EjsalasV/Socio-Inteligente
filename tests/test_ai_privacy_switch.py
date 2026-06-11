"""El interruptor AI_CLIENT_DATA_ENABLED=0 impide enviar datos del cliente
a proveedores externos de IA. No requiere red: corta antes de crear el cliente
HTTP del proveedor.
"""
from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from backend.services.intelligent_analyzer_service import analyze_financial_data


def test_kill_switch_blocks_remote_provider(monkeypatch) -> None:
    monkeypatch.setenv("AI_CLIENT_DATA_ENABLED", "0")
    monkeypatch.delenv("LM_STUDIO_BASE_URL", raising=False)

    out = analyze_financial_data(
        "cliente_demo",
        {"balance_trial": {"1101 Caja": 1000.0, "2101 Proveedores": -500.0}},
    )

    assert out["error"] == "AI_CLIENT_DATA_DISABLED"
    assert out["hallazgos"] == []
    assert "deshabilitado" in out["message"]


def test_switch_defaults_to_enabled(monkeypatch) -> None:
    """Sin la variable, el comportamiento actual no cambia: el flujo sigue
    hasta la verificacion de API key (aqui forzamos key ausente)."""
    monkeypatch.delenv("AI_CLIENT_DATA_ENABLED", raising=False)
    monkeypatch.delenv("LM_STUDIO_BASE_URL", raising=False)
    monkeypatch.setenv("AI_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    out = analyze_financial_data("cliente_demo", {"balance_trial": {}})

    assert out.get("error") != "AI_CLIENT_DATA_DISABLED"
