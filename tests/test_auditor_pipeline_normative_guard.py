from __future__ import annotations

import json
from typing import Any

from backend.auditor_pipeline import pipeline
from backend.auditor_pipeline.post_check import check_citations
from backend.auditor_pipeline.prompt_builder import format_rag_chunks
from backend.services.normative_quality_service import apply_quality_gate


def _metadata(*, verified: bool) -> dict[str, Any]:
    base: dict[str, Any] = {
        "norma": "NIA 500",
        "tipo": "NIA",
        "autoridad": "IAASB",
        "version": "NIA 500, Manual 2025",
        "jurisdiccion": "Internacional",
    }
    if verified:
        base.update(
            {
                "tipo_contenido": "oficial",
                "estado_revision": "verificado",
                "vigente_desde": "2009-12-15",
                "url_oficial": "https://www.iaasb.org/publications/example",
                "localizador": "parrafo 6",
                "licencia": "permiso_otorgado_para_ia para prueba",
                "aplicacion_local": "Aplicable en Ecuador para el encargo de prueba",
                "revisado_por": "Profesional de prueba",
                "rol_revisor": "Socio de auditoria",
                "fecha_revision": "2026-08-09",
                "alcance_revision": "Fuente completa",
                "evidencia_revision": "TEST-REVIEW-PIPELINE",
            }
        )
    return apply_quality_gate(base, "data/conocimiento_normativo/nias/nia_500.md")


def _chunk(name: str, *, verified: bool) -> dict[str, Any]:
    return {
        "source": name,
        "excerpt": "Resumen de evidencia de auditoria.",
        "score": 8.0,
        "metadata": _metadata(verified=verified),
    }


def _llm_json(analysis: str, citations: list[dict[str, str]]) -> str:
    return json.dumps(
        {
            "modo": "consulta_rapida",
            "riesgo_nivel": "medio",
            "afirmaciones_expuestas": ["existencia"],
            "analisis": analysis,
            "procedimientos": ["Contrastar facturas con cobros posteriores."],
            "citas_normativas": citations,
            "alerta_tributaria": None,
            "alertas_calidad": [],
            "confidence": "medio",
            "flags_internos": [],
        }
    )


def _run(monkeypatch, chunks: list[dict[str, Any]], raw_text: str) -> dict[str, Any]:
    monkeypatch.setattr(pipeline, "load_context", lambda *_args: ({}, {"riesgo": "medio"}))
    monkeypatch.setattr(pipeline, "format_client_context", lambda *_args: "Contexto de prueba")
    monkeypatch.setattr(pipeline, "call_llm", lambda **_kwargs: (raw_text, {"provider": "test", "model": "test"}))
    return pipeline.execute_pipeline(
        cliente_id="cliente_prueba",
        codigo_area="140",
        modo="consulta_rapida",
        chunks_rag=chunks,
    )


def test_prompt_distinguishes_verified_sources_from_orientation() -> None:
    block = format_rag_chunks([_chunk("verified.md", verified=True), _chunk("pending.md", verified=False)])

    assert "[FUENTE 1]" in block
    assert "[ORIENTACION 2]" in block


def test_structured_citation_rejects_pending_source() -> None:
    chunks = [_chunk("pending.md", verified=False)]
    response = {
        "citas_normativas": [
            {"source_id": "FUENTE 1", "referencia": "NIA 500", "respaldo": "con_chunk", "texto_parafraseado": "Texto"}
        ]
    }

    assert any(flag.startswith("CITA_NO_VERIFICADA") for flag in check_citations(response, chunks))


def test_pipeline_blocks_pending_source_and_hides_raw_output(monkeypatch) -> None:
    chunks = [_chunk("pending.md", verified=False)]
    raw = _llm_json(
        "La NIA 500 exige evaluar la suficiencia [FUENTE 1].",
        [{"source_id": "FUENTE 1", "referencia": "NIA 500", "respaldo": "con_chunk", "texto_parafraseado": "Texto"}],
    )

    result = _run(monkeypatch, chunks, raw)

    assert result["mode_used"] == "consulta_rapida_output_blocked"
    assert result["citations"] == []
    assert result["pipeline"]["raw"] == ""


def test_pipeline_exposes_only_verified_source_used_in_answer(monkeypatch) -> None:
    chunks = [_chunk("unused.md", verified=True), _chunk("used.md", verified=True)]
    raw = _llm_json(
        "La NIA 500 exige evaluar la suficiencia [FUENTE 2].",
        [{"source_id": "FUENTE 2", "referencia": "NIA 500", "respaldo": "con_chunk", "texto_parafraseado": "Texto"}],
    )

    result = _run(monkeypatch, chunks, raw)

    assert result["mode_used"] == "consulta_rapida_pipeline"
    assert [citation["source"] for citation in result["citations"]] == ["used.md"]
