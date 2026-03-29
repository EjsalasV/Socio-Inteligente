"""
Módulo de análisis de tendencias para auditoría.
Detecta patrones de evolución en cuentas y áreas del TB.
"""

from __future__ import annotations

from typing import Any


from analysis.lector_tb import leer_tb


def calcular_tendencias(cliente: str) -> list[dict[str, Any]]:
    """
    Analiza tendencias de cuentas con saldo actual vs anterior.

    Returns:
        Lista de cuentas con clasificación de tendencia.
    """
    tb = leer_tb(cliente)
    if tb is None or tb.empty:
        return []

    resultados = []

    saldo_actual_col = None
    saldo_anterior_col = None
    for c in ["saldo_actual", "saldo_2025", "saldo"]:
        if c in tb.columns:
            saldo_actual_col = c
            break
    for c in ["saldo_2024", "saldo_anterior"]:
        if c in tb.columns:
            saldo_anterior_col = c
            break

    if not saldo_actual_col:
        return []

    for _, row in tb.iterrows():
        actual = float(row.get(saldo_actual_col, 0) or 0)
        anterior = float(row.get(saldo_anterior_col, 0) or 0) if saldo_anterior_col else 0

        if anterior == 0 and actual == 0:
            continue

        if anterior == 0:
            variacion_pct = None
            tendencia = "nueva_cuenta"
        elif actual == 0:
            variacion_pct = -100.0
            tendencia = "cuenta_eliminada"
        else:
            variacion_pct = round(((actual - anterior) / abs(anterior)) * 100, 2)
            if variacion_pct > 30:
                tendencia = "crecimiento_alto"
            elif variacion_pct > 10:
                tendencia = "crecimiento_moderado"
            elif variacion_pct < -30:
                tendencia = "caida_alta"
            elif variacion_pct < -10:
                tendencia = "caida_moderada"
            else:
                tendencia = "estable"

        nombre = str(row.get("nombre", row.get("nombre_cuenta", "")))
        codigo = str(row.get("codigo", row.get("numero_cuenta", "")))
        ls = str(row.get("ls", ""))

        resultados.append(
            {
                "codigo": codigo,
                "nombre": nombre,
                "ls": ls,
                "saldo_anterior": round(anterior, 2),
                "saldo_actual": round(actual, 2),
                "variacion_absoluta": round(actual - anterior, 2),
                "variacion_porcentual": variacion_pct,
                "tendencia": tendencia,
            }
        )

    resultados.sort(key=lambda x: abs(x["variacion_absoluta"]), reverse=True)
    return resultados


def cuentas_por_tendencia(
    cliente: str,
    tendencia: str,
) -> list[dict[str, Any]]:
    """
    Filtra cuentas por tipo de tendencia.

    tendencia: 'crecimiento_alto' | 'crecimiento_moderado' |
               'caida_alta' | 'caida_moderada' |
               'estable' | 'nueva_cuenta' | 'cuenta_eliminada'
    """
    return [t for t in calcular_tendencias(cliente) if t["tendencia"] == tendencia]


def alertas_tendencias(cliente: str) -> list[dict[str, Any]]:
    """
    Devuelve solo cuentas con tendencias que requieren atención
    de auditoría (crecimientos/caídas altas y cuentas nuevas).
    """
    tendencias_alerta = {"crecimiento_alto", "caida_alta", "nueva_cuenta", "cuenta_eliminada"}
    return [t for t in calcular_tendencias(cliente) if t["tendencia"] in tendencias_alerta]


def resumen_tendencias(cliente: str) -> dict[str, Any]:
    """
    Resumen ejecutivo de tendencias para dashboards.
    """
    tendencias = calcular_tendencias(cliente)
    if not tendencias:
        return {}

    conteo: dict[str, int] = {}
    for t in tendencias:
        conteo[t["tendencia"]] = conteo.get(t["tendencia"], 0) + 1

    return {
        "total_cuentas": len(tendencias),
        "conteo_por_tendencia": conteo,
        "cuentas_alerta": len(alertas_tendencias(cliente)),
        "mayor_crecimiento": tendencias[0] if tendencias else None,
    }
