from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime

import yaml


def _normalizar_codigo_area(codigo_ls: str) -> str:
    return str(codigo_ls).strip()


def ruta_estado_area(nombre_cliente: str, codigo_ls: str) -> Path:
    """
    Devuelve la ruta estándar del YAML de estado por cliente-área
    dentro de la nueva arquitectura del proyecto.

    Estructura esperada:
    data/clientes/{cliente}/areas/{codigo}.yaml
    """
    codigo = _normalizar_codigo_area(codigo_ls)
    return Path("data") / "clientes" / nombre_cliente / "areas" / f"{codigo}.yaml"


def estructura_area_vacia(codigo_ls: str) -> dict[str, Any]:
    """
    Devuelve una estructura vacía estándar para un área
    cuando el YAML aún no existe.
    """
    return {
        "codigo": _normalizar_codigo_area(codigo_ls),
        "nombre": "",
        "estado_area": "",
        "riesgo": "",
        "procedimientos": [],
        "hallazgos_abiertos": [],
        "notas": [],
        "pendientes": [],
        "conclusion_preliminar": None,
        "decision_cierre": "",
        "fecha_actualizacion": None,
        "_fuente_yaml": None,
    }


def cargar_estado_area(nombre_cliente: str, codigo_ls: str) -> dict[str, Any]:
    """
    Carga el estado del área desde YAML.
    Si no existe, devuelve una estructura vacía estándar.
    """
    ruta = ruta_estado_area(nombre_cliente, codigo_ls)

    if not ruta.exists():
        return estructura_area_vacia(codigo_ls)

    with open(ruta, "r", encoding="utf-8") as archivo:
        data = yaml.safe_load(archivo) or {}

    if not isinstance(data, dict):
        raise ValueError(f"El YAML de estado de área no es válido: {ruta}")

    data.setdefault("codigo", _normalizar_codigo_area(codigo_ls))
    data.setdefault("nombre", "")
    data.setdefault("estado_area", "")
    data.setdefault("riesgo", "")
    data.setdefault("procedimientos", [])
    data.setdefault("hallazgos_abiertos", [])
    data.setdefault("notas", [])
    data.setdefault("pendientes", [])
    data.setdefault("conclusion_preliminar", None)
    data.setdefault("decision_cierre", "")
    data.setdefault("fecha_actualizacion", None)
    data["_fuente_yaml"] = str(ruta)

    return data


def guardar_estado_area(nombre_cliente: str, codigo_ls: str, estado_area: dict[str, Any]) -> Path:
    """
    Guarda el estado del área en su YAML correspondiente.

    Returns:
        Ruta del archivo guardado.
    """
    ruta = ruta_estado_area(nombre_cliente, codigo_ls)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    data = dict(estado_area)
    data["codigo"] = _normalizar_codigo_area(codigo_ls)
    data["fecha_actualizacion"] = datetime.now().isoformat(timespec="seconds")
    data.pop("_fuente_yaml", None)

    try:
        with open(ruta, "w", encoding="utf-8") as archivo:
            yaml.safe_dump(data, archivo, allow_unicode=True, sort_keys=False)
    except OSError:
        # Streamlit Cloud has read-only filesystem
        # Writes are silently ignored in production
        pass

    return ruta


def extraer_hallazgos_abiertos(estado_area: dict[str, Any]) -> list[str]:
    """
    Extrae una lista limpia de descripciones de hallazgos abiertos
    desde el estado del área.

    Acepta:
    - strings
    - dicts con campos como descripcion y estado
    """
    hallazgos = estado_area.get("hallazgos_abiertos", []) or []
    salida: list[str] = []

    for hallazgo in hallazgos:
        if isinstance(hallazgo, str):
            descripcion = hallazgo.strip()
            if descripcion:
                salida.append(descripcion)
            continue

        if isinstance(hallazgo, dict):
            estado = str(hallazgo.get("estado", "")).strip().lower()
            if estado in {"abierto", "pendiente", "en_proceso", ""}:
                descripcion = str(hallazgo.get("descripcion", "")).strip()
                if descripcion:
                    salida.append(descripcion)

    return [x for x in salida if x]


def obtener_procedimientos_area(estado_area: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Devuelve los procedimientos del área en formato lista.
    """
    procedimientos = estado_area.get("procedimientos", [])
    return procedimientos if isinstance(procedimientos, list) else []


def obtener_estado_area(estado_area: dict[str, Any]) -> str:
    """
    Devuelve el estado general del área.
    """
    return str(estado_area.get("estado_area", "")).strip()


def obtener_notas_area(estado_area: dict[str, Any]) -> list[str]:
    """
    Devuelve las notas del área.
    """
    notas = estado_area.get("notas", [])
    if not isinstance(notas, list):
        return []
    return [str(n).strip() for n in notas if str(n).strip()]


def obtener_pendientes_area(estado_area: dict[str, Any]) -> list[str]:
    """
    Devuelve los pendientes del área.
    """
    pendientes = estado_area.get("pendientes", [])
    if not isinstance(pendientes, list):
        return []
    return [str(p).strip() for p in pendientes if str(p).strip()]
