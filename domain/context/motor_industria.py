from __future__ import annotations

import sys
from typing import Any, Dict, List, Set

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
# BASE DE CONOCIMIENTO DE INDUSTRIAS
# =========================================================

BASE_INDUSTRIAS = {
    "holding": {
        "default": {
            "areas_prioritarias": ["14", "200", "1500", "1501", "425.2"],
            "areas_secundarias": ["136", "140"],
            "riesgos_esperados": [
                "ValuaciÃ³n de inversiones",
                "AplicaciÃ³n de mÃ©todo VPP",
                "PresentaciÃ³n de resultados por inversiones",
                "Partes relacionadas",
                "Consistencia entre inversiones, ingresos y patrimonio",
            ],
            "observaciones": [
                "El riesgo principal suele concentrarse en inversiones y sus efectos en resultados y patrimonio.",
                "Las variaciones de ingresos pueden responder a resultados de inversiones y no necesariamente a operaciones ordinarias.",
                "Debe evaluarse soporte financiero de subsidiarias o participadas.",
            ],
            "alertas_profesionales": [
                "No asumir que el principal riesgo estÃ¡ en ingresos solo por variaciÃ³n matemÃ¡tica si estos provienen de inversiones.",
                "Revisar si la sustancia econÃ³mica del negocio estÃ¡ correctamente reflejada en la presentaciÃ³n de estados financieros.",
            ],
            "supuestos_a_validar": [
                "Si las inversiones corresponden realmente a subsidiarias, asociadas o simples participaciones.",
                "Si el uso de VPP es consistente con el porcentaje de control o influencia significativa.",
            ],
        }
    },

    "comercial": {
        "default": {
            "areas_prioritarias": ["110", "130.1", "1500", "425", "140"],
            "areas_secundarias": ["1600", "136"],
            "riesgos_esperados": [
                "ValuaciÃ³n de inventarios",
                "Deterioro de cartera",
                "Reconocimiento de ingresos",
                "Corte de compras y ventas",
                "Obligaciones con proveedores",
            ],
            "observaciones": [
                "En empresas comerciales, el foco suele estar en inventarios, cartera e ingresos.",
                "Las variaciones en inventarios e ingresos deben analizarse en conjunto.",
                "La rotaciÃ³n de cartera e inventarios es clave para interpretar riesgos.",
            ],
            "alertas_profesionales": [
                "No revisar inventarios aislados del comportamiento de ventas y margen.",
                "Evaluar si el crecimiento de ingresos estÃ¡ acompaÃ±ado por crecimiento razonable en cartera y compras.",
            ],
            "supuestos_a_validar": [
                "Si la empresa realmente mantiene inventarios materiales o funciona como intermediaria.",
                "Si existen productos obsoletos o de baja rotaciÃ³n.",
            ],
        },

        "retail": {
            "areas_prioritarias": ["110", "1500", "140", "425", "130.1"],
            "areas_secundarias": ["1600", "136"],
            "riesgos_esperados": [
                "Inventarios obsoletos",
                "Corte de ventas",
                "Faltantes de caja",
                "Diferencias entre sistema y conteo fÃ­sico",
            ],
            "observaciones": [
                "En retail suele ser crÃ­tico revisar inventario, efectivo y corte de ventas.",
            ],
            "alertas_profesionales": [
                "El volumen de operaciones puede ocultar errores pequeÃ±os repetitivos pero acumulativos.",
            ],
            "supuestos_a_validar": [
                "Si el sistema de facturaciÃ³n y el control fÃ­sico son consistentes.",
            ],
        },

        "distribuidora": {
            "areas_prioritarias": ["110", "130.1", "1500", "425"],
            "areas_secundarias": ["140", "136"],
            "riesgos_esperados": [
                "ValuaciÃ³n de inventarios",
                "Cartera concentrada",
                "Descuentos y devoluciones",
                "Corte de compras y ventas",
            ],
            "observaciones": [
                "En distribuidoras, cartera e inventario suelen moverse de forma conjunta.",
            ],
            "alertas_profesionales": [
                "No evaluar ingresos sin revisar devoluciones, descuentos y cartera.",
            ],
            "supuestos_a_validar": [
                "Si la polÃ­tica de provisiÃ³n de cartera es consistente con la antigÃ¼edad real.",
            ],
        },
    },

    "servicios": {
        "default": {
            "areas_prioritarias": ["1500", "130.1", "1600", "140", "425"],
            "areas_secundarias": ["136", "1900"],
            "riesgos_esperados": [
                "Reconocimiento de ingresos",
                "Recuperabilidad de cuentas por cobrar",
                "ClasificaciÃ³n de gastos",
                "Flujos de efectivo",
                "Soporte de costos y gastos operativos",
            ],
            "observaciones": [
                "En empresas de servicios, el Ã¡rea crÃ­tica suele ser ingresos y cartera.",
                "Si no existen inventarios, el Ã©nfasis se traslada a ingresos, gastos y liquidez.",
                "Debe revisarse si los ingresos estÃ¡n correctamente devengados y soportados.",
            ],
            "alertas_profesionales": [
                "No sobrevalorar riesgos de inventario si el negocio realmente no depende de ellos.",
                "Revisar si los ingresos estÃ¡n ligados a contratos, eventos o prestaciÃ³n continua.",
            ],
            "supuestos_a_validar": [
                "Si la polÃ­tica de reconocimiento de ingresos refleja el servicio realmente prestado.",
            ],
        },

        "funeraria": {
            "areas_prioritarias": ["5", "1500", "140", "425", "1600"],
            "areas_secundarias": ["110", "136"],
            "riesgos_esperados": [
                "ClasificaciÃ³n y mediciÃ³n de propiedades de inversiÃ³n",
                "Reconocimiento de ingresos por servicios funerarios",
                "Soporte de cobros y anticipos",
                "RevelaciÃ³n de activos de naturaleza especial",
            ],
            "observaciones": [
                "En una funeraria, el entendimiento del negocio es clave para interpretar correctamente propiedades de inversiÃ³n y servicios funerarios.",
                "No todas las propiedades vinculadas al negocio funerario deben analizarse con la misma lÃ³gica que un activo industrial o comercial.",
                "La naturaleza del servicio puede hacer que ciertos activos mantengan su utilidad y valor econÃ³mico por perÃ­odos prolongados.",
            ],
            "alertas_profesionales": [
                "No asumir deterioro automÃ¡tico de propiedades de inversiÃ³n solo por antigÃ¼edad o falta de movimiento.",
                "Primero entender cÃ³mo se utiliza el activo en el modelo de negocio funerario.",
            ],
            "supuestos_a_validar": [
                "Si las propiedades estÃ¡n clasificadas correctamente como propiedades de inversiÃ³n, PPE u otro tipo de activo.",
                "Si la ausencia de deterioro estÃ¡ soportada por la naturaleza econÃ³mica del activo y del negocio.",
            ],
        },

        "hospital": {
            "areas_prioritarias": ["1500", "130.1", "1", "1600", "425"],
            "areas_secundarias": ["110", "136"],
            "riesgos_esperados": [
                "Reconocimiento de ingresos por servicios mÃ©dicos",
                "Cartera a aseguradoras o convenios",
                "ValuaciÃ³n de PPE mÃ©dico",
                "ClasificaciÃ³n de gastos operativos",
            ],
            "observaciones": [
                "En hospitales y salud, cartera e ingresos suelen depender de convenios, aseguradoras y tratamientos.",
            ],
            "alertas_profesionales": [
                "El ingreso devengado debe corresponder a servicios efectivamente prestados.",
            ],
            "supuestos_a_validar": [
                "Si existen glosas, devoluciones o disputas con aseguradoras.",
            ],
        },

        "consultoria": {
            "areas_prioritarias": ["1500", "130.1", "1600", "140"],
            "areas_secundarias": ["1900", "136"],
            "riesgos_esperados": [
                "Reconocimiento de ingresos por avance o hitos",
                "Cartera vencida",
                "Gastos operativos y honorarios",
            ],
            "observaciones": [
                "En consultorÃ­a suele ser crÃ­tico el reconocimiento correcto del ingreso y la recuperaciÃ³n de cartera.",
            ],
            "alertas_profesionales": [
                "Ingresos altos sin cartera o efectivo consistente pueden requerir revisiÃ³n.",
            ],
            "supuestos_a_validar": [
                "Si el ingreso se reconoce por contrato, hito o prestaciÃ³n completada.",
            ],
        },

        "firma_legal_propiedad_intelectual": {
            "areas_prioritarias": ["1500", "130.1", "1600", "130.2", "136"],
            "areas_secundarias": ["140", "425.2", "1900"],
            "riesgos_esperados": [
                "Reconocimiento de ingresos por honorarios profesionales",
                "Recuperabilidad de cuentas por cobrar",
                "AdecuaciÃ³n de la provisiÃ³n de cartera",
                "PrÃ©stamos a socios",
                "Reembolsos de gastos y su clasificaciÃ³n",
                "Anticipos a proveedores",
                "Operaciones con partes relacionadas",
            ],
            "observaciones": [
                "En firmas legales o de servicios profesionales especializados, el foco principal suele estar en ingresos, cartera, provisiÃ³n de cartera y cuentas relacionadas con socios.",
                "La ausencia de inventarios desplaza el anÃ¡lisis hacia ingresos, cuentas por cobrar, gastos y cumplimiento tributario.",
                "Las operaciones internacionales y reembolsos pueden generar riesgos de clasificaciÃ³n y soporte.",
            ],
            "alertas_profesionales": [
                "No asumir que ingresos altos implican bajo riesgo si la cartera no es recuperable.",
                "PrÃ©stamos a socios y reembolsos deben analizarse con especial cuidado por sustancia y presentaciÃ³n.",
                "La provisiÃ³n de cartera debe revisarse frente a antigÃ¼edad real y evidencia de recuperabilidad.",
            ],
            "supuestos_a_validar": [
                "Si la polÃ­tica de reconocimiento de ingresos refleja adecuadamente los servicios efectivamente prestados.",
                "Si los prÃ©stamos a socios estÃ¡n adecuadamente aprobados, soportados y presentados.",
                "Si la provisiÃ³n de cartera responde al riesgo real de incobrabilidad.",
                "Si los reembolsos de gastos estÃ¡n correctamente documentados y clasificados.",
            ],
        },
    },

    "industrial": {
        "default": {
            "areas_prioritarias": ["110", "1", "1500", "1600", "425"],
            "areas_secundarias": ["140", "136"],
            "riesgos_esperados": [
                "ValuaciÃ³n de inventarios",
                "Costeo y absorciÃ³n",
                "Existencia y depreciaciÃ³n de PPE",
                "Reconocimiento de ingresos",
                "Corte y clasificaciÃ³n de pasivos",
            ],
            "observaciones": [
                "En entidades industriales, inventarios y propiedad planta y equipo suelen ser Ã¡reas crÃ­ticas.",
                "La relaciÃ³n entre inventarios, producciÃ³n, costo y ventas debe mantenerse consistente.",
                "Es importante revisar la razonabilidad de costos y gastos de producciÃ³n.",
            ],
            "alertas_profesionales": [
                "No analizar inventarios sin revisar costeo y PPE asociado a producciÃ³n.",
            ],
            "supuestos_a_validar": [
                "Si el sistema de costeo refleja adecuadamente la operaciÃ³n real.",
            ],
        },

        "manufactura": {
            "areas_prioritarias": ["110", "1", "1500", "1600", "425"],
            "areas_secundarias": ["140", "136"],
            "riesgos_esperados": [
                "Costo estÃ¡ndar vs real",
                "Obsolescencia de inventario",
                "Capacidad ociosa",
                "DepreciaciÃ³n de maquinaria",
            ],
            "observaciones": [
                "En manufactura, el riesgo suele estar en inventarios, costeo y maquinaria.",
            ],
            "alertas_profesionales": [
                "Una variaciÃ³n baja en inventarios no elimina el riesgo de valuaciÃ³n si el costeo es deficiente.",
            ],
            "supuestos_a_validar": [
                "Si existe producciÃ³n en proceso y cÃ³mo se valÃºa.",
            ],
        },
    },
}


