from __future__ import annotations

from typing import Any

from domain.services.area_briefing import construir_foco_auditoria, construir_resumen_area
from domain.context.contexto_auditoria import construir_contexto_auditoria
from domain.services.leer_perfil import cargar_perfil, ruta_tb_cliente
from analysis.lector_tb import leer_trial_balance
from domain.services.procedimientos_area import procedimientos_por_area, procedimientos_por_area_estructurados
from domain.services.cobertura_aseveraciones import evaluar_cobertura_aseveraciones
from domain.catalogos_python.aseveraciones_ls import ASEVERACIONES_LS
from domain.services.estado_area_yaml import cargar_estado_area, extraer_hallazgos_abiertos
from domain.services.riesgos_area import detectar_riesgos_area, obtener_area
from analysis.variaciones import calcular_variaciones, marcar_movimientos_relevantes


def _afirmaciones_por_area(codigo_ls: str) -> list[str]:
    codigo = str(codigo_ls).strip()
    return ASEVERACIONES_LS.get(codigo, ["existencia", "integridad", "presentacion", "revelacion"])


def _hallazgos_abiertos(perfil: dict[str, Any]) -> list[str]:
    """
    Busca hallazgos abiertos en ubicaciones comunes del perfil YAML.
    """
    candidatos = []
    candidatos.extend(perfil.get("hallazgos_abiertos", []) or [])
    candidatos.extend((perfil.get("notas_generales", {}) or {}).get("hallazgos_abiertos", []) or [])
    candidatos.extend((perfil.get("auditoria", {}) or {}).get("hallazgos_abiertos", []) or [])
    return [str(x).strip() for x in candidatos if str(x).strip()]


def _clasificar_cobertura(
    afirmaciones: list[str],
    riesgos: list[dict[str, Any]],
    focos: list[str],
    procedimientos: list[str],
    contexto: dict[str, Any],
    resumen: dict[str, Any],
) -> tuple[list[str], list[str]]:
    texto_total = " ".join(
        [str(r.get("titulo", "")) + " " + str(r.get("descripcion", "")) for r in riesgos]
        + focos
        + procedimientos
    ).lower()

    cubiertas: list[str] = []
    debiles: list[str] = []

    for a in afirmaciones:
        score = 0
        if a in texto_total:
            score += 2
        if a == "valuacion" and (
            "deterioro" in texto_total
            or "provision" in texto_total
            or bool(contexto.get("senales_cuantitativas", {}).get("material"))
        ):
            score += 1
        if a == "corte" and ("corte" in texto_total or "periodo" in texto_total):
            score += 1
        if a == "presentacion" and ("revelacion" in texto_total or "presentacion" in texto_total):
            score += 1
        if a in {"existencia", "integridad"} and resumen.get("cuentas_relevantes", 0) > 0:
            score += 1

        if score >= 2:
            cubiertas.append(a)
        else:
            debiles.append(a)

    return cubiertas, debiles


def _conclusion_sugerida(
    debiles: list[str],
    pendientes: list[str],
    nivel_riesgo: str,
    hallazgos_abiertos: list[str],
) -> str:
    if not debiles and not pendientes and not hallazgos_abiertos:
        return "El area puede concluirse en esta etapa, sujeto a documentacion final del juicio profesional."

    if nivel_riesgo == "alto" or len(debiles) >= 2 or len(hallazgos_abiertos) > 0:
        return (
            "El area no deberia concluirse todavia. Se recomienda cerrar pendientes criticos, "
            "fortalecer afirmaciones debiles y resolver hallazgos abiertos."
        )

    return (
        "El area podria concluirse con reservas, siempre que se cierre la evidencia pendiente "
        "en afirmaciones debiles antes del cierre definitivo."
    )


