"""
Search service for global search across Biblioteca, Hallazgos, Areas, Reportes, Procedimientos.
Uses PostgreSQL text search for efficient querying.
"""
from __future__ import annotations

import logging
from typing import Any

from backend.repositories.file_repository import repo

LOGGER = logging.getLogger("socio_ai.search")


def search(
    query: str,
    cliente_id: str | None = None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Global search across all resources.

    Args:
        query: Search query string
        cliente_id: Optional cliente_id to filter results
        filters: Optional filters dict with keys like:
            - tipo: "hallazgo", "area", "reporte", "norma", "procedimiento"
            - severidad: "critico", "alto", "medio", "bajo"
            - estado: "abierto", "cerrado"

    Returns:
        {
            "results": [
                {
                    "type": "hallazgo" | "area" | "reporte" | "norma" | "procedimiento",
                    "title": str,
                    "id": str,
                    "excerpt": str,
                    "href": str,
                    "metadata": {...}
                },
                ...
            ],
            "total": int
        }
    """
    if not query or not query.strip():
        return {"results": [], "total": 0}

    filters = filters or {}
    results = []
    query_lower = query.lower().strip()

    # Search in each resource type
    results.extend(_search_normas(query_lower, filters))
    if cliente_id:
        results.extend(_search_hallazgos(query_lower, cliente_id, filters))
        results.extend(_search_areas(query_lower, cliente_id, filters))
        results.extend(_search_reportes(query_lower, cliente_id, filters))
        results.extend(_search_procedimientos(query_lower, filters))
    else:
        results.extend(_search_procedimientos(query_lower, filters))

    return {
        "results": results,
        "total": len(results),
    }


def search_suggestions(
    query: str,
    cliente_id: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """
    Return autocomplete suggestions for search input.

    Returns:
        {
            "suggestions": [
                {
                    "text": str,
                    "type": "hallazgo" | "area" | "reporte" | "norma" | "procedimiento",
                    "id": str
                },
                ...
            ]
        }
    """
    if not query or len(query) < 2:
        return {"suggestions": []}

    query_lower = query.lower().strip()
    suggestions = []

    # Get suggestions from normas (always available)
    suggestions.extend(_suggest_normas(query_lower, limit=limit))

    if cliente_id:
        suggestions.extend(_suggest_hallazgos(query_lower, cliente_id, limit=limit))
        suggestions.extend(_suggest_areas(query_lower, cliente_id, limit=limit))
        suggestions.extend(_suggest_procedimientos(query_lower, limit=limit))

    # Deduplicate and limit
    seen = set()
    unique_suggestions = []
    for sug in suggestions:
        key = (sug["type"], sug["id"])
        if key not in seen:
            seen.add(key)
            unique_suggestions.append(sug)
        if len(unique_suggestions) >= limit:
            break

    return {"suggestions": unique_suggestions[:limit]}


# ============================================================================
# NORMAS (Biblioteca)
# ============================================================================

def _search_normas(query: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
    """Search in biblioteca (normas)."""
    results = []

    # Read biblioteca index
    try:
        biblioteca = repo.read_biblioteca()
        if not isinstance(biblioteca, dict):
            return results

        normas = biblioteca.get("normas", [])
        if not isinstance(normas, list):
            return results

        tipo_filter = filters.get("tipo", "").lower()
        if tipo_filter and tipo_filter != "norma":
            return results

        for norma in normas:
            if not isinstance(norma, dict):
                continue

            codigo = str(norma.get("codigo", "")).lower()
            titulo = str(norma.get("titulo", "")).lower()
            fuente = str(norma.get("fuente", "")).lower()
            tags = [str(t).lower() for t in (norma.get("tags") or [])]

            # Match query
            if (query in codigo or query in titulo or query in fuente or
                any(query in tag for tag in tags)):

                excerpt = titulo if titulo else codigo
                results.append({
                    "type": "norma",
                    "title": norma.get("titulo", norma.get("codigo", "N/A")),
                    "id": str(norma.get("codigo", "")),
                    "excerpt": excerpt[:150],
                    "href": f"/biblioteca?search={norma.get('codigo', '')}",
                    "metadata": {
                        "fuente": norma.get("fuente"),
                        "tags": norma.get("tags", []),
                    }
                })
    except Exception as e:
        LOGGER.warning("Error searching normas: %s", e)

    return results


def _suggest_normas(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Autocomplete suggestions for normas."""
    suggestions = []

    try:
        biblioteca = repo.read_biblioteca()
        if not isinstance(biblioteca, dict):
            return suggestions

        normas = biblioteca.get("normas", [])
        if not isinstance(normas, list):
            return suggestions

        for norma in normas:
            if not isinstance(norma, dict):
                continue

            codigo = str(norma.get("codigo", "")).lower()
            titulo = str(norma.get("titulo", "")).lower()

            if query in codigo or query in titulo:
                suggestions.append({
                    "text": norma.get("titulo", norma.get("codigo", "N/A")),
                    "type": "norma",
                    "id": str(norma.get("codigo", ""))
                })

        return suggestions[:limit]
    except Exception as e:
        LOGGER.warning("Error getting normas suggestions: %s", e)
        return suggestions


# ============================================================================
# HALLAZGOS
# ============================================================================

def _search_hallazgos(query: str, cliente_id: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
    """Search in hallazgos."""
    results = []

    try:
        tipo_filter = filters.get("tipo", "").lower()
        if tipo_filter and tipo_filter != "hallazgo":
            return results

        severidad_filter = filters.get("severidad", "").lower()

        hallazgos_doc = repo.read_hallazgos(cliente_id)
        if not hallazgos_doc:
            return results

        # Parse markdown hallazgos
        lines = hallazgos_doc.split("\n")
        current_hallazgo = None

        for line in lines:
            if line.startswith("## Hallazgo"):
                if current_hallazgo and query in current_hallazgo.get("text", "").lower():
                    result = _format_hallazgo_result(current_hallazgo, severidad_filter)
                    if result:
                        results.append(result)

                # Start new hallazgo
                parts = line.replace("## Hallazgo", "").strip().split(" - ", 1)
                current_hallazgo = {
                    "area_codigo": parts[0].strip() if parts else "",
                    "area_nombre": parts[1].strip() if len(parts) > 1 else "",
                    "text": "",
                }
            elif current_hallazgo is not None:
                current_hallazgo["text"] += line + " "

        # Check last hallazgo
        if current_hallazgo and query in current_hallazgo.get("text", "").lower():
            result = _format_hallazgo_result(current_hallazgo, severidad_filter)
            if result:
                results.append(result)

    except Exception as e:
        LOGGER.warning("Error searching hallazgos for cliente_id=%s: %s", cliente_id, e)

    return results


def _format_hallazgo_result(hallazgo: dict, severidad_filter: str) -> dict[str, Any] | None:
    """Format hallazgo search result."""
    text = hallazgo.get("text", "").lower()

    # Check severity filter
    if severidad_filter:
        severidad_map = {"critico": "crítico", "alto": "alto", "medio": "medio", "bajo": "bajo"}
        if severidad_filter not in severidad_map:
            return None
        if severidad_map[severidad_filter] not in text:
            return None

    excerpt = text[:150].strip()
    area_codigo = hallazgo.get("area_codigo", "")
    area_nombre = hallazgo.get("area_nombre", "")

    return {
        "type": "hallazgo",
        "title": f"Hallazgo {area_codigo} - {area_nombre}",
        "id": area_codigo,
        "excerpt": excerpt,
        "href": f"/dashboard/{area_codigo}",  # Placeholder
        "metadata": {
            "area_codigo": area_codigo,
            "area_nombre": area_nombre,
        }
    }


def _suggest_hallazgos(query: str, cliente_id: str, limit: int = 5) -> list[dict[str, Any]]:
    """Autocomplete suggestions for hallazgos."""
    suggestions = []

    try:
        hallazgos_doc = repo.read_hallazgos(cliente_id)
        if not hallazgos_doc:
            return suggestions

        lines = hallazgos_doc.split("\n")
        for line in lines:
            if line.startswith("## Hallazgo"):
                parts = line.replace("## Hallazgo", "").strip().split(" - ", 1)
                area_codigo = parts[0].strip() if parts else ""
                area_nombre = parts[1].strip() if len(parts) > 1 else ""

                if query in area_codigo.lower() or query in area_nombre.lower():
                    suggestions.append({
                        "text": f"Hallazgo {area_codigo}",
                        "type": "hallazgo",
                        "id": area_codigo
                    })

        return suggestions[:limit]
    except Exception as e:
        LOGGER.warning("Error getting hallazgos suggestions: %s", e)
        return suggestions


# ============================================================================
# AREAS
# ============================================================================

def _search_areas(query: str, cliente_id: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
    """Search in areas."""
    results = []

    try:
        tipo_filter = filters.get("tipo", "").lower()
        if tipo_filter and tipo_filter != "area":
            return results

        areas = repo.list_areas(cliente_id)
        if not isinstance(areas, list):
            return results

        for area_code in areas:
            try:
                area_data = repo.read_area_yaml(cliente_id, area_code)
                if not isinstance(area_data, dict):
                    continue

                nombre = str(area_data.get("nombre", "")).lower()
                descripcion = str(area_data.get("descripcion", "")).lower()

                if query in nombre or query in descripcion:
                    results.append({
                        "type": "area",
                        "title": area_data.get("nombre", area_code),
                        "id": area_code,
                        "excerpt": descripcion[:150] if descripcion else nombre,
                        "href": f"/areas/{cliente_id}/{area_code}",
                        "metadata": {
                            "codigo": area_code,
                        }
                    })
            except Exception:
                continue

    except Exception as e:
        LOGGER.warning("Error searching areas for cliente_id=%s: %s", cliente_id, e)

    return results


def _suggest_areas(query: str, cliente_id: str, limit: int = 5) -> list[dict[str, Any]]:
    """Autocomplete suggestions for areas."""
    suggestions = []

    try:
        areas = repo.list_areas(cliente_id)
        if not isinstance(areas, list):
            return suggestions

        for area_code in areas:
            try:
                area_data = repo.read_area_yaml(cliente_id, area_code)
                if not isinstance(area_data, dict):
                    continue

                nombre = str(area_data.get("nombre", "")).lower()
                if query in nombre or query in area_code.lower():
                    suggestions.append({
                        "text": area_data.get("nombre", area_code),
                        "type": "area",
                        "id": area_code
                    })
            except Exception:
                continue

        return suggestions[:limit]
    except Exception as e:
        LOGGER.warning("Error getting areas suggestions: %s", e)
        return suggestions


# ============================================================================
# REPORTES
# ============================================================================

def _search_reportes(query: str, cliente_id: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
    """Search in reportes."""
    results = []

    try:
        tipo_filter = filters.get("tipo", "").lower()
        if tipo_filter and tipo_filter != "reporte":
            return results

        estado_filter = filters.get("estado", "").lower()

        # Try to read reportes from file repo
        # This is a placeholder - adapt based on your actual reportes storage
        reportes = repo.read_reportes(cliente_id) or []
        if not isinstance(reportes, list):
            return results

        for reporte in reportes:
            if not isinstance(reporte, dict):
                continue

            nombre = str(reporte.get("nombre", "")).lower()
            descripcion = str(reporte.get("descripcion", "")).lower()
            estado = str(reporte.get("estado", "")).lower()

            # Apply filters
            if estado_filter and estado_filter not in estado:
                continue

            if query in nombre or query in descripcion:
                results.append({
                    "type": "reporte",
                    "title": reporte.get("nombre", "N/A"),
                    "id": str(reporte.get("id", "")),
                    "excerpt": descripcion[:150] if descripcion else nombre,
                    "href": f"/reportes/{cliente_id}",
                    "metadata": {
                        "estado": reporte.get("estado"),
                        "fecha": reporte.get("fecha"),
                    }
                })
    except Exception as e:
        LOGGER.warning("Error searching reportes for cliente_id=%s: %s", cliente_id, e)

    return results


# ============================================================================
# PROCEDIMIENTOS
# ============================================================================

def _search_procedimientos(query: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
    """Search in procedimientos."""
    results = []

    try:
        tipo_filter = filters.get("tipo", "").lower()
        if tipo_filter and tipo_filter != "procedimiento":
            return results

        # Placeholder for procedimientos search
        # Adapt based on your actual procedimientos storage
        procedimientos = repo.read_procedimientos() or []
        if not isinstance(procedimientos, list):
            return results

        for proc in procedimientos:
            if not isinstance(proc, dict):
                continue

            descripcion = str(proc.get("descripcion", "")).lower()
            tipo_proc = str(proc.get("tipo", "")).lower()

            if query in descripcion or query in tipo_proc:
                results.append({
                    "type": "procedimiento",
                    "title": proc.get("descripcion", "N/A")[:50],
                    "id": str(proc.get("id", "")),
                    "excerpt": descripcion[:150],
                    "href": "/procedimientos",
                    "metadata": {
                        "tipo": proc.get("tipo"),
                    }
                })
    except Exception as e:
        LOGGER.warning("Error searching procedimientos: %s", e)

    return results


def _suggest_procedimientos(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Autocomplete suggestions for procedimientos."""
    suggestions = []

    try:
        procedimientos = repo.read_procedimientos() or []
        if not isinstance(procedimientos, list):
            return suggestions

        for proc in procedimientos:
            if not isinstance(proc, dict):
                continue

            descripcion = str(proc.get("descripcion", "")).lower()
            if query in descripcion:
                suggestions.append({
                    "text": proc.get("descripcion", "N/A")[:50],
                    "type": "procedimiento",
                    "id": str(proc.get("id", ""))
                })

        return suggestions[:limit]
    except Exception as e:
        LOGGER.warning("Error getting procedimientos suggestions: %s", e)
        return suggestions