# =========================================================
# EXTRACCIÃ“N DESDE PERFIL
# =========================================================

def detectar_sector_base(perfil: Dict[str, Any]) -> str:
    industria = obtener_industria_inteligente(perfil)
    if industria.get("sector_base"):
        return str(industria["sector_base"]).strip().lower()

    cliente = obtener_cliente(perfil)
    contexto = obtener_contexto_negocio(perfil)
    operacion = obtener_operacion(perfil)

    sector = str(cliente.get("sector", "")).strip().lower()
    subsector = str(cliente.get("subsector", "")).strip().lower()
    descripcion = str(contexto.get("descripcion_breve_negocio", "")).strip().lower()

    if contexto.get("pertenece_a_grupo") and "holding" in descripcion:
        return "holding"

    if "sociedad de cartera" in descripcion:
        return "holding"

    texto_total = f"{sector} {subsector} {descripcion}"

    if any(x in texto_total for x in ["industrial", "manufactura", "produccion", "fabrica"]):
        return "industrial"

    if any(x in texto_total for x in ["comercial", "retail", "comercio", "distrib", "import"]):
        return "comercial"

    if operacion.get("tiene_inventarios_significativos"):
        return "comercial"

    return "servicios"


def detectar_subtipo_negocio(perfil: Dict[str, Any], sector_base: str) -> str:
    industria = obtener_industria_inteligente(perfil)
    if industria.get("subtipo_negocio"):
        return str(industria["subtipo_negocio"]).strip().lower()

    cliente = obtener_cliente(perfil)
    contexto = obtener_contexto_negocio(perfil)

    subsector = str(cliente.get("subsector", "")).strip().lower()
    descripcion = str(contexto.get("descripcion_breve_negocio", "")).strip().lower()
    texto_total = f"{subsector} {descripcion}"

    if sector_base == "servicios":
        if "funeraria" in texto_total or "funebre" in texto_total:
            return "funeraria"
        if "hospital" in texto_total or "clinica" in texto_total or "salud" in texto_total:
            return "hospital"
        if "consult" in texto_total:
            return "consultoria"
        if "legal" in texto_total and "propiedad intelectual" in texto_total:
            return "firma_legal_propiedad_intelectual"

    if sector_base == "comercial":
        if "retail" in texto_total:
            return "retail"
        if "distrib" in texto_total:
            return "distribuidora"

    if sector_base == "industrial":
        if "manufactura" in texto_total or "produccion" in texto_total:
            return "manufactura"

    return "default"


