from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from analysis.ranking_areas import calcular_ranking_areas


def test_ranking_no_divide_por_cero_si_total_balance_es_cero():
    tb = pd.DataFrame(
        {
            "ls": ["130", "200"],
            "codigo": ["130.1", "200.1"],
            "saldo_actual": [0.0, 0.0],
            "nombre": ["CxC", "Patrimonio"],
        }
    )
    with (
        patch("analysis.ranking_areas.leer_tb", return_value=tb),
        patch("analysis.ranking_areas.calcular_variaciones", return_value=pd.DataFrame()),
        patch("analysis.ranking_areas.leer_perfil", return_value={}),
        patch(
            "analysis.ranking_areas.calcular_materialidad",
            return_value={"materialidad_sugerida": 100000, "materialidad_desempeno": 50000, "error_trivial": 5000},
        ),
        patch("analysis.ranking_areas.detectar_expert_flags", return_value=[]),
        patch(
            "analysis.ranking_areas.obtener_audit_areas_config",
            return_value=[
                {"code": "130", "name": "CxC", "weight": 0.8},
                {"code": "200", "name": "Patrimonio", "weight": 0.9},
            ],
        ),
        patch("analysis.ranking_areas.cargar_areas_catalogo", return_value=[]),
    ):
        out = calcular_ranking_areas("cliente_x")

    assert out is not None
    assert not out.empty
    assert (out["pct_total"] == 0).all()
    assert (out["materialidad_relativa"] == 0).all()


def test_ranking_materialidad_cero_no_rompe_scoring():
    tb = pd.DataFrame(
        {
            "ls": ["130"],
            "codigo": ["130.1"],
            "saldo_actual": [1000.0],
            "nombre": ["CxC"],
        }
    )
    with (
        patch("analysis.ranking_areas.leer_tb", return_value=tb),
        patch("analysis.ranking_areas.calcular_variaciones", return_value=pd.DataFrame()),
        patch("analysis.ranking_areas.leer_perfil", return_value={}),
        patch(
            "analysis.ranking_areas.calcular_materialidad",
            return_value={"materialidad_sugerida": 0, "materialidad_desempeno": 0, "error_trivial": 0},
        ),
        patch("analysis.ranking_areas.detectar_expert_flags", return_value=[]),
        patch(
            "analysis.ranking_areas.obtener_audit_areas_config",
            return_value=[{"code": "130", "name": "CxC", "weight": 0.8}],
        ),
        patch("analysis.ranking_areas.cargar_areas_catalogo", return_value=[]),
    ):
        out = calcular_ranking_areas("cliente_x")

    assert out is not None
    row = out.iloc[0]
    assert row["materialidad_relativa"] == 0
    assert row["score_riesgo"] >= 0
