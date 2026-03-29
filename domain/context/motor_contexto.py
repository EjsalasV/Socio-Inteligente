from __future__ import annotations

import sys
from typing import Any, Dict

from domain.services.leer_perfil import (
    cargar_perfil,
    obtener_cliente,
    obtener_contexto_negocio,
    obtener_operacion,
    obtener_tesoreria,
    obtener_nomina,
    obtener_industria_inteligente,
    obtener_nombre_cliente,
    obtener_periodo,
    obtener_marco_referencial,
)

# =========================================================
# REGLAS GENERALES POR TIPO DE CONTEXTO
# =========================================================

REGLAS_CONTEXTO = {
    "holding": {
        "areas_prioritarias": ["14", "200", "1500", "1501", "425.2"],
        "areas_secundarias": ["136", "140"],
        "riesgos_esperados": [
            "Valuación de inversiones",
            "Aplicación de método VPP",
            "Presentación de resultados por inversiones",
            "Partes relacionadas",
            "Consistencia entre inversiones, ingresos y patrimonio",
        ],
        "observaciones": [
            "El riesgo principal suele concentrarse en inversiones y sus efectos en resultados y patrimonio.",
            "Las variaciones de ingresos pueden responder a resultados de inversiones y no necesariamente a operaciones ordinarias.",
            "Debe evaluarse soporte financiero de subsidiarias o participadas.",
        ],
    },
    "comercial": {
        "areas_prioritarias": ["110", "130.1", "1500", "425", "140"],
        "areas_secundarias": ["1600", "136"],
        "riesgos_esperados": [
            "Valuación de inventarios",
            "Deterioro de cartera",
            "Reconocimiento de ingresos",
            "Corte de compras y ventas",
            "Obligaciones con proveedores",
        ],
        "observaciones": [
            "En empresas comerciales, el foco suele estar en inventarios, cartera e ingresos.",
            "Las variaciones en inventarios e ingresos deben analizarse en conjunto.",
            "La rotación de cartera e inventarios es clave para interpretar riesgos.",
        ],
    },
    "servicios": {
        "areas_prioritarias": ["1500", "130.1", "1600", "140", "425"],
        "areas_secundarias": ["136", "1900"],
        "riesgos_esperados": [
            "Reconocimiento de ingresos",
            "Recuperabilidad de cuentas por cobrar",
            "Clasificación de gastos",
            "Flujos de efectivo",
            "Soporte de costos y gastos operativos",
        ],
        "observaciones": [
            "En empresas de servicios, el área crítica suele ser ingresos y cartera.",
            "Si no existen inventarios, el énfasis se traslada a ingresos, gastos y liquidez.",
            "Debe revisarse si los ingresos están correctamente devengados y soportados.",
        ],
    },
    "industrial": {
        "areas_prioritarias": ["110", "1", "1500", "1600", "425"],
        "areas_secundarias": ["140", "136"],
        "riesgos_esperados": [
            "Valuación de inventarios",
            "Costeo y absorción",
            "Existencia y depreciación de PPE",
            "Reconocimiento de ingresos",
            "Corte y clasificación de pasivos",
        ],
        "observaciones": [
            "En entidades industriales, inventarios y propiedad planta y equipo suelen ser áreas críticas.",
            "La relación entre inventarios, producción, costo y ventas debe mantenerse consistente.",
            "Es importante revisar la razonabilidad de costos y gastos de producción.",
        ],
    },
}


# =========================================================
# DETECCIÓN DEL CONTEXTO GENERAL
# =========================================================


def detectar_tipo_contexto(perfil: Dict[str, Any]) -> str:
    """
    Clasifica el cliente en uno de los tipos base:
    holding, comercial, servicios, industrial.
    """
    industria = obtener_industria_inteligente(perfil)
    if industria.get("sector_base"):
        sector_base = str(industria["sector_base"]).strip().lower()

        if sector_base in {"holding", "comercial", "servicios", "industrial"}:
            return sector_base

    cliente = obtener_cliente(perfil)
    contexto = obtener_contexto_negocio(perfil)
    operacion = obtener_operacion(perfil)

    sector = str(cliente.get("sector", "")).strip().lower()
    subsector = str(cliente.get("subsector", "")).strip().lower()
    descripcion = str(contexto.get("descripcion_breve_negocio", "")).strip().lower()
    actividad = str(contexto.get("actividad_principal", "")).strip().lower()

    if actividad in {"holding", "sociedad_cartera"}:
        return "holding"

    if "sociedad de cartera" in descripcion or "holding" in descripcion:
        return "holding"

    if (
        contexto.get("pertenece_a_grupo")
        and not operacion.get("tiene_inventarios_significativos", False)
        and any(x in descripcion for x in ["inversion", "participacion", "subsidiaria"])
    ):
        return "holding"

    texto_total = f"{sector} {subsector} {descripcion} {actividad}"

    if any(x in texto_total for x in ["industrial", "manufactura", "produccion", "fabrica"]):
        return "industrial"

    if any(x in texto_total for x in ["comercial", "retail", "comercio", "distrib", "import"]):
        return "comercial"

    return "servicios"


