"""La guía de requerimientos por área (qué pedir y qué preguntar al cliente,
por aseveración) debe cargarse desde data/catalogos/requerimientos_por_area.yaml
y exponerse en el detalle de área que consume la página de Procedimientos.
"""
from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from backend.services.area_procedures_service import (
    get_procedures_by_area,
    load_requirements_yaml,
)


def test_requirements_load_for_efectivo() -> None:
    data = load_requirements_yaml(force_reload=True)
    assert "140" in data, "El catalogo debe incluir Efectivo (140)"
    aseveraciones = data["140"]["aseveraciones"]
    assert aseveraciones, "Efectivo debe tener aseveraciones con guia"
    existencia = next((a for a in aseveraciones if a["aseveracion"] == "existencia"), None)
    assert existencia is not None
    assert existencia["documentos"], "Debe listar documentos a solicitar"
    assert existencia["preguntas"], "Debe listar preguntas al cliente"


def test_area_detail_includes_requirements() -> None:
    detail = get_procedures_by_area("140")
    assert isinstance(detail.get("requerimientos"), list)
    assert detail["requerimientos"], "El detalle de Efectivo debe incluir requerimientos"
    first = detail["requerimientos"][0]
    assert {"aseveracion", "documentos", "preguntas", "procedimientos"} <= set(first.keys())


def test_area_without_requirements_returns_empty_list() -> None:
    detail = get_procedures_by_area("9999")
    assert detail["requerimientos"] == []
