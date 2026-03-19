"""
Módulo de benchmark sectorial para auditoría.
Compara ratios del cliente contra referencias por sector
para identificar desviaciones que requieren atención.
"""
from __future__ import annotations

from typing import Any

from analysis.ratios import calcular_ratios
from domain.services.leer_perfil import leer_perfil


# Benchmarks referenciales por sector
# Fuente: rangos típicos de industria para empresas PYME en Ecuador
BENCHMARKS_SECTOR: dict[str, dict[str, dict[str, float]]] = {
    "comerciales": {
        "razon_corriente":  {"min": 1.2, "max": 2.5, "optimo": 1.8},
        "endeudamiento":    {"min": 0.3, "max": 0.6, "optimo": 0.45},
        "margen_neto":      {"min": 0.02, "max": 0.12, "optimo": 0.06},
        "rotacion_activos": {"min": 0.8, "max": 2.5, "optimo": 1.5},
        "roa":              {"min": 0.03, "max": 0.12, "optimo": 0.07},
    },
    "servicios": {
        "razon_corriente":  {"min": 1.0, "max": 2.0, "optimo": 1.5},
        "endeudamiento":    {"min": 0.2, "max": 0.55, "optimo": 0.38},
        "margen_neto":      {"min": 0.05, "max": 0.25, "optimo": 0.15},
        "rotacion_activos": {"min": 0.5, "max": 2.0, "optimo": 1.0},
        "roa":              {"min": 0.05, "max": 0.18, "optimo": 0.10},
    },
    "holding": {
        "razon_corriente":  {"min": 0.5, "max": 3.0, "optimo": 1.2},
        "endeudamiento":    {"min": 0.1, "max": 0.5, "optimo": 0.25},
        "margen_neto":      {"min": 0.0, "max": 1.0, "optimo": 0.20},
        "rotacion_activos": {"min": 0.0, "max": 0.5, "optimo": 0.10},
        "roa":              {"min": 0.0, "max": 0.15, "optimo": 0.05},
    },
    "manufactura": {
        "razon_corriente":  {"min": 1.2, "max": 2.8, "optimo": 1.8},
        "endeudamiento":    {"min": 0.35, "max": 0.65, "optimo": 0.50},
        "margen_neto":      {"min": 0.03, "max": 0.15, "optimo": 0.08},
        "rotacion_activos": {"min": 0.4, "max": 1.5, "optimo": 0.9},
        "roa":              {"min": 0.03, "max": 0.12, "optimo": 0.07},
    },
    "default": {
        "razon_corriente":  {"min": 1.0, "max": 2.5, "optimo": 1.5},
        "endeudamiento":    {"min": 0.2, "max": 0.65, "optimo": 0.45},
        "margen_neto":      {"min": 0.02, "max": 0.20, "optimo": 0.10},
        "rotacion_activos": {"min": 0.3, "max": 2.0, "optimo": 1.0},
        "roa":              {"min": 0.02, "max": 0.15, "optimo": 0.07},
    },
}


def obtener_benchmark_sector(sector: str) -> dict[str, dict[str, float]]:
    sector_norm = str(sector or "").strip().lower()
    return BENCHMARKS_SECTOR.get(sector_norm, BENCHMARKS_SECTOR["default"])


def comparar_con_benchmark(cliente: str) -> list[dict[str, Any]]:
    """
    Compara ratios del cliente contra benchmark de su sector.

    Returns:
        Lista de comparaciones con estado (ok / alerta / critico).
    """
    perfil = leer_perfil(cliente)
    if not perfil:
        return []

    sector = perfil.get("cliente", {}).get("sector", "default")
    benchmark = obtener_benchmark_sector(sector)
    ratios = calcular_ratios(cliente)
    if not ratios:
        return []

    resultados = []

    ratio_map = {
        "razon_corriente": ratios.get("liquidez", {}).get("razon_corriente"),
        "endeudamiento":   ratios.get("solvencia", {}).get("endeudamiento"),
        "margen_neto":     ratios.get("rentabilidad", {}).get("margen_neto"),
        "rotacion_activos":ratios.get("actividad", {}).get("rotacion_activos"),
        "roa":             ratios.get("rentabilidad", {}).get("roa"),
    }

    for nombre_ratio, valor in ratio_map.items():
        ref = benchmark.get(nombre_ratio)
        if ref is None or valor is None:
            continue

        desviacion = round(valor - ref["optimo"], 4)
        dentro_rango = ref["min"] <= valor <= ref["max"]

        if dentro_rango:
            estado = "ok"
        elif abs(desviacion) > (ref["max"] - ref["min"]):
            estado = "critico"
        else:
            estado = "alerta"

        resultados.append({
            "ratio": nombre_ratio,
            "sector": sector,
            "valor_cliente": valor,
            "benchmark_min": ref["min"],
            "benchmark_optimo": ref["optimo"],
            "benchmark_max": ref["max"],
            "desviacion": desviacion,
            "dentro_rango": dentro_rango,
            "estado": estado,
        })

    return resultados


def resumen_benchmark(cliente: str) -> dict[str, Any]:
    """
    Resumen ejecutivo del benchmark para dashboards.
    """
    comparaciones = comparar_con_benchmark(cliente)
    if not comparaciones:
        return {"total": 0, "ok": 0, "alerta": 0, "critico": 0, "detalle": []}

    return {
        "total": len(comparaciones),
        "ok": sum(1 for c in comparaciones if c["estado"] == "ok"),
        "alerta": sum(1 for c in comparaciones if c["estado"] == "alerta"),
        "critico": sum(1 for c in comparaciones if c["estado"] == "critico"),
        "detalle": comparaciones,
    }
