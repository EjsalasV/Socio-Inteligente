from backend.validation import (
    normalize_workflow_doc_v1,
    validate_area_doc_v1,
    validate_perfil_doc_v1,
    validate_workflow_doc_v1,
)


def test_validate_perfil_v1_requires_core_fields() -> None:
    ok, errors = validate_perfil_doc_v1({"cliente": {"nombre_legal": ""}})
    assert ok is False
    assert any("cliente.nombre_legal" in err for err in errors)
    assert any("cliente.sector" in err for err in errors)


def test_validate_area_v1_requires_identity() -> None:
    ok, errors = validate_area_doc_v1({"nombre": ""}, area_code="")
    assert ok is False
    assert any("codigo" in err for err in errors)


def test_validate_workflow_v1_normalizes_phase() -> None:
    doc = normalize_workflow_doc_v1({"phase": "Ejecucion"}, cliente_id="cli_1", phase="planificacion")
    assert doc["phase"] == "ejecucion"
    ok, errors = validate_workflow_doc_v1(doc, cliente_id="cli_1", phase="ejecucion")
    assert ok is True
    assert errors == []
