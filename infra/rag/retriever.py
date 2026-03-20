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


def recuperar_contexto_normativo(
    consulta: str,
    n_resultados: int = 3,
    fuente_filtro: str | None = None,
) -> str:
    """
    Recupera contexto normativo relevante para una consulta.
    Listo para insertar en el prompt de DeepSeek.

    Args:
        consulta: Pregunta del auditor.
        n_resultados: Chunks a recuperar.
        fuente_filtro: Filtrar por tipo (NIA, Tributario Ecuador, etc.)

    Returns:
        Texto formateado con los fragmentos relevantes.
        Retorna string vacío si no hay resultados.
    """
    if not esta_indexado():
        return ""

    resultados = buscar_normativa(consulta, n_resultados, fuente_filtro)

    if not resultados:
        return ""

    partes = ["CONTEXTO NORMATIVO RELEVANTE:"]
    for i, r in enumerate(resultados, 1):
        partes.append(
            f"\n[{i}] {r['fuente']} — {r['titulo']} "
            f"(relevancia: {r['relevancia']:.2f})\n{r['texto']}"
        )
    partes.append("\n---")

    return "\n".join(partes)