def construir_tags_negocio(perfil: Dict[str, Any]) -> List[str]:
    industria = obtener_industria_inteligente(perfil)
    contexto = obtener_contexto_negocio(perfil)
    operacion = obtener_operacion(perfil)
    tesoreria = obtener_tesoreria(perfil)
    nomina = obtener_nomina(perfil)

    tags: Set[str] = set()

    for tag in industria.get("tags", []):
        tags.add(str(tag).strip().lower())

    if contexto.get("pertenece_a_grupo"):
        tags.add("grupo")

    if contexto.get("tiene_partes_relacionadas"):
        tags.add("partes_relacionadas")

    if contexto.get("tiene_operaciones_extranjero"):
        tags.add("operaciones_extranjero")

    if operacion.get("tiene_cartera_significativa"):
        tags.add("cartera_significativa")

    if operacion.get("tiene_provision_cartera"):
        tags.add("provision_cartera")

    if operacion.get("tiene_prestamos_socios"):
        tags.add("prestamos_socios")

    if operacion.get("tiene_anticipos_proveedores"):
        tags.add("anticipos_proveedores")

    if operacion.get("maneja_reembolsos_gastos"):
        tags.add("reembolsos_gastos")

    if operacion.get("tiene_inventarios_significativos"):
        tags.add("inventarios_significativos")

    if tesoreria.get("usa_efectivo_intensivo"):
        tags.add("efectivo_intensivo")

    if nomina.get("tiene_empleados"):
        tags.add("tiene_empleados")

    return sorted(tags)


