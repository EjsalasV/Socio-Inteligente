"""Tests for lector_mayor.py"""
from __future__ import annotations

import pandas as pd
import pytest

from analysis.lector_mayor import (
    buscar_movimientos,
    filtrar_por_cuenta,
    filtrar_por_ls,
    mayor_existe,
    resumen_mayor,
)


@pytest.fixture
def df_sample():
    return pd.DataFrame({
        "fecha": ["2025-01-10", "2025-01-15", "2025-02-01"],
        "numero_cuenta": ["1.02.07.07.001", "5.2.18.02.032", "2.01.13.03.023"],
        "nombre_cuenta": ["Inversiones VPP", "Auditoría Externa", "CxP Inversiones"],
        "ls": ["14", "1600", "425.2"],
        "descripcion": ["Reconoc. VPP Q1", "Honorarios auditoría", "Pago proveedor"],
        "referencia": ["EG-001", "EG-002", "EG-003"],
        "debe": [157080.75, 0.0, 3993.0],
        "haber": [0.0, 5910.0, 0.0],
        "saldo": [157080.75, -5910.0, 3993.0],
        "tipo": ["DEBE", "HABER", "DEBE"],
        "movimiento": [157080.75, -5910.0, 3993.0],
    })


def test_mayor_existe_false():
    assert mayor_existe("cliente_inexistente_xyz") is False


def test_filtrar_por_ls(df_sample):
    result = filtrar_por_ls(df_sample, "14")
    assert len(result) == 1
    assert result.iloc[0]["numero_cuenta"] == "1.02.07.07.001"


def test_filtrar_por_ls_empty(df_sample):
    result = filtrar_por_ls(df_sample, "999")
    assert result.empty


def test_filtrar_por_cuenta(df_sample):
    result = filtrar_por_cuenta(df_sample, "1.02")
    assert len(result) == 1


def test_buscar_por_texto(df_sample):
    result = buscar_movimientos(df_sample, texto="VPP")
    assert len(result) == 1
    assert "VPP" in result.iloc[0]["descripcion"]


def test_buscar_por_monto_min(df_sample):
    result = buscar_movimientos(df_sample, monto_min=10000.0)
    assert len(result) == 1
    assert result.iloc[0]["debe"] == 157080.75


def test_buscar_sin_filtros(df_sample):
    result = buscar_movimientos(df_sample)
    assert len(result) == 3


def test_resumen_mayor(df_sample):
    r = resumen_mayor(df_sample)
    assert r["total_movimientos"] == 3
    assert r["cuentas_distintas"] == 3
    assert r["total_debe"] > 0


def test_resumen_mayor_empty():
    r = resumen_mayor(pd.DataFrame())
    assert r["total_movimientos"] == 0


def test_filtrar_por_ls_none():
    result = filtrar_por_ls(None, "14")
    assert result.empty

