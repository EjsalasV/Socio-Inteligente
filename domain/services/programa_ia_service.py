"""
Servicio para generar programas de auditoría con IA.
Combina contexto del cliente, riesgos del área y base normativa
para que DeepSeek genere un programa de trabajo accionable.
"""

from __future__ import annotations

from typing import Any

from domain.services.leer_perfil import leer_perfil
from domain.catalogos_python.estructura_ls import obtener_nombre_area_ls
from llm.llm_client import llamar_llm_seguro


def _construir_prompt_programa(
    nombre_cliente: str,
    codigo_ls: str,
    etapa: str,
    perfil: dict[str, Any],
    riesgos: list[dict[str, Any]],
    aseveraciones: list[str],
    materialidad: float,
    contexto_normativo: str,
) -> str:
    nombre_area = obtener_nombre_area_ls(codigo_ls)
    nombre_legal = perfil.get("cliente", {}).get("nombre_legal", nombre_cliente)
    sector = perfil.get("cliente", {}).get("sector", "N/A")
    marco = perfil.get("encargo", {}).get("marco_referencial", "NIIF_PYMES")
    periodo = perfil.get("encargo", {}).get("anio_activo", "N/A")

    riesgos_txt = (
        "\n".join(
            [
                f"- [{r.get('nivel','').upper()}] {r.get('titulo','')}: {r.get('descripcion','')}"
                for r in riesgos[:5]
            ]
        )
        if riesgos
        else "- Sin riesgos automáticos detectados."
    )

    asev_txt = ", ".join(aseveraciones) if aseveraciones else "Existencia, Integridad, Valuación"

    partes_relacionadas = perfil.get("contexto_negocio", {}).get("tiene_partes_relacionadas", False)
    es_holding = "holding" in str(perfil.get("cliente", {}).get("sector", "")).lower()

    contexto_especial = ""
    if partes_relacionadas:
        contexto_especial += "\n- El cliente tiene partes relacionadas identificadas."
    if es_holding:
        contexto_especial += (
            "\n- Es una sociedad holding — revisar VPP y consistencia de inversiones."
        )

    return f"""Eres un socio senior de auditoría financiera especializado en NIAs y NIIF.
Debes generar un programa de auditoría profesional, específico y accionable.

DATOS DEL ENCARGO:
- Cliente: {nombre_legal}
- Sector: {sector}
- Marco: {marco}
- Período: {periodo}
- Área: {nombre_area} (L/S {codigo_ls})
- Etapa: {etapa}
- Materialidad de ejecución: ${materialidad:,.2f}

RIESGOS IDENTIFICADOS:
{riesgos_txt}

AFIRMACIONES MÁS EXPUESTAS:
{asev_txt}

CONTEXTO ESPECIAL:{contexto_especial if contexto_especial else " Ninguno adicional."}

{contexto_normativo}

INSTRUCCIONES:
Genera un programa de auditoría estructurado con las siguientes secciones:

1. **OBJETIVO DEL ÁREA** (1-2 oraciones específicas para este cliente)

2. **PROCEDIMIENTOS OBLIGATORIOS** (mínimo 5, máximo 8)
   Para cada procedimiento incluir:
   - ID (ej: P-01)
   - Descripción específica y accionable
   - Afirmación que cubre
   - Tipo: sustantivo_detalle | analitico | confirmacion | recalculo | inspeccion
   - Referencia normativa si aplica

3. **PROCEDIMIENTOS ADICIONALES POR RIESGO** (1 por cada riesgo ALTO/MEDIO identificado)
   Vinculados directamente a los riesgos del cliente.

4. **ALERTAS DE CALIDAD** (2-3 puntos)
   Qué observaría el revisor de calidad si estos procedimientos no se ejecutan bien.

5. **CRITERIO DEL SOCIO**
   Una conclusión de 3-4 oraciones sobre cómo abordar esta área.

Responde en español. Usa formato Markdown con negrillas y listas.
Sé específico para este cliente — no generes respuestas genéricas."""


def generar_programa_auditoria_ia(
    nombre_cliente: str,
    codigo_ls: str,
    etapa: str = "planificacion",
) -> str:
    """
    Genera un programa de auditoría completo usando IA.

    Args:
        nombre_cliente: Nombre de la carpeta del cliente.
        codigo_ls: Código L/S del área.
        etapa: planificacion | ejecucion | cierre.

    Returns:
        Programa de auditoría en formato Markdown.
    """
    try:
        perfil = leer_perfil(nombre_cliente) or {}

        # Obtener riesgos del área
        riesgos: list[dict[str, Any]] = []
        aseveraciones: list[str] = []
        materialidad = 0.0

        try:
            from analysis.lector_tb import leer_tb
            from analysis.variaciones import calcular_variaciones, marcar_movimientos_relevantes
            from domain.services.riesgos_area import detectar_riesgos_area, obtener_area

            df_tb = leer_tb(nombre_cliente)
            if df_tb is not None and not df_tb.empty:
                df_var = marcar_movimientos_relevantes(calcular_variaciones(nombre_cliente))
                if df_var is not None and not df_var.empty:
                    area_df = obtener_area(df_var, str(codigo_ls))
                    if not area_df.empty:
                        riesgos = detectar_riesgos_area(area_df, str(codigo_ls), perfil)
        except Exception:
            pass

        # Obtener aseveraciones
        try:
            from domain.catalogos_python.aseveraciones_ls import ASEVERACIONES_LS

            aseveraciones = ASEVERACIONES_LS.get(str(codigo_ls), [])
        except Exception:
            pass

        # Obtener materialidad
        try:
            from domain.services.leer_perfil import obtener_materialidad_ejecucion

            mat = obtener_materialidad_ejecucion(perfil)
            materialidad = float(mat or 0.0)
        except Exception:
            pass

        # Recuperar contexto normativo RAG
        contexto_normativo = ""
        try:
            from infra.rag.retriever import recuperar_contexto_normativo
            from infra.rag.vector_store import esta_indexado

            if esta_indexado():
                nombre_area = obtener_nombre_area_ls(str(codigo_ls))
                consulta_rag = (
                    f"procedimientos auditoria {nombre_area} {codigo_ls} afirmaciones riesgos"
                )
                contexto_normativo = recuperar_contexto_normativo(consulta_rag, n_resultados=3)
        except Exception:
            pass

        prompt = _construir_prompt_programa(
            nombre_cliente=nombre_cliente,
            codigo_ls=str(codigo_ls),
            etapa=etapa,
            perfil=perfil,
            riesgos=riesgos,
            aseveraciones=aseveraciones,
            materialidad=materialidad,
            contexto_normativo=contexto_normativo,
        )

        system = (
            "Eres un socio senior de auditoría con 20 años de experiencia en NIAs, "
            "NIIF para PYMES y tributación ecuatoriana. "
            "Generas programas de auditoría profesionales, específicos y accionables. "
            "Siempre conectas riesgo → afirmación → procedimiento → evidencia esperada."
        )

        resultado = llamar_llm_seguro(prompt, system=system)

        if not resultado or resultado == "[Sin respuesta del modelo]":
            return (
                f"## Programa de Auditoría — {obtener_nombre_area_ls(str(codigo_ls))}\n\n"
                "No se pudo generar el programa. Verifica tu DEEPSEEK_API_KEY."
            )

        return resultado

    except Exception as e:
        return f"Error generando programa: {e}"
