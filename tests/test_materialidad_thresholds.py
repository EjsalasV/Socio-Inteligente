from __future__ import annotations

from unittest.mock import patch

from domain.services.materialidad_service import calcular_materialidad


def test_minimum_threshold_precedencia_cliente_sector_global():
    with (
        patch(
            "domain.services.materialidad_service.obtener_regla_materialidad",
            return_value={
                "base": "activos",
                "porcentaje_min": 0.01,
                "porcentaje_max": 0.02,
                "minimum_threshold": 80000,
                "origen": "sector:servicios",
            },
        ),
        patch(
            "domain.services.materialidad_service.leer_perfil",
            return_value={"materialidad": {"minimum_threshold": 200000}},
        ),
        patch(
            "domain.services.materialidad_service.obtener_resumen_tb",
            return_value={"ACTIVO": 1_000_000, "INGRESOS": 200_000, "PATRIMONIO": 100_000, "PASIVO": 50_000},
        ),
        patch(
            "domain.services.materialidad_service.obtener_materialidad_config",
            return_value={"minimum_threshold": 100000},
        ),
    ):
        out = calcular_materialidad("cliente_x")

    assert out is not None
    assert out["materialidad_sugerida"] == 200000
    assert out["minimum_threshold_origen"] == "cliente"


def test_materialidad_maneja_patrimonio_negativo():
    with (
        patch(
            "domain.services.materialidad_service.obtener_regla_materialidad",
            return_value={"base": "patrimonio", "porcentaje_min": 0.02, "porcentaje_max": 0.05, "origen": "sector:x"},
        ),
        patch("domain.services.materialidad_service.leer_perfil", return_value={}),
        patch(
            "domain.services.materialidad_service.obtener_resumen_tb",
            return_value={"PATRIMONIO": -500_000, "ACTIVO": 900_000, "INGRESOS": 100_000, "PASIVO": 400_000},
        ),
        patch(
            "domain.services.materialidad_service.obtener_materialidad_config",
            return_value={"minimum_threshold": 1000},
        ),
    ):
        out = calcular_materialidad("cliente_x")

    assert out is not None
    assert out["base_utilizada"] == "patrimonio"
    assert out["valor_base"] == 500000.0


def test_materialidad_hace_fallback_si_ingresos_en_perdida():
    with (
        patch(
            "domain.services.materialidad_service.obtener_regla_materialidad",
            return_value={"base": "ingresos", "porcentaje_min": 0.05, "porcentaje_max": 0.1, "origen": "sector:x"},
        ),
        patch("domain.services.materialidad_service.leer_perfil", return_value={}),
        patch(
            "domain.services.materialidad_service.obtener_resumen_tb",
            return_value={"INGRESOS": -80_000, "ACTIVO": 600_000, "PATRIMONIO": -10_000, "PASIVO": 100_000},
        ),
        patch(
            "domain.services.materialidad_service.obtener_materialidad_config",
            return_value={"minimum_threshold": 1000},
        ),
    ):
        out = calcular_materialidad("cliente_x")

    assert out is not None
    assert out["base_utilizada"] == "ingresos"
    assert out["valor_base"] == 80000.0
