"""
Servicio de requerimientos de auditoría por área y aseveración.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_RUTA = Path(__file__).resolve().parents[2] / "data" / "catalogos" / "requerimientos_por_area.yaml"
_CACHE: dict[str, Any] = {}


def _cargar() -> dict[str, Any]:
    if _CACHE:
        return _CACHE
    if not _RUTA.exists():
        return {}
    with open(_RUTA, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    _CACHE.update(data)
    return _CACHE


def obtener_requerimientos_area(
    codigo_ls: str,
) -> dict[str, Any]:
    """Returns requirements for a given L/S area."""
    data = _cargar()
    areas = data.get("areas", {})
    return areas.get(str(codigo_ls).strip(), {})


def obtener_todas_las_areas() -> list[str]:
    """Returns list of L/S codes with requirements."""
    data = _cargar()
    return list(data.get("areas", {}).keys())


def construir_checklist(
    codigo_ls: str,
    aseveraciones: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Builds a flat checklist for a given area.
    Each item has: aseveracion, tipo, descripcion, checked=False.
    """
    area = obtener_requerimientos_area(codigo_ls)
    if not area:
        return []

    asev_data = area.get("aseveraciones", {})
    checklist: list[dict[str, Any]] = []

    for asev, contenido in asev_data.items():
        # Filter by requested aseveraciones if provided
        if aseveraciones and asev.lower() not in [a.lower() for a in aseveraciones]:
            continue

        if not isinstance(contenido, dict):
            continue

        for doc in contenido.get("documentos", []):
            checklist.append(
                {
                    "aseveracion": asev,
                    "tipo": "documento",
                    "descripcion": str(doc),
                    "checked": False,
                }
            )

        for preg in contenido.get("preguntas", []):
            checklist.append(
                {
                    "aseveracion": asev,
                    "tipo": "pregunta",
                    "descripcion": str(preg),
                    "checked": False,
                }
            )

        for proc in contenido.get("procedimientos", []):
            checklist.append(
                {
                    "aseveracion": asev,
                    "tipo": "procedimiento",
                    "descripcion": str(proc),
                    "checked": False,
                }
            )

    return checklist
