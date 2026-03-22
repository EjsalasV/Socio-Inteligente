"""
Carga y divide en chunks la base de conocimiento normativo.
Lee todos los archivos .md de data/conocimiento_normativo/
y los prepara para indexación en ChromaDB.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

KNOWLEDGE_ROOT = Path("data") / "conocimiento_normativo"

FUENTE_MAP = {
    "nias": "NIA",
    "niif_pymes": "NIIF PYMES",
    "niif_completas": "NIIF Completas",
    "tributario_ec": "Tributario Ecuador",
    "metodologia": "Metodología SocioAI",
    "supercias": "Supercias Ecuador",
}


def _detectar_fuente(path: Path) -> str:
    for parte in path.parts:
        if parte in FUENTE_MAP:
            return FUENTE_MAP[parte]
    return "Normativa General"


def _chunk_texto(texto: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """
    Divide texto en chunks con overlap para mejor recuperación.
    Respeta saltos de sección (##) cuando es posible.
    """
    secciones = texto.split("\n## ")
    chunks: list[str] = []

    for seccion in secciones:
        if len(seccion) <= chunk_size:
            if seccion.strip():
                chunks.append(seccion.strip())
        else:
            palabras = seccion.split()
            actual: list[str] = []
            tam_actual = 0
            for palabra in palabras:
                actual.append(palabra)
                tam_actual += len(palabra) + 1
                if tam_actual >= chunk_size:
                    chunks.append(" ".join(actual))
                    solapado = actual[-overlap // 6 :] if len(actual) > overlap // 6 else actual
                    actual = solapado.copy()
                    tam_actual = sum(len(p) + 1 for p in actual)
            if actual:
                chunks.append(" ".join(actual))

    return [c for c in chunks if len(c.strip()) > 10]


def cargar_documentos() -> list[dict[str, Any]]:
    """
    Lee todos los archivos .md de la base normativa.

    Returns:
        Lista de dicts con: id, texto, fuente, archivo, titulo
    """
    documentos: list[dict[str, Any]] = []

    if not KNOWLEDGE_ROOT.exists():
        print(f"[RAG] Directorio no encontrado: {KNOWLEDGE_ROOT}")
        return documentos

    archivos = sorted(KNOWLEDGE_ROOT.rglob("*.md"))
    print(f"[RAG] Encontrados {len(archivos)} archivos .md")

    for archivo in archivos:
        try:
            texto = archivo.read_text(encoding="utf-8").strip()
            if not texto:
                continue

            fuente = _detectar_fuente(archivo)
            titulo = archivo.stem.upper().replace("_", " ")

            chunks = _chunk_texto(texto)
            for i, chunk in enumerate(chunks):
                doc_id = f"{archivo.stem}_{i}"
                # Prefix chunk with document title for better retrieval
                texto_enriquecido = f"[{fuente}: {titulo}]\n{chunk}"
                documentos.append(
                    {
                        "id": doc_id,
                        "texto": texto_enriquecido,
                        "fuente": fuente,
                        "archivo": str(archivo),
                        "titulo": titulo,
                        "chunk_idx": i,
                    }
                )

        except Exception as e:
            print(f"[RAG] Error leyendo {archivo}: {e}")

    print(f"[RAG] Total chunks generados: {len(documentos)}")
    return documentos


def listar_archivos_normativa() -> list[dict[str, str]]:
    """Lista todos los archivos disponibles en la base normativa."""
    if not KNOWLEDGE_ROOT.exists():
        return []
    return [
        {
            "archivo": str(p.relative_to(KNOWLEDGE_ROOT)),
            "fuente": _detectar_fuente(p),
            "titulo": p.stem.upper().replace("_", " "),
        }
        for p in sorted(KNOWLEDGE_ROOT.rglob("*.md"))
        if p.stat().st_size > 50
    ]
