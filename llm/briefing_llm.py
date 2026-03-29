from __future__ import annotations

from typing import Any

import pandas as pd

from domain.services.area_briefing import construir_foco_auditoria, obtener_nombre_area_ls
from domain.context.contexto_auditoria import construir_contexto_auditoria
from analysis.lector_tb import leer_tb
from domain.services.riesgos_area import detectar_riesgos_area, obtener_area
from analysis.variaciones import calcular_variaciones, marcar_movimientos_relevantes


def _normalizar_etapa(etapa: str | None) -> str:
    valor = str(etapa or "").strip().lower()
    aliases = {
        "planificacion": "planificacion",
        "planificación": "planificacion",
        "ejecucion": "ejecucion",
        "ejecución": "ejecucion",
        "cierre": "cierre",
    }
    return aliases.get(valor, "planificacion")


def _afirmaciones_por_area(codigo_ls: str) -> list[str]:
    codigo = str(codigo_ls).strip()

    if codigo.startswith("13"):
        return ["Existencia", "Valuacion (deterioro)", "Presentacion y revelacion"]
    if codigo in {"14", "15"}:
        return ["Valuacion", "Existencia", "Revelacion"]
    if codigo.startswith("42") or codigo.startswith("425"):
        return ["Integridad", "Corte", "Presentacion"]
    if codigo.startswith("15"):
        return ["Ocurrencia", "Corte", "Clasificacion"]
    if codigo.startswith("16") or codigo.startswith("17") or codigo.startswith("18"):
        return ["Ocurrencia", "Clasificacion", "Corte"]
    return ["Existencia", "Integridad", "Presentacion y revelacion"]


def _priorizar_focos(
    focos_base: list[str],
    banderas: list[str],
    riesgos_area: list[dict[str, Any]],
    contexto: dict[str, Any],
    etapa: str,
) -> list[str]:
    """
    Selecciona 3 focos priorizados con criterio de riesgo + contexto + etapa.
    """
    candidatos: list[tuple[int, str]] = []

    palabras_riesgo = ("vpp", "partes relacionadas", "valuacion", "revelacion")
    etapa_bonus = {
        "planificacion": ("entendimiento", "medicion", "revelacion"),
        "ejecucion": ("recalcular", "verificar", "conciliar", "soporte"),
        "cierre": ("presentacion", "revelacion", "conclusion"),
    }

    for foco in focos_base:
        score = 1
        f = foco.lower()

        if contexto.get("relevancia_contextual", {}).get("es_prioritaria_negocio"):
            score += 2
        if contexto.get("relevancia_contextual", {}).get("es_prioritaria_industria"):
            score += 2

        if contexto.get("senales_cuantitativas", {}).get("material"):
            score += 2
        if contexto.get("senales_cuantitativas", {}).get("nivel_riesgo") == "alto":
            score += 2

        if any(p in f for p in palabras_riesgo):
            score += 2
        if any(p in f for p in etapa_bonus.get(etapa, ())):
            score += 1

        candidatos.append((score, foco))

    for b in banderas:
        candidatos.append((4, f"Atender bandera clave: {b}."))

    for r in riesgos_area:
        nivel = str(r.get("nivel", "")).upper()
        titulo = str(r.get("titulo", "")).strip()
        if not titulo:
            continue
        base = 3
        if nivel == "ALTO":
            base = 6
        elif nivel == "MEDIO":
            base = 4
        candidatos.append((base, f"Responder riesgo '{titulo}' con procedimiento especifico."))

    ordenados = sorted(candidatos, key=lambda x: x[0], reverse=True)
    salida: list[str] = []
    vistos = set()
    for _, texto in ordenados:
        if texto in vistos:
            continue
        salida.append(texto)
        vistos.add(texto)
        if len(salida) == 3:
            break
    return salida


def _direccion_por_etapa(etapa: str) -> dict[str, str]:
    if etapa == "ejecucion":
        return {
            "por_donde_empezar": (
                "Empieza por las cuentas con mayor variacion y las banderas de riesgo alto; "
                "ejecuta pruebas de detalle y recalculos sobre esas partidas antes del resto del universo."
            ),
            "observacion_calidad": (
                "Calidad puede observar falta de trazabilidad entre riesgo identificado, muestra seleccionada y evidencia."
            ),
        }
    if etapa == "cierre":
        return {
            "por_donde_empezar": (
                "Empieza por validar consistencia final entre resultados de pruebas, ajustes propuestos y revelaciones."
            ),
            "observacion_calidad": (
                "Calidad puede observar conclusiones no soportadas o hallazgos sin impacto claramente evaluado en EEFF."
            ),
        }
    return {
        "por_donde_empezar": (
            "Empieza por entendimiento del modelo del area y define alcance en funcion de materialidad, "
            "riesgo y relevancia contextual."
        ),
        "observacion_calidad": (
            "Calidad puede observar un programa demasiado generico si no conecta riesgo, afirmaciones y procedimientos."
        ),
    }


