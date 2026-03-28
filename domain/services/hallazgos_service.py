"""
Servicio de gestión de hallazgos de auditoría.
Permite crear, actualizar, listar y cerrar hallazgos por cliente y área.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

DATA_ROOT = Path("data") / "clientes"

try:
    from infra.repositories.supabase_repository import (
        cargar_hallazgos_remoto,
        guardar_hallazgos_remoto,
    )
except Exception:
    cargar_hallazgos_remoto = None
    guardar_hallazgos_remoto = None


def _ruta_hallazgos(cliente: str) -> Path:
    return DATA_ROOT / cliente / "hallazgos_gestion.yaml"


def cargar_hallazgos_gestion(cliente: str) -> list[dict[str, Any]]:
    # Remote-first (Supabase), fallback to YAML
    if callable(cargar_hallazgos_remoto):
        try:
            remoto = cargar_hallazgos_remoto(cliente)
            if isinstance(remoto, list) and remoto:
                return [x for x in remoto if isinstance(x, dict)]
        except Exception:
            pass

    ruta = _ruta_hallazgos(cliente)
    if not ruta.exists():
        return []
    with open(ruta, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    return data if isinstance(data, list) else []


def guardar_hallazgos_gestion(cliente: str, hallazgos: list[dict[str, Any]]) -> bool:
    try:
        # Remote-first save (Supabase), local as best-effort fallback
        if callable(guardar_hallazgos_remoto):
            try:
                guardar_hallazgos_remoto(cliente, hallazgos)
            except Exception:
                pass

        ruta = _ruta_hallazgos(cliente)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                yaml.safe_dump(hallazgos, f, allow_unicode=True, sort_keys=False)
        except OSError:
            # Streamlit Cloud has read-only filesystem
            # Writes are silently ignored in production
            pass
        return True
    except Exception as e:
        print(f"[hallazgos] Error guardando: {e}")
        return False


def crear_hallazgo(
    cliente: str,
    codigo_area: str,
    descripcion: str,
    aseveracion: str = "",
    nivel: str = "medio",
    responsable: str = "",
) -> dict[str, Any]:
    hallazgos = cargar_hallazgos_gestion(cliente)
    nuevo_id = f"H-{len(hallazgos) + 1:03d}"
    hallazgo = {
        "id": nuevo_id,
        "cliente": cliente,
        "codigo_area": codigo_area,
        "descripcion": descripcion,
        "aseveracion": aseveracion,
        "nivel": nivel,
        "responsable": responsable,
        "estado": "abierto",
        "fecha_creacion": datetime.now().isoformat(timespec="seconds"),
        "fecha_cierre": None,
        "notas": [],
    }
    hallazgos.append(hallazgo)
    guardar_hallazgos_gestion(cliente, hallazgos)
    return hallazgo


def actualizar_estado_hallazgo(
    cliente: str,
    hallazgo_id: str,
    nuevo_estado: str,
    nota: str = "",
) -> bool:
    hallazgos = cargar_hallazgos_gestion(cliente)
    for h in hallazgos:
        if h.get("id") == hallazgo_id:
            h["estado"] = nuevo_estado
            if nota:
                h.setdefault("notas", []).append(
                    {"timestamp": datetime.now().isoformat(timespec="seconds"), "nota": nota}
                )
            if nuevo_estado == "cerrado":
                h["fecha_cierre"] = datetime.now().isoformat(timespec="seconds")
            guardar_hallazgos_gestion(cliente, hallazgos)
            return True
    return False


def listar_hallazgos(
    cliente: str,
    estado: str | None = None,
    codigo_area: str | None = None,
) -> list[dict[str, Any]]:
    hallazgos = cargar_hallazgos_gestion(cliente)
    if estado:
        hallazgos = [h for h in hallazgos if h.get("estado") == estado]
    if codigo_area:
        hallazgos = [h for h in hallazgos if h.get("codigo_area") == codigo_area]
    return hallazgos


def resumen_hallazgos(cliente: str) -> dict[str, Any]:
    hallazgos = cargar_hallazgos_gestion(cliente)
    abiertos = [h for h in hallazgos if h.get("estado") == "abierto"]
    cerrados = [h for h in hallazgos if h.get("estado") == "cerrado"]
    altos = [h for h in abiertos if h.get("nivel") == "alto"]
    return {
        "total": len(hallazgos),
        "abiertos": len(abiertos),
        "cerrados": len(cerrados),
        "alto_riesgo_abiertos": len(altos),
    }
