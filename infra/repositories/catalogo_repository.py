from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "catalogos"
AREAS_PATH = DATA_ROOT / "areas.yaml"
CORRESPONDENCIA_PATH = DATA_ROOT / "correspondencia.yaml"
ASEVERACIONES_GUIA_LS_PATH = DATA_ROOT / "aseveraciones_guia_ls.yaml"


def _read_yaml(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if data is not None else default
    except Exception:
        return default


def cargar_areas_catalogo() -> list[dict[str, Any]]:
    data = _read_yaml(AREAS_PATH, default={})
    if isinstance(data, list):
        areas = data
    elif isinstance(data, dict):
        areas = data.get("areas", [])
    else:
        areas = []

    if not isinstance(areas, list):
        return []

    salida: list[dict[str, Any]] = []
    for item in areas:
        if not isinstance(item, dict):
            continue
        codigo = str(item.get("codigo", "")).strip()
        if not codigo:
            continue
        salida.append(
            {
                "codigo": codigo,
                "titulo": str(item.get("titulo", "")).strip() or f"Area {codigo}",
                "clase": str(item.get("clase", "")).strip(),
                "categoria_general": str(item.get("categoria_general", "")).strip(),
            }
        )
    return salida


def cargar_correspondencia_catalogo() -> dict[str, dict[str, str]]:
    data = _read_yaml(CORRESPONDENCIA_PATH, default={})
    if not isinstance(data, dict):
        data = {}

    con_inv = data.get("con_inventario", {})
    sin_inv = data.get("sin_inventario", {})
    if not isinstance(con_inv, dict):
        con_inv = {}
    if not isinstance(sin_inv, dict):
        sin_inv = {}

    # fallback seguro minimo
    if not con_inv:
        con_inv = {"Activo corriente": "1.1.2.10.100"}
    if not sin_inv:
        sin_inv = {"Activo corriente": "1.1.2.80"}

    return {"con_inventario": con_inv, "sin_inventario": sin_inv}


def obtener_area_por_codigo(codigo_ls: str) -> dict[str, Any] | None:
    codigo = str(codigo_ls).strip()
    if not codigo:
        return None
    for area in cargar_areas_catalogo():
        if str(area.get("codigo", "")).strip() == codigo:
            return area
    return None


def obtener_modo_correspondencia(perfil: dict[str, Any] | None = None) -> str:
    """
    Determina modo de correspondencia:
    - con_inventario
    - sin_inventario
    Si no se puede determinar, default seguro: con_inventario.
    """
    perfil = perfil or {}
    if not isinstance(perfil, dict):
        return "con_inventario"

    posibles = []
    oper = perfil.get("operacion", {})
    contexto = perfil.get("contexto_negocio", {})
    posibles.extend(
        [
            oper.get("maneja_inventarios"),
            oper.get("tiene_inventarios"),
            contexto.get("maneja_inventarios"),
            contexto.get("tiene_inventarios"),
            perfil.get("maneja_inventarios"),
            perfil.get("tiene_inventarios"),
        ]
    )

    for val in posibles:
        txt = str(val).strip().lower()
        if txt in {"true", "1", "si", "yes"}:
            return "con_inventario"
        if txt in {"false", "0", "no"}:
            return "sin_inventario"

    return "con_inventario"


def cargar_aseveraciones_guia_ls() -> dict[str, dict[str, Any]]:
    data = _read_yaml(ASEVERACIONES_GUIA_LS_PATH, default={})
    if not isinstance(data, dict):
        return {}

    salida: dict[str, dict[str, Any]] = {}
    for codigo, payload in data.items():
        code = str(codigo).strip()
        if not code or not isinstance(payload, dict):
            continue
        asev = payload.get("aseveraciones_sugeridas", [])
        if not isinstance(asev, list):
            asev = []
        salida[code] = {
            "titulo_ls": str(payload.get("titulo_ls", "")).strip(),
            "aseveraciones_sugeridas": [str(x).strip() for x in asev if str(x).strip()],
            "nota": str(payload.get("nota", "")).strip() or "Guia referencial, no exhaustiva.",
        }
    return salida


def obtener_aseveraciones_sugeridas_por_ls(codigo_ls: str) -> dict[str, Any] | None:
    code = str(codigo_ls).strip()
    if not code:
        return None
    data = cargar_aseveraciones_guia_ls()
    return data.get(code)