def generar_briefing_area_llm(
    nombre_cliente: str,
    codigo_ls: str,
    etapa: str = "planificacion",
) -> str:
    """
    Genera briefing de criterio auditor, priorizado y orientado a accion.
    """
    etapa_norm = _normalizar_etapa(etapa)
    contexto = construir_contexto_auditoria(
        nombre_cliente=nombre_cliente,
        codigo_area=codigo_ls,
        etapa=etapa_norm,
    )

    perfil = cargar_perfil(nombre_cliente)
    try:
        df_tb = leer_tb(nombre_cliente)
        if df_tb is None:
            df_tb = pd.DataFrame()
    except Exception:
        df_tb = pd.DataFrame()

    try:
        if df_tb is not None and not df_tb.empty:
            df_var = marcar_movimientos_relevantes(calcular_variaciones(df_tb))
        else:
            df_var = pd.DataFrame()
    except Exception:
        df_var = pd.DataFrame()

    if df_var is not None and not df_var.empty and "ls" in df_var.columns:
        area_df = obtener_area(df_var, str(codigo_ls))
    else:
        area_df = pd.DataFrame()

    focos_base = construir_foco_auditoria(str(codigo_ls), perfil, area_df)
    riesgos_area = (
        detectar_riesgos_area(area_df, str(codigo_ls), perfil) if not area_df.empty else []
    )

    senales = contexto.get("senales_cuantitativas", {})
    banderas = senales.get("banderas", [])
    focos_priorizados = _priorizar_focos(focos_base, banderas, riesgos_area, contexto, etapa_norm)

    afirmaciones = _afirmaciones_por_area(str(codigo_ls))
    direccion = _direccion_por_etapa(etapa_norm)

    cliente = contexto.get("cliente", {})
    area = contexto.get("area_activa", {})
    rel = contexto.get("relevancia_contextual", {})
    auditoria = contexto.get("auditoria", {})

    juicio = (
        f"En {area.get('nombre', obtener_nombre_area_ls(str(codigo_ls)))} (L/S {area.get('codigo', codigo_ls)}), "
        f"el nivel de riesgo observado es {senales.get('nivel_riesgo', 'bajo')} "
        f"(score {senales.get('riesgo_score', 0)}/100), con variacion absoluta de "
        f"{senales.get('variacion_absoluta', 0):,.2f} y variacion porcentual de "
        f"{senales.get('variacion_porcentual', 0):,.2f}%."
    )

    sensibilidad = []
    if rel.get("es_prioritaria_negocio"):
        sensibilidad.append("es foco natural del negocio")
    if rel.get("es_prioritaria_industria"):
        sensibilidad.append("es critica por industria")
    if senales.get("material"):
        sensibilidad.append("la variacion es material")
    else:
        sensibilidad.append(
            "la variacion no supera materialidad, pero puede ser sensible por contexto"
        )

    texto = []
    texto.append(
        f"Cliente: {cliente.get('nombre', nombre_cliente)} | Periodo: {cliente.get('periodo', 'N/A')} | Etapa: {etapa_norm}"
    )
    texto.append("")
    texto.append("Juicio profesional")
    texto.append(juicio)
    texto.append(f"Contexto ponderado: {', '.join(sensibilidad)}.")
    texto.append("")
    texto.append("Top 3 prioridades")
    for i, foco in enumerate(focos_priorizados, start=1):
        texto.append(f"{i}. {foco}")
    texto.append("")
    texto.append("Direccion sugerida")
    texto.append(f"- Por donde empezar: {direccion['por_donde_empezar']}")
    texto.append(f"- Afirmaciones mas expuestas: {', '.join(afirmaciones)}.")
    texto.append(f"- Que podria observar revision de calidad: {direccion['observacion_calidad']}")

    if banderas:
        texto.append("")
        texto.append("Senales relevantes")
        for b in banderas[:5]:
            texto.append(f"- {b}")

    if auditoria.get("materialidad_ejecucion") is not None:
        texto.append("")
        texto.append(
            f"Materialidad de ejecucion de referencia: {float(auditoria.get('materialidad_ejecucion') or 0):,.2f}."
        )

    prompt_final = "\n".join(texto)

    system_auditor = (
        "Eres un socio de auditoría senior especializado en NIAs. "
        "Tu rol es dar criterio profesional claro, accionable y técnico. "
        "Responde en español. Sé directo y conciso."
    )

    from llm.llm_client import llamar_llm_seguro

    criterio_llm = llamar_llm_seguro(prompt_final, system=system_auditor)

    texto.append("")
    texto.append("Criterio del socio (IA)")
    texto.append(criterio_llm)

    return "\n".join(texto)
