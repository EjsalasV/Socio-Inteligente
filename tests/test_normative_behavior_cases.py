from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from backend.services import rag_chat_service
from backend.services.normative_quality_service import (
    apply_quality_gate,
    evaluate_normative_request,
    validate_normative_output,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "conocimiento_normativo" / "manifest_piloto_ingresos_cxc.yaml"
CASES = ROOT / "data" / "conocimiento_normativo" / "casos_prueba_piloto.yaml"


def _frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8").lstrip("\ufeff")
    parts = text.split("---", 2)
    return yaml.safe_load(parts[1]) or {}


def _source_metadata() -> dict[str, dict[str, Any]]:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}
    result: dict[str, dict[str, Any]] = {}
    for source in manifest.get("sources", []):
        source_id = str(source.get("id") or "")
        relative_path = str(source.get("path") or "")
        metadata = _frontmatter(ROOT / relative_path)
        result[source_id] = apply_quality_gate(metadata, relative_path)
    return result


def test_all_pilot_cases_follow_the_declared_runtime_policy() -> None:
    metadata_by_source = _source_metadata()
    suite = yaml.safe_load(CASES.read_text(encoding="utf-8")) or {}

    for case in suite.get("cases", []):
        case_id = str(case.get("id") or "")
        expected = case.get("expected_behavior") or {}
        source_id = str(case.get("source") or "")
        assert source_id in metadata_by_source, f"{case_id}: fuente ausente del manifiesto"

        metadata = metadata_by_source[source_id]
        decision = evaluate_normative_request(str(case.get("question") or ""), [metadata])
        if expected.get("answer_allowed") is False:
            assert decision.blocked, f"{case_id}: debia activar un bloqueo, obtuvo {decision.action}"
        else:
            assert not decision.blocked, f"{case_id}: debia permitir orientacion, obtuvo {decision.action}"
        if expected.get("normative_citation_allowed") is False:
            assert metadata["citation_eligible"] is False, f"{case_id}: habilito una cita pendiente"


def test_chat_blocks_unverified_exact_citation_before_calling_llm(monkeypatch) -> None:
    pending = apply_quality_gate(
        {
            "norma": "NIA 500",
            "tipo": "NIA",
            "autoridad": "IAASB",
            "version": "Manual 2025",
            "jurisdiccion": "Internacional",
        },
        "data/conocimiento_normativo/nias/nia_500.md",
    )
    chunks = [rag_chat_service.RetrievedChunk("nia_500.md", "Resumen interno", 8.0, pending)]
    monkeypatch.setattr(rag_chat_service, "get_cached_response", lambda _key: None)
    monkeypatch.setattr(rag_chat_service, "set_cached_response", lambda _key, _value: None)
    monkeypatch.setattr(rag_chat_service, "_retrieve_chunks", lambda *_args, **_kwargs: chunks)
    monkeypatch.setattr(
        rag_chat_service,
        "_has_llm_credentials",
        lambda: (_ for _ in ()).throw(AssertionError("El guard debio responder antes del LLM")),
    )

    result = rag_chat_service.generate_chat_response(
        "cliente_prueba",
        "Cita el parrafo exacto que define suficiencia y adecuacion.",
    )

    assert result["mode_used"] == "block_unverified_citation"
    assert result["citations"] == []
    assert "bloqueada" in result["answer"].lower()


def _verified_metadata() -> dict[str, Any]:
    return apply_quality_gate(
        {
            "norma": "NIA 500",
            "tipo": "NIA",
            "tipo_contenido": "oficial",
            "estado_revision": "verificado",
            "autoridad": "IAASB",
            "version": "NIA 500, Manual 2025",
            "jurisdiccion": "Internacional",
            "vigente_desde": "2009-12-15",
            "url_oficial": "https://www.iaasb.org/publications/example",
            "localizador": "parrafo 6",
            "licencia": "permiso_otorgado_para_ia para prueba",
            "aplicacion_local": "Aplicable en Ecuador para el encargo de prueba",
            "revisado_por": "Profesional de prueba",
            "rol_revisor": "Socio de auditoria",
            "fecha_revision": "2026-08-09",
            "alcance_revision": "Fuente completa",
            "evidencia_revision": "TEST-REVIEW-OUTPUT",
        },
        "data/conocimiento_normativo/nias/nia_500.md",
    )


def _pending_metadata() -> dict[str, Any]:
    return apply_quality_gate(
        {
            "norma": "NIA 500",
            "tipo": "NIA",
            "autoridad": "IAASB",
            "version": "NIA 500, Manual 2025",
            "jurisdiccion": "Internacional",
        },
        "data/conocimiento_normativo/nias/nia_500.md",
    )


def test_output_blocks_normative_attribution_without_source_marker() -> None:
    result = validate_normative_output(
        "La NIA 500 exige evaluar la suficiencia de la evidencia.",
        [_verified_metadata()],
    )

    assert result.allowed is False
    assert "atribucion_sin_fuente:1" in result.issues


def test_output_blocks_pending_source_presented_as_verified() -> None:
    result = validate_normative_output(
        "La NIA 500 exige evaluar la suficiencia de la evidencia [FUENTE 1].",
        [_pending_metadata()],
    )

    assert result.allowed is False
    assert "fuente_no_verificada:1" in result.issues


def test_output_blocks_nonexistent_source_index() -> None:
    result = validate_normative_output(
        "La NIA 500 exige evaluar la suficiencia de la evidencia [FUENTE 9].",
        [_verified_metadata()],
    )

    assert result.allowed is False
    assert "fuente_inexistente:9" in result.issues


def test_output_allows_verified_attribution_with_immediate_marker() -> None:
    result = validate_normative_output(
        "La NIA 500 exige evaluar la suficiencia de la evidencia [FUENTE 1].",
        [_verified_metadata()],
    )

    assert result.allowed is True
    assert result.issues == ()


def test_output_allows_general_orientation_without_normative_attribution() -> None:
    result = validate_normative_output(
        "Conviene contrastar las facturas con cobros posteriores y documentar cualquier diferencia.",
        [_pending_metadata()],
    )

    assert result.allowed is True


def test_output_allows_explicit_limit_statement() -> None:
    result = validate_normative_output(
        "No puedo confirmar que la NIA 500 exige ese procedimiento sin validar la fuente oficial.",
        [_pending_metadata()],
    )

    assert result.allowed is True
