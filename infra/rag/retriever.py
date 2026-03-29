"""
Retriever principal del sistema RAG de SocioAI.
Orquesta carga, indexación y búsqueda de la base normativa.
"""

from __future__ import annotations

from typing import Any

from infra.rag.knowledge_loader import cargar_documentos
from infra.rag.vector_store import (
    buscar_normativa,
    esta_indexado,
    indexar_documentos,
    total_indexado,
)


def inicializar_rag(forzar: bool = False) -> dict[str, Any]:
    """
    Inicializa el motor RAG: carga documentos e indexa si necesario.

    Args:
        forzar: Si True, re-indexa aunque ya exista contenido.

    Returns:
        dict con estado de la inicialización.
    """
    if not forzar and esta_indexado():
        total = total_indexado()
        print(f"[RAG] Ya inicializado ({total} chunks). Usar forzar=True para re-indexar.")
        return {"estado": "ya_indexado", "total_chunks": total}

    print("[RAG] Iniciando indexacion de base normativa...")
    documentos = cargar_documentos()

    if not documentos:
        return {"estado": "sin_documentos", "total_chunks": 0}

    total = indexar_documentos(documentos)
    return {
        "estado": "indexado",
        "total_chunks": total,
        "documentos_fuente": len(documentos),
    }


# Keyword signals: if query contains these words, boost chunks
# from the matching source
_KEYWORD_BOOST: list[tuple[list[str], str]] = [
    (["nia 240", "fraude", "override", "fraude en ingresos"], "NIA — NIA 240"),
    (["nia 315", "riesgo inherente", "valoracion de riesgo"], "NIA — NIA 315"),
    (
        ["nia 320", "materialidad", "materialidad de ejecucion", "error trivial", "umbral"],
        "NIA — NIA 320",
    ),
    (
        ["nia 330", "prueba de control", "procedimiento sustantivo", "respuesta al riesgo"],
        "NIA — NIA 330",
    ),
    (["nia 500", "evidencia", "suficiencia", "adecuacion"], "NIA — NIA 500"),
    (
        [
            "retencion",
            "retenciones",
            "retencion en la fuente",
            "tarifa retencion",
            "agente de retencion",
        ],
        "Tributario Ecuador — RETENCIONES",
    ),
    (
        ["impuesto diferido", "diferencia temporaria", "nic 12", "seccion 29"],
        "Tributario Ecuador — IMPUESTO DIFERIDO",
    ),
    (
        [
            "conciliacion tributaria",
            "provision cartera",
            "gastos no deducibles",
            "base imponible",
            "anticipo impuesto",
            "participacion trabajadores",
            "lrti art",
            "rlrti art",
        ],
        "Tributario Ecuador — CONCILIACION TRIBUTARIA",
    ),
    (
        [
            "seccion 23",
            "reconocimiento ingreso",
            "ingresos ordinarios",
            "grado de terminacion",
            "prestacion de servicios",
        ],
        "NIIF PYMES — SECCION 23",
    ),
    (
        [
            "seccion 11",
            "instrumento financiero",
            "deterioro cartera",
            "costo amortizado",
            "valor razonable",
        ],
        "NIIF PYMES — SECCION 11",
    ),
    (
        ["materialidad metodologia", "base materialidad", "socioai"],
        "Metodología SocioAI — MATERIALIDAD",
    ),
    (
        [
            "afirmacion",
            "ocurrencia",
            "integridad",
            "valuacion",
            "existencia",
            "derechos y obligaciones",
        ],
        "Metodología SocioAI — ASEVERACIONES",
    ),
    (
        [
            "partes relacionadas",
            "nic 24",
            "relacionadas revelaciones",
            "transacciones relacionadas",
            "arm's length",
        ],
        "NIA — NIA 550",
    ),
    (
        [
            "negocio en marcha",
            "empresa en funcionamiento",
            "continuidad",
            "nia 570",
            "going concern",
        ],
        "NIA — NIA 570",
    ),
    (
        [
            "procedimientos analiticos",
            "nia 520",
            "ratio analitico",
            "variacion esperada",
            "expectativa auditor",
        ],
        "NIA — NIA 520",
    ),
    (
        [
            "estimaciones contables",
            "nia 540",
            "jubilacion patronal",
            "provision actuarial",
            "sesgo gerencia",
        ],
        "NIA — NIA 540",
    ),
    (
        [
            "informe auditor",
            "opinion auditoria",
            "nia 700",
            "opinion no modificada",
            "salvedades",
            "opinion adversa",
        ],
        "NIA — NIA 700",
    ),
    (
        [
            "ppe depreciacion",
            "propiedad planta equipo",
            "seccion 17",
            "vida util",
            "valor residual",
        ],
        "NIIF PYMES — SECCION 17",
    ),
    (
        [
            "deterioro activos",
            "importe recuperable",
            "seccion 27",
            "valor en uso",
            "valor neto realizable activos",
        ],
        "NIIF PYMES — SECCION 27",
    ),
    (
        [
            "impuesto diferido pymes",
            "seccion 29",
            "diferencia temporaria",
            "tasa efectiva",
            "conciliacion tasa",
        ],
        "NIIF PYMES — SECCION 29",
    ),
    (
        [
            "inventarios fifo",
            "costo promedio",
            "seccion 13",
            "valor neto realizable inventario",
            "obsolescencia",
        ],
        "NIIF PYMES — SECCION 13",
    ),
    (
        [
            "supercias",
            "superintendencia compañias",
            "auditoria obligatoria",
            "presentacion estados financieros supercias",
            "30 abril",
        ],
        "Supercias Ecuador — SUPERCIAS GENERAL",
    ),
    (
        [
            "gastos no deducibles",
            "rlrti art 35",
            "multas no deducibles",
            "gastos personales accionista",
            "subcapitalizacion",
        ],
        "Tributario Ecuador — GASTOS NO DEDUCIBLES",
    ),
    (
        [
            "iva",
            "impuesto valor agregado",
            "tarifa iva",
            "credito tributario iva",
            "factor proporcionalidad",
            "tarifa 15",
        ],
        "Tributario Ecuador — IVA",
    ),
    (
        [
            "planificacion auditoria",
            "fases auditoria",
            "escepticismo",
            "programa de trabajo",
            "aceptacion cliente",
        ],
        "Metodología SocioAI — PLANIFICACION",
    ),
    (
        [
            "hallazgo auditoria",
            "condicion criterio causa efecto",
            "carta gerencia",
            "incorrecciones no corregidas",
            "4c",
        ],
        "Metodología SocioAI — HALLAZGOS",
    ),
]


