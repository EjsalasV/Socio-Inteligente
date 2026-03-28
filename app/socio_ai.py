"""
SocioAI - Punto de entrada principal.

Orquestador del flujo de auditoria:
cliente -> perfil -> TB -> variaciones -> ranking de areas
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Optional

from analysis.lector_tb import leer_tb, obtener_resumen_tb
from analysis.ranking_areas import calcular_ranking_areas, obtener_indicadores_clave
from analysis.variaciones import calcular_variaciones, resumen_variaciones
from domain.services.leer_perfil import leer_perfil, obtener_datos_clave

# Ensure Windows terminals can print Unicode output safely.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run_cliente(cliente: str) -> Optional[Dict[str, Any]]:
    print("\n" + "=" * 70)
    print(f"INICIANDO ANALISIS: {cliente}")
    print("=" * 70)

    print("\nPASO 1: Cargando perfil cliente...")
    print("-" * 70)
    perfil = leer_perfil(cliente)
    if not perfil:
        print(f"ERROR Cliente '{cliente}' no encontrado o perfil invalido")
        return {
            "status": "ERROR",
            "cliente": cliente,
            "mensaje": "No se pudo cargar el perfil",
        }

    datos_clave = obtener_datos_clave(cliente) or {}
    print(f"OK Cliente cargado: {datos_clave.get('nombre', cliente)}")
    print(f"   RUC: {datos_clave.get('ruc', 'N/A')}")
    print(f"   Sector: {datos_clave.get('sector', 'N/A')}")

    print("\nPASO 2: Cargando trial balance...")
    print("-" * 70)
    tb = leer_tb(cliente)
    if tb is None or tb.empty:
        print("ERROR No se pudo cargar el trial balance")
        return {
            "status": "ERROR",
            "cliente": cliente,
            "mensaje": "No se pudo cargar el TB",
        }

    resumen_tb = obtener_resumen_tb(cliente) or {}
    print(f"OK TB cargado: {tb.shape[0]} cuentas")
    print(f"   Total Activos: ${resumen_tb.get('ACTIVO', 0):,.0f}")
    print(f"   Total Pasivos: ${resumen_tb.get('PASIVO', 0):,.0f}")
    print(f"   Total Patrimonio: ${resumen_tb.get('PATRIMONIO', 0):,.0f}")

    print("\nPASO 3: Calculando variaciones...")
    print("-" * 70)
    _ = calcular_variaciones(cliente)
    resumen_var = resumen_variaciones(cliente)
    if resumen_var:
        print(f"OK Variaciones calculadas: {resumen_var.get('total_cuentas_variacion', 0)} cuentas")
        print(f"   Mayor variacion: ${resumen_var.get('mayor_variacion', 0):,.0f}")
        print(f"   Top cuentas: {', '.join(resumen_var.get('cuentas_top_5', [])[:2])}")
    else:
        print("INFO Sin variaciones significativas")
        resumen_var = {
            "total_cuentas_variacion": 0,
            "mayor_variacion": 0,
            "cuentas_top_5": [],
        }

    print("\nPASO 4: Calculando ranking de areas...")
    print("-" * 70)
    ranking = calcular_ranking_areas(cliente)
    indicadores = obtener_indicadores_clave(cliente) or {}

    if ranking is not None and not ranking.empty:
        print("OK Ranking de areas calculado:")
        for idx, row in ranking.head(3).iterrows():
            print(
                f"   {idx + 1}. {row['nombre']:30} | "
                f"Score: {row['score_riesgo']:5.1f} | "
                f"${row['saldo_total']:>12,.0f}"
            )

        print("\n   Indicadores clave:")
        print(f"   - Areas alto riesgo: {indicadores.get('areas_alto_riesgo', 0)}")
        print(f"   - Areas medio riesgo: {indicadores.get('areas_medio_riesgo', 0)}")
        print(f"   - Areas bajo riesgo: {indicadores.get('areas_bajo_riesgo', 0)}")
        print(
            "   - Concentracion principal area: "
            f"{indicadores.get('concentracion_principal_area', 0):.1f}%"
        )
    else:
        print("WARN No se pudo calcular ranking")
        ranking = None

    print("\n" + "=" * 70)
    print("RESUMEN EJECUTIVO")
    print("=" * 70)

    resultado = {
        "status": "EXITOSO",
        "cliente": cliente,
        "perfil": {
            "nombre": datos_clave.get("nombre"),
            "ruc": datos_clave.get("ruc"),
            "sector": datos_clave.get("sector"),
            "moneda": datos_clave.get("moneda"),
        },
        "balance": {
            "total_activos": resumen_tb.get("ACTIVO", 0),
            "total_pasivos": resumen_tb.get("PASIVO", 0),
            "total_patrimonio": resumen_tb.get("PATRIMONIO", 0),
            "num_cuentas": tb.shape[0],
        },
        "variaciones": resumen_var,
        "areas_riesgo": indicadores,
        "top_areas": (
            ranking[["ranking", "area", "nombre", "score_riesgo"]]
            .head(3)
            .to_dict("records")
            if ranking is not None
            else []
        ),
    }

    print("\nOK ANALISIS COMPLETADO EXITOSAMENTE")
    print(f"   Cliente: {resultado['perfil']['nombre']}")
    print(f"   Cuentas procesadas: {resultado['balance']['num_cuentas']}")
    print(f"   Patrimonio total: ${resultado['balance']['total_patrimonio']:,.0f}")
    print(f"   Areas alto riesgo: {resultado['areas_riesgo'].get('areas_alto_riesgo', 0)}")

    if resultado["top_areas"]:
        print("\n   AREAS A PRIORIZAR:")
        for area in resultado["top_areas"]:
            print(f"      {area['ranking']}. {area['nombre']} (Score: {area['score_riesgo']})")

    print("\n" + "=" * 70 + "\n")
    return resultado


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python socio_ai.py <nombre_cliente>")
        print("Ejemplo: python socio_ai.py cliente_demo")
        raise SystemExit(1)

    cliente = sys.argv[1]
    resultado = run_cliente(cliente)

    if not resultado or resultado.get("status") != "EXITOSO":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