# =========================================================
# CONTEXTO ESTRUCTURADO
# =========================================================


def construir_contexto_cliente(perfil: Dict[str, Any]) -> Dict[str, Any]:
    tipo_contexto = detectar_tipo_contexto(perfil)
    reglas = REGLAS_CONTEXTO.get(tipo_contexto, {})

    contexto_negocio = obtener_contexto_negocio(perfil)
    operacion = obtener_operacion(perfil)
    tesoreria = obtener_tesoreria(perfil)
    nomina = obtener_nomina(perfil)

    areas_prioritarias = list(reglas.get("areas_prioritarias", []))
    areas_secundarias = list(reglas.get("areas_secundarias", []))
    riesgos_esperados = list(reglas.get("riesgos_esperados", []))
    observaciones = list(reglas.get("observaciones", []))

    if operacion.get("tiene_cartera_significativa") and "130.1" not in areas_prioritarias:
        areas_prioritarias.append("130.1")

    if (
        operacion.get("tiene_provision_cartera")
        and "Recuperabilidad de cuentas por cobrar" not in riesgos_esperados
    ):
        riesgos_esperados.append("Recuperabilidad de cuentas por cobrar")

    if operacion.get("tiene_prestamos_socios"):
        if "130.2" not in areas_secundarias:
            areas_secundarias.append("130.2")
        riesgos_esperados.append("Préstamos a socios y su adecuada presentación")

    if operacion.get("tiene_anticipos_proveedores"):
        riesgos_esperados.append("Clasificación y recuperabilidad de anticipos a proveedores")

    if operacion.get("maneja_reembolsos_gastos"):
        riesgos_esperados.append("Clasificación y soporte de reembolsos de gastos")

    if contexto_negocio.get("tiene_partes_relacionadas"):
        if "425.2" not in areas_secundarias and tipo_contexto != "holding":
            areas_secundarias.append("425.2")
        if "Partes relacionadas" not in riesgos_esperados:
            riesgos_esperados.append("Partes relacionadas")

    if tesoreria.get("usa_efectivo_intensivo") and "140" not in areas_prioritarias:
        areas_prioritarias.append("140")

    if nomina.get("tiene_empleados"):
        if "1600" not in areas_prioritarias and tipo_contexto == "servicios":
            areas_prioritarias.append("1600")
        riesgos_esperados.append("Gastos de personal y obligaciones laborales")

    areas_prioritarias = list(dict.fromkeys(areas_prioritarias))
    areas_secundarias = list(dict.fromkeys(areas_secundarias))
    riesgos_esperados = list(dict.fromkeys(riesgos_esperados))
    observaciones = list(dict.fromkeys(observaciones))

    return {
        "tipo_contexto": tipo_contexto,
        "areas_prioritarias": areas_prioritarias,
        "areas_secundarias": areas_secundarias,
        "riesgos_esperados": riesgos_esperados,
        "observaciones": observaciones,
    }


# =========================================================
# IMPRESIÓN
# =========================================================


def imprimir_contexto_cliente(nombre_cliente: str) -> None:
    perfil = cargar_perfil(nombre_cliente)
    contexto = construir_contexto_cliente(perfil)

    print("\n====================================================")
    print("MOTOR CONTEXTUAL DEL CLIENTE")
    print("====================================================\n")

    print(f"Cliente: {obtener_nombre_cliente(perfil)}")
    print(f"Periodo: {obtener_periodo(perfil)}")
    print(f"Marco referencial: {obtener_marco_referencial(perfil)}")
    print(f"Tipo de contexto detectado: {contexto['tipo_contexto']}\n")

    print("Áreas prioritarias esperadas:")
    for area in contexto["areas_prioritarias"]:
        print(f"- {area}")

    print("\nÁreas secundarias:")
    for area in contexto["areas_secundarias"]:
        print(f"- {area}")

    print("\nRiesgos esperados por naturaleza del cliente:")
    for riesgo in contexto["riesgos_esperados"]:
        print(f"- {riesgo}")

    print("\nObservaciones contextuales:")
    for obs in contexto["observaciones"]:
        print(f"- {obs}")

    print()


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise ValueError(
                "Debes indicar el nombre de la carpeta del cliente. "
                "Ejemplo: python motor/motor_contexto.py bf_ip_2025"
            )

        cliente = sys.argv[1]
        imprimir_contexto_cliente(cliente)

    except Exception as e:
        print(f"\nError en motor contextual: {e}")