def revisar_cierre_area_llm(
    nombre_cliente: str,
    codigo_ls: str,
    etapa: str = "cierre",
) -> str:
    contexto = construir_contexto_auditoria(nombre_cliente, codigo_ls, etapa)
    perfil = cargar_perfil(nombre_cliente)
    estado_area_yaml = cargar_estado_area(nombre_cliente, str(codigo_ls))

    df_tb = leer_trial_balance(ruta_tb_cliente(nombre_cliente))
    df_var = marcar_movimientos_relevantes(calcular_variaciones(df_tb))
    area_df = obtener_area(df_var, str(codigo_ls))

    if area_df.empty:
        return (
            f"REVISION DE CIERRE - L/S {codigo_ls}\n\n"
            "LECTURA GENERAL\n"
            "No hay informacion cuantitativa para el area seleccionada. No es posible concluir el cierre."
        )

    resumen = construir_resumen_area(area_df)
    riesgos = detectar_riesgos_area(area_df, str(codigo_ls), perfil)
    focos = construir_foco_auditoria(str(codigo_ls), perfil, area_df)
    procedimientos = procedimientos_por_area(str(codigo_ls), perfil, riesgos)
    procedimientos_struct_yaml = estado_area_yaml.get("procedimientos", []) or []
    if procedimientos_struct_yaml:
        procedimientos_struct = [
            {
                "id": str(p.get("id", "")).strip(),
                "descripcion": str(p.get("descripcion", "")).strip(),
                "estado": str(p.get("estado", "planificado")).strip().lower(),
            }
            for p in procedimientos_struct_yaml
            if isinstance(p, dict) and str(p.get("id", "")).strip()
        ]
    else:
        # Fallback conservador cuando no existe YAML: todo queda planificado.
        procedimientos_struct = procedimientos_por_area_estructurados(
            str(codigo_ls), perfil, riesgos, estado_default="planificado"
        )

    hallazgos_yaml = extraer_hallazgos_abiertos(estado_area_yaml)
    hallazgos = hallazgos_yaml or _hallazgos_abiertos(perfil)
    cobertura = evaluar_cobertura_aseveraciones(
        codigo_ls=str(codigo_ls),
        procedimientos=procedimientos_struct,
        hallazgos_abiertos=hallazgos,
    )
    afirmaciones = cobertura.get("esperadas", _afirmaciones_por_area(str(codigo_ls)))
    cubiertas = cobertura.get("cubiertas", [])
    debiles = cobertura.get("debiles", [])
    no_cubiertas = cobertura.get("no_cubiertas", [])

    senales = contexto.get("senales_cuantitativas", {})
    nivel_riesgo = str(senales.get("nivel_riesgo", "medio"))
    variacion = float(resumen.get("variacion_acumulada", 0.0) or 0.0)
    material = bool(senales.get("material", False))

    pendientes: list[str] = []
    if debiles:
        pendientes.append(f"Cubrir pruebas adicionales para: {', '.join(debiles[:3])}.")
    if int(resumen.get("cuentas_sin_base", 0) or 0) > 0:
        pendientes.append(
            f"Revisar soporte de {int(resumen.get('cuentas_sin_base', 0) or 0)} cuentas sin base comparativa."
        )
    if any(str(r.get("nivel", "")).upper() == "ALTO" for r in riesgos):
        pendientes.append("Documentar respuesta puntual a riesgos de nivel ALTO.")
    if len(procedimientos) > 0:
        pendientes.append("Verificar ejecucion/evidencia de procedimientos clave del area.")

    if hallazgos:
        pendientes.append(f"Resolver {len(hallazgos)} hallazgo(s) abierto(s) reportado(s) en perfil.")

    if no_cubiertas:
        pendientes.append(f"Cubrir aseveraciones no cubiertas: {', '.join(no_cubiertas[:3])}.")
    if not estado_area_yaml.get("_fuente_yaml"):
        pendientes.append(
            "No existe YAML de estado real del area; validar estados de procedimientos (planificado/ejecutado/pendiente)."
        )

    pendientes = list(dict.fromkeys(pendientes))[:4]
    conclusion = _conclusion_sugerida(
        debiles=debiles + no_cubiertas,
        pendientes=pendientes,
        nivel_riesgo=nivel_riesgo,
        hallazgos_abiertos=hallazgos,
    )

    nombre_area = contexto.get("area_activa", {}).get("nombre", f"L/S {codigo_ls}")
    lectura = (
        f"El area presenta riesgo {nivel_riesgo}, variacion acumulada de {variacion:,.2f}"
        f"{' y comportamiento material' if material else ' y comportamiento no material'}"
        f". Cobertura de aseveraciones: {cobertura.get('cobertura_porcentaje', 0)}%."
    )

    lineas = []
    lineas.append(f"REVISION DE CIERRE - {nombre_area} (L/S {codigo_ls})")
    lineas.append("")
    lineas.append("LECTURA GENERAL")
    lineas.append(lectura)
    lineas.append("")
    lineas.append("AFIRMACIONES CON MAYOR COBERTURA")
    if cubiertas:
        for a in cubiertas[:3]:
            lineas.append(f"- {a}")
    else:
        lineas.append("- Sin cobertura fuerte identificada.")
    lineas.append("")
    lineas.append("AFIRMACIONES DEBILES O PENDIENTES")
    if debiles or no_cubiertas:
        for a in (debiles + no_cubiertas)[:3]:
            lineas.append(f"- {a}")
    else:
        lineas.append("- No se observan afirmaciones debiles relevantes.")
    lineas.append("")
    lineas.append("PENDIENTES ANTES DE CONCLUIR")
    if pendientes:
        for i, p in enumerate(pendientes, start=1):
            lineas.append(f"{i}. {p}")
    else:
        lineas.append("1. Documentar cierre tecnico y referencia cruzada de evidencia.")
    lineas.append("")
    lineas.append("CONCLUSION SUGERIDA")
    lineas.append(conclusion)

    return "\n".join(lineas)

