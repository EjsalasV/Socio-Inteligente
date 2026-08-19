from types import SimpleNamespace

from backend.services import rag_chat_service
from backend.services.rag_chat_service import RetrievedChunk, _diversify_chunks, _is_data_inventory_question


def test_explicit_client_inventory_question_is_detected() -> None:
    assert _is_data_inventory_question("Que informacion tienes de este cliente?") is True
    assert _is_data_inventory_question("Que datos tienes cargados?") is True


def test_request_for_audit_evidence_is_not_misrouted_to_inventory() -> None:
    query = (
        "Estoy revisando ingresos y cuentas por cobrar. Explicame que informacion debo pedir "
        "y como documentar el razonamiento."
    )

    assert _is_data_inventory_question(query) is False


def test_pilot_guidance_fallback_stays_in_requested_area(monkeypatch) -> None:
    monkeypatch.setattr(
        rag_chat_service,
        "read_perfil",
        lambda _client_id: {
            "cliente": {"nombre_legal": "Cliente Prueba", "sector": "Servicios"},
            "encargo": {"marco_referencial": "NIIF PYMES", "fecha_inicio_periodo": "2025-01-01"},
        },
    )

    result = rag_chat_service._pilot_area_guidance_answer(
        "cliente_prueba",
        "Que riesgos y aseveraciones debo considerar en ingresos y cuentas por cobrar?",
    )

    assert result["mode_used"] == "pilot_area_guidance"
    assert "Riesgos candidatos" in result["answer"]
    assert "Cuentas por cobrar" in result["answer"]
    assert "Cuentas a pagar" not in result["answer"]
    assert result["citations"] == []


def test_chunk_diversity_prefers_distinct_documents() -> None:
    chunks = [
        RetrievedChunk("nia_315.md", "uno", 9.0, {}),
        RetrievedChunk("nia_315.md", "dos", 8.0, {}),
        RetrievedChunk("nia_240.md", "tres", 7.0, {}),
        RetrievedChunk("seccion_23.md", "cuatro", 6.0, {}),
    ]

    selected = _diversify_chunks(chunks, 3)

    assert [chunk.source for chunk in selected] == ["nia_315.md", "nia_240.md", "seccion_23.md"]


def test_prior_period_marker_is_repeated_on_every_client_chunk() -> None:
    chunks = rag_chat_service._split_chunks(
        "prior.md",
        ("Hallazgo anterior con detalle suficiente para el primer fragmento.\n\n"
         "Importe anterior con detalle suficiente para el segundo fragmento."),
        {
            "tipo": "CLIENTE",
            "document_period": "2024",
            "temporal_status": "antecedente_periodo_anterior",
        },
    )

    assert len(chunks) == 2
    assert all("ANTECEDENTE_PERIODO_ANTERIOR" in excerpt for _, excerpt, _ in chunks)


def test_combined_pilot_query_covers_income_and_receivables_sources(monkeypatch) -> None:
    monkeypatch.setattr(
        rag_chat_service,
        "read_perfil",
        lambda _client_id: {"encargo": {"marco_referencial": "NIIF PYMES"}},
    )
    candidates = [
        RetrievedChunk("data/conocimiento_normativo/nias/nia_240.md", "fraude", 4.0, {}),
        RetrievedChunk("data/conocimiento_normativo/nias/nia_315.md", "riesgos", 5.0, {}),
        RetrievedChunk("data/conocimiento_normativo/niif_pymes/seccion_23.md", "ingresos", 6.0, {}),
        RetrievedChunk("data/conocimiento_normativo/niif_pymes/seccion_11.md", "cartera", 7.0, {}),
    ]

    selected = rag_chat_service._select_pilot_coverage(
        candidates,
        cliente_id="cliente_prueba",
        query="Riesgos de fraude en ingresos y cuentas por cobrar",
        limit=4,
    )

    assert [chunk.source.rsplit("/", 1)[-1] for chunk in selected] == [
        "nia_240.md",
        "nia_315.md",
        "seccion_23.md",
        "seccion_11.md",
    ]


def test_risk_question_in_mentor_chat_uses_conversational_prompt(monkeypatch) -> None:
    captured: dict[str, str] = {}

    monkeypatch.setattr(rag_chat_service, "_retrieve_chunks", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(rag_chat_service, "_has_llm_credentials", lambda: True)
    monkeypatch.setattr(rag_chat_service, "_web_fallback_enabled", lambda: False)
    monkeypatch.setattr(
        rag_chat_service,
        "evaluate_normative_request",
        lambda *_args, **_kwargs: SimpleNamespace(blocked=False),
    )

    def fake_llm(_query, _chunks, *, mode, **_kwargs):
        captured["mode"] = mode
        return {"answer": "respuesta", "mode_used": mode}

    monkeypatch.setattr(rag_chat_service, "_llm_answer", fake_llm)

    result = rag_chat_service.generate_chat_response(
        "cliente_ruta_chat",
        "Que riesgos debo analizar en ingresos y cuentas por cobrar?",
        conversation_id="prueba_ruta_riesgo_chat",
    )

    assert captured["mode"] == "chat"
    assert result["mode_used"] == "chat"
