"""
Unit tests covering the 5 bug fixes applied to SocioAI.
"""
import pytest


# ── FIX 3: _afirmaciones_por_area order (425 before 42) ──────────────────────

from domain.models.hallazgo import _afirmaciones_por_area

def test_afirmaciones_425_matched_before_42():
    """Area 425.2 must match the '425' branch, not the generic '42' branch."""
    result = _afirmaciones_por_area("425")
    assert result == ["Integridad", "Corte", "Presentacion"]

def test_afirmaciones_425_dot_2():
    result = _afirmaciones_por_area("425.2")
    assert result == ["Integridad", "Corte", "Presentacion"]

def test_afirmaciones_420_matches_42_branch():
    """Area 420 must still match the '42' branch."""
    result = _afirmaciones_por_area("420")
    assert result == ["Integridad", "Corte", "Presentacion"]

def test_afirmaciones_130():
    result = _afirmaciones_por_area("130")
    assert result == ["Valuacion", "Existencia", "Presentacion"]

def test_afirmaciones_default():
    result = _afirmaciones_por_area("999")
    assert result == ["Existencia", "Integridad", "Presentacion"]


# ── FIX 1 + FIX 2: resumen_materialidad and sugerir_materialidad ─────────────

from unittest.mock import patch, MagicMock
from domain.services import materialidad_service


MOCK_PERFIL = {
    "cliente": {
        "nombre_legal": "Test Corp S.A.",
        "sector": "comerciales",
        "tipo_entidad": "SOCIEDAD_ANONIMA",
    }
}

MOCK_CALCULO = {
    "materialidad_sugerida": 100000.0,
    "materialidad_minima": 75000.0,
    "materialidad_maxima": 125000.0,
    "materialidad_desempeno": 75000.0,
    "error_trivial": 5000.0,
    "porcentaje_maximo": 5,
    "base_utilizada": "activos",
}

MOCK_SUGERENCIA = {
    "cliente": "test_client",
    "nombre_cliente": "Test Corp S.A.",
    "sector": "comerciales",
    "calculo": MOCK_CALCULO,
    "recomendacion": "Usar $100,000",
    "proximos_pasos": [],
}


def test_resumen_materialidad_no_name_error():
    """
    FIX 1: resumen_materialidad must not raise NameError (calc vs calculo).
    FIX 2: accesses perfil via nested keys.
    """
    with patch.object(materialidad_service, "sugerir_materialidad", return_value=MOCK_SUGERENCIA), \
         patch.object(materialidad_service, "obtener_materialidad_guardada", return_value=None):
        result = materialidad_service.resumen_materialidad("test_client")

    assert result is not None
    assert result["materialidad_desempeno"] == 75000.0
    assert result["estado"] == "PENDIENTE"


def test_resumen_materialidad_with_saved():
    """When guardada exists, estado must be ESTABLECIDA."""
    guardada = {"materialidad_elegida": 110000.0}
    with patch.object(materialidad_service, "sugerir_materialidad", return_value=MOCK_SUGERENCIA), \
         patch.object(materialidad_service, "obtener_materialidad_guardada", return_value=guardada):
        result = materialidad_service.resumen_materialidad("test_client")

    assert result["materialidad_elegida"] == 110000.0
    assert result["estado"] == "ESTABLECIDA"


def test_sugerir_materialidad_uses_nested_perfil():
    """
    FIX 2: sugerir_materialidad must read perfil.cliente.nombre_legal,
    not perfil.nombre (flat access that returned None before the fix).
    """
    mock_calculo = {**MOCK_CALCULO}
    with patch.object(materialidad_service, "calcular_materialidad", return_value=mock_calculo), \
         patch.object(materialidad_service, "leer_perfil", return_value=MOCK_PERFIL):
        result = materialidad_service.sugerir_materialidad("test_client")

    assert result is not None
    assert result["nombre_cliente"] == "Test Corp S.A."
    assert "None" not in result["recomendacion"]


# ── FIX 4: no unused import inside obtener_materialidad_guardada ──────────────

import ast, pathlib

def test_no_unused_import_in_obtener_materialidad_guardada():
    """
    FIX 4: the line 'from infra.repositories.cliente_repository import
    cargar_perfil as repo_cargar' must not exist inside the function body.
    """
    source = pathlib.Path(
        "domain/services/materialidad_service.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "obtener_materialidad_guardada":
                for child in ast.walk(node):
                    if isinstance(child, (ast.Import, ast.ImportFrom)):
                        for alias in getattr(child, "names", []):
                            assert alias.asname != "repo_cargar", (
                                "Unused import 'repo_cargar' still present "
                                "inside obtener_materialidad_guardada()"
                            )