# =========================================================
# COMBINACIÃ“N DE REGLAS
# =========================================================

def obtener_reglas_base(sector_base: str, subtipo_negocio: str) -> Dict[str, Any]:
    reglas_sector = BASE_INDUSTRIAS.get(sector_base, {})
    reglas_default = reglas_sector.get("default", {})
    reglas_subtipo = reglas_sector.get(subtipo_negocio, {}) if subtipo_negocio in reglas_sector else {}

    def merge_listas(clave: str) -> List[str]:
        base = reglas_default.get(clave, [])
        extra = reglas_subtipo.get(clave, [])
        return list(dict.fromkeys(base + extra))

    return {
        "areas_prioritarias": merge_listas("areas_prioritarias"),
        "areas_secundarias": merge_listas("areas_secundarias"),
        "riesgos_esperados": merge_listas("riesgos_esperados"),
        "observaciones": merge_listas("observaciones"),
        "alertas_profesionales": merge_listas("alertas_profesionales"),
        "supuestos_a_validar": merge_listas("supuestos_a_validar"),
    }


def construir_contexto_industrial(perfil: Dict[str, Any]) -> Dict[str, Any]:
    sector_base = detectar_sector_base(perfil)
    subtipo_negocio = detectar_subtipo_negocio(perfil, sector_base)
    tags = construir_tags_negocio(perfil)

    reglas = obtener_reglas_base(sector_base, subtipo_negocio)

    # Ajustes finos por tags
    areas_prioritarias = list(reglas["areas_prioritarias"])
    areas_secundarias = list(reglas["areas_secundarias"])
    riesgos_esperados = list(reglas["riesgos_esperados"])
    observaciones = list(reglas["observaciones"])
    alertas_profesionales = list(reglas["alertas_profesionales"])
    supuestos_a_validar = list(reglas["supuestos_a_validar"])

    if "prestamos_socios" in tags and "130.2" not in areas_prioritarias:
        areas_prioritarias.append("130.2")

    if "reembolsos_gastos" in tags and "1600" not in areas_prioritarias:
        areas_prioritarias.append("1600")

    if "operaciones_extranjero" in tags:
        riesgos_esperados.append("Operaciones del exterior y su correcta presentaciÃ³n o soporte")
        alertas_profesionales.append("Revisar si existen efectos contables, tributarios o documentales derivados de operaciones internacionales.")

    if "tiene_empleados" in tags:
        riesgos_esperados.append("Gastos de personal y obligaciones laborales")
        if "1600" not in areas_secundarias and "1600" not in areas_prioritarias:
            areas_secundarias.append("1600")

    if "partes_relacionadas" in tags:
        riesgos_esperados.append("Operaciones con partes relacionadas")
        if "425.2" not in areas_secundarias and "425.2" not in areas_prioritarias:
            areas_secundarias.append("425.2")

    # Limpieza de duplicados
    areas_prioritarias = list(dict.fromkeys(areas_prioritarias))
    areas_secundarias = list(dict.fromkeys(areas_secundarias))
    riesgos_esperados = list(dict.fromkeys(riesgos_esperados))
    observaciones = list(dict.fromkeys(observaciones))
    alertas_profesionales = list(dict.fromkeys(alertas_profesionales))
    supuestos_a_validar = list(dict.fromkeys(supuestos_a_validar))

    return {
        "sector_base": sector_base,
        "subtipo_negocio": subtipo_negocio,
        "tags": tags,
        "areas_prioritarias": areas_prioritarias,
        "areas_secundarias": areas_secundarias,
        "riesgos_esperados": riesgos_esperados,
        "observaciones": observaciones,
        "alertas_profesionales": alertas_profesionales,
        "supuestos_a_validar": supuestos_a_validar,
    }


