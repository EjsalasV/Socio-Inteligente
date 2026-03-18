from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def _codigo(codigo_ls: str) -> str:
    return str(codigo_ls).strip()


def ruta_historial_area(nombre_cliente: str, codigo_ls: str) -> Path:
    codigo = _codigo(codigo_ls)
    return Path("data") / "clientes" / nombre_cliente / "areas" / f"{codigo}_historial.yaml"


def cargar_historial_area(nombre_cliente: str, codigo_ls: str) -> list[dict[str, Any]]:
    ruta = ruta_historial_area(nombre_cliente, codigo_ls)
    if not ruta.exists():
        return []

    with open(ruta, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []

    if not isinstance(data, list):
        return []

    eventos = [x for x in data if isinstance(x, dict)]
    eventos.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return eventos


def _snapshot_significativo(evento: dict[str, Any]) -> dict[str, Any]:
    return {
        "codigo": str(evento.get("codigo", "")).strip(),
        "estado_area": str(evento.get("estado_area", "")).strip(),
        "decision_cierre": str(evento.get("decision_cierre", "")).strip(),
        "conclusion_preliminar": str(evento.get("conclusion_preliminar", "")).strip(),
        "notas_resumen": str(evento.get("notas_resumen", "")).strip(),
        "pendientes_resumen": str(evento.get("pendientes_resumen", "")).strip(),
        "origen": str(evento.get("origen", "manual")).strip() or "manual",
    }


def _resumen_lista(value: Any, max_items: int = 3) -> str:
    if not isinstance(value, list):
        return ""
    vals = [str(x).strip() for x in value if str(x).strip()]
    if not vals:
        return ""
    head = vals[:max_items]
    more = f" (+{len(vals)-max_items})" if len(vals) > max_items else ""
    return " | ".join(head) + more


def _count_lista(value: Any) -> int:
    if not isinstance(value, list):
        return 0
    return len([x for x in value if str(x).strip()])


def agregar_evento_historial_area(
    nombre_cliente: str,
    codigo_ls: str,
    estado_actual: dict[str, Any],
    origen: str = "manual",
) -> dict[str, Any] | None:
    historial = cargar_historial_area(nombre_cliente, codigo_ls)
    prev = historial[0] if historial else None

    evento: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "codigo": _codigo(codigo_ls),
        "estado_area": str(estado_actual.get("estado_area", "")).strip(),
        "decision_cierre": str(estado_actual.get("decision_cierre", "")).strip(),
        "conclusion_preliminar": str(estado_actual.get("conclusion_preliminar", "")).strip(),
        "notas_resumen": _resumen_lista(estado_actual.get("notas", [])),
        "pendientes_resumen": _resumen_lista(estado_actual.get("pendientes", [])),
        "notas_count": _count_lista(estado_actual.get("notas", [])),
        "pendientes_count": _count_lista(estado_actual.get("pendientes", [])),
        "origen": str(origen or "manual").strip(),
    }

    if prev:
        evento["previous_state"] = {
            "estado_area": prev.get("estado_area", ""),
            "decision_cierre": prev.get("decision_cierre", ""),
            "conclusion_preliminar": prev.get("conclusion_preliminar", ""),
        }

    # Evita duplicar eventos idénticos en campos significativos.
    if prev and _snapshot_significativo(prev) == _snapshot_significativo(evento):
        return None

    historial.append(evento)
    ruta = ruta_historial_area(nombre_cliente, codigo_ls)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        yaml.safe_dump(historial, f, allow_unicode=True, sort_keys=False)

    return evento


def resumir_historial_area(historial: list[dict[str, Any]]) -> dict[str, Any]:
    if not historial:
        return {"total_eventos": 0, "ultimo_estado": "", "ultima_decision": ""}

    eventos = sorted(historial, key=lambda x: str(x.get("timestamp", "")), reverse=True)
    ultimo = eventos[0]
    return {
        "total_eventos": len(eventos),
        "ultimo_estado": str(ultimo.get("estado_area", "")).strip(),
        "ultima_decision": str(ultimo.get("decision_cierre", "")).strip(),
        "ultimo_timestamp": str(ultimo.get("timestamp", "")).strip(),
    }