def _boost_score(
    resultado: dict,
    consulta_lower: str,
) -> float:
    """
    Returns a boost value (0.0 to 0.25) if the result's source
    matches keyword signals in the query.
    """
    fuente_titulo = f"{resultado['fuente']} — {resultado['titulo']}"
    for keywords, fuente_target in _KEYWORD_BOOST:
        if any(kw in consulta_lower for kw in keywords):
            if fuente_target.lower() in fuente_titulo.lower():
                return 0.20
    return 0.0


def recuperar_contexto_normativo(
    consulta: str,
    n_resultados: int = 3,
    fuente_filtro: str | None = None,
) -> str:
    """
    Recupera contexto normativo relevante para una consulta.
    Incluye logging estructurado de latencia y fuentes encontradas.
    """
    import time

    if not esta_indexado():
        print("[RAG] Vector store vacío. Ejecuta: python -m app.cli_commands indexar")
        return ""

    t_inicio = time.time()
    resultados = buscar_normativa(consulta, n_resultados, fuente_filtro)
    latencia = round(time.time() - t_inicio, 3)

    if not resultados:
        print(f"[RAG] Sin resultados para: '{consulta[:60]}' ({latencia}s)")
        return ""

    # Re-rank: apply keyword boost and sort by adjusted score
    consulta_lower = consulta.lower()
    for r in resultados:
        boost = _boost_score(r, consulta_lower)
        r["relevancia_ajustada"] = round(r["relevancia"] + boost, 4)

    resultados.sort(key=lambda x: x["relevancia_ajustada"], reverse=True)

    # Update log to show adjusted scores
    relevancia_max = max(r["relevancia_ajustada"] for r in resultados)
    fuentes = [f"{r['fuente']}:{r['titulo']}" for r in resultados]
    print(
        f"[RAG] consulta='{consulta[:50]}' "
        f"chunks={len(resultados)} "
        f"relevancia_max={relevancia_max:.3f} "
        f"latencia={latencia}s "
        f"fuentes={fuentes}"
    )

    partes = ["CONTEXTO NORMATIVO RELEVANTE:"]
    for i, r in enumerate(resultados, 1):
        partes.append(
            f"\n[{i}] {r['fuente']} — {r['titulo']} "
            f"(relevancia: {r.get('relevancia_ajustada', r['relevancia']):.2f})\n{r['texto']}"
        )
    partes.append("\n---")

    return "\n".join(partes)