# =========================================================
# IMPRESIÃ“N
# =========================================================

def imprimir_contexto_industrial(nombre_cliente: str) -> None:
    perfil = cargar_perfil(nombre_cliente)
    contexto = construir_contexto_industrial(perfil)

    print("\n====================================================")
    print("MOTOR DE INDUSTRIA")
    print("====================================================\n")

    print(f"Cliente: {obtener_nombre_cliente(perfil)}")
    print(f"Periodo: {obtener_periodo(perfil)}")
    print(f"Marco referencial: {obtener_marco_referencial(perfil)}")
    print(f"Sector base detectado: {contexto['sector_base']}")
    print(f"Subtipo de negocio detectado: {contexto['subtipo_negocio']}")
    print(f"Tags del negocio: {', '.join(contexto['tags']) if contexto['tags'] else 'N/A'}\n")

    print("Ãreas prioritarias por naturaleza del negocio:")
    for area in contexto["areas_prioritarias"]:
        print(f"- {area}")

    print("\nÃreas secundarias:")
    for area in contexto["areas_secundarias"]:
        print(f"- {area}")

    print("\nRiesgos esperados:")
    for riesgo in contexto["riesgos_esperados"]:
        print(f"- {riesgo}")

    print("\nObservaciones contextuales:")
    for obs in contexto["observaciones"]:
        print(f"- {obs}")

    print("\nAlertas profesionales:")
    for alerta in contexto["alertas_profesionales"]:
        print(f"- {alerta}")

    print("\nSupuestos a validar:")
    for s in contexto["supuestos_a_validar"]:
        print(f"- {s}")

    print()


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise ValueError(
                "Debes indicar el nombre de la carpeta del cliente. "
                "Ejemplo: python motor/motor_industria.py bf_ip_2025"
            )

        cliente = sys.argv[1]
        imprimir_contexto_industrial(cliente)

    except Exception as e:
        print(f"\nError en motor de industria: {e}")
