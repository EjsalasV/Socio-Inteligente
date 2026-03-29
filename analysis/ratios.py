"""
Módulo de ratios financieros para auditoría.
Calcula indicadores de liquidez, solvencia, rentabilidad y actividad
a partir del Trial Balance del cliente.
"""

from __future__ import annotations

from typing import Any


from analysis.lector_tb import obtener_resumen_tb


def calcular_ratios(cliente: str) -> dict[str, Any]:
    """
    Calcula ratios financieros clave del cliente.

    Returns:
        dict con ratios agrupados por categoría.
        Retorna dict vacío si no hay datos suficientes.
    """
    resumen = obtener_resumen_tb(cliente)
    if not resumen:
        return {}

    activo = abs(float(resumen.get("ACTIVO", 0) or 0))
    pasivo = abs(float(resumen.get("PASIVO", 0) or 0))
    patrimonio = abs(float(resumen.get("PATRIMONIO", 0) or 0))
    ingresos = abs(float(resumen.get("INGRESOS", 0) or 0))
    gastos = abs(float(resumen.get("GASTOS", 0) or 0))

    def _safe_div(a: float, b: float) -> float | None:
        if b == 0:
            return None
        return round(a / b, 4)

    utilidad_neta = ingresos - gastos

    ratios: dict[str, Any] = {
        "liquidez": {
            "razon_corriente": _safe_div(activo, pasivo),
            "descripcion": "Activo / Pasivo — capacidad de pago general",
        },
        "solvencia": {
            "endeudamiento": _safe_div(pasivo, activo),
            "deuda_patrimonio": _safe_div(pasivo, patrimonio),
            "descripcion": "Nivel de apalancamiento financiero",
        },
        "rentabilidad": {
            "roa": _safe_div(utilidad_neta, activo),
            "roe": _safe_div(utilidad_neta, patrimonio),
            "margen_neto": _safe_div(utilidad_neta, ingresos),
            "descripcion": "Capacidad de generar utilidades",
        },
        "actividad": {
            "rotacion_activos": _safe_div(ingresos, activo),
            "descripcion": "Eficiencia en uso de activos",
        },
        "_meta": {
            "activo": activo,
            "pasivo": pasivo,
            "patrimonio": patrimonio,
            "ingresos": ingresos,
            "gastos": gastos,
            "utilidad_neta": round(utilidad_neta, 2),
        },
    }

    return ratios


def interpretar_ratio(nombre: str, valor: float | None) -> str:
    """
    Devuelve interpretación simple de un ratio para uso en briefings.
    """
    if valor is None:
        return "Sin datos suficientes para calcular."

    interpretaciones = {
        "razon_corriente": (
            "Saludable (>1.5)"
            if valor >= 1.5
            else "Ajustado (1.0-1.5)" if valor >= 1.0 else "Riesgo de liquidez (<1.0)"
        ),
        "endeudamiento": (
            "Bajo (<0.4)" if valor < 0.4 else "Moderado (0.4-0.6)" if valor < 0.6 else "Alto (>0.6)"
        ),
        "deuda_patrimonio": (
            "Conservador (<0.5)"
            if valor < 0.5
            else "Moderado (0.5-1.5)" if valor < 1.5 else "Apalancado (>1.5)"
        ),
        "roa": (
            "Excelente (>10%)"
            if valor > 0.10
            else "Bueno (5-10%)" if valor > 0.05 else "Bajo (<5%)"
        ),
        "roe": (
            "Excelente (>15%)"
            if valor > 0.15
            else "Bueno (10-15%)" if valor > 0.10 else "Bajo (<10%)"
        ),
        "margen_neto": (
            "Alto (>15%)" if valor > 0.15 else "Moderado (5-15%)" if valor > 0.05 else "Bajo (<5%)"
        ),
        "rotacion_activos": (
            "Alta (>1.0)" if valor > 1.0 else "Normal (0.5-1.0)" if valor > 0.5 else "Baja (<0.5)"
        ),
    }
    return interpretaciones.get(nombre, f"Valor: {valor:.4f}")


def resumen_ratios(cliente: str) -> list[dict[str, Any]]:
    """
    Devuelve lista plana de ratios para mostrar en tablas/dashboards.
    """
    ratios = calcular_ratios(cliente)
    if not ratios:
        return []

    salida = []
    for categoria, datos in ratios.items():
        if categoria.startswith("_"):
            continue
        desc = datos.get("descripcion", "")
        for nombre, valor in datos.items():
            if nombre == "descripcion":
                continue
            salida.append(
                {
                    "categoria": categoria,
                    "ratio": nombre,
                    "valor": valor,
                    "interpretacion": interpretar_ratio(nombre, valor),
                    "descripcion_categoria": desc,
                }
            )
    return salida
