from backend.services import quality_trace_service
from backend.repositories.file_repository import FileRepository


def test_quality_summary_reports_safe_adjustments() -> None:
    summary = quality_trace_service.summarize_quality_controls(
        {
            "mode_used": "chat",
            "quality_repair_used": True,
            "normative_repair_used": True,
            "normative_redaction_used": True,
            "grounding_redaction_used": False,
        }
    )

    assert summary["publication"] == "published"
    assert summary["normative"] == "redacted"
    assert summary["grounding"] == "passed"


def test_quality_trace_stores_hashes_without_full_query_or_answer(monkeypatch) -> None:
    stored: list[dict] = []
    monkeypatch.setattr(
        quality_trace_service,
        "append_quality_trace",
        lambda _cliente_id, event: stored.append(event),
    )

    event = quality_trace_service.record_quality_trace(
        cliente_id="cliente_prueba",
        conversation_id="conv-1",
        query="Consulta privada del auditor",
        result={
            "answer": "Respuesta privada del sistema",
            "mode_used": "chat",
            "provider": "test",
            "model": "test-model",
            "context_sources": ["perfil.yaml"],
        },
        user_id="auditor-1",
    )

    assert stored == [event]
    assert len(event["query_sha256"]) == 64
    assert len(event["response_sha256"]) == 64
    assert "Consulta privada" not in str(event)
    assert "Respuesta privada" not in str(event)


def test_quality_trace_repository_persists_event(tmp_path) -> None:
    repository = FileRepository(root=tmp_path)
    event = {"trace_id": "trace-1", "controls": {"publication": "published"}}

    repository.append_quality_trace("cliente_prueba", event)

    assert repository.read_quality_trace("cliente_prueba") == [event]


def test_pilot_feedback_repository_persists_separately(tmp_path) -> None:
    repository = FileRepository(root=tmp_path)
    event = {"feedback_id": "feedback-1", "outcome": "helpful"}

    repository.append_pilot_feedback("cliente_prueba", event)

    assert repository.read_pilot_feedback("cliente_prueba") == [event]
    assert repository.read_quality_trace("cliente_prueba") == []
