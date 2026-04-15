from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CATALOGOS_ROOT = ROOT / "data" / "catalogos"
PROCEDURES_PATH = CATALOGOS_ROOT / "procedimientos_por_area.yaml"
RISKS_PATH = CATALOGOS_ROOT / "riesgos_por_area.yaml"
TAX_ALERTS_PATH = CATALOGOS_ROOT / "alertas_tributarias_por_area.yaml"
AREAS_PATH = CATALOGOS_ROOT / "areas.yaml"

_CACHE: dict[str, Any] = {
    "signatures": {},
    "procedures": {},
    "risks": {},
    "tax_alerts": {},
    "areas_lookup": {},
}


def _safe_signature(path: Path) -> str:
    try:
        stat = path.stat()
        return f"{int(stat.st_mtime_ns)}:{int(stat.st_size)}"
    except Exception:
        return "missing"


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"true", "1", "si", "sí", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return default


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _infer_nia_ref(tipo: str) -> str:
    mapping = {
        "confirmacion_externa": "NIA 505",
        "analitico": "NIA 520",
        "observacion": "NIA 500",
        "inspeccion": "NIA 500",
        "conciliacion": "NIA 500",
        "recalculo": "NIA 500",
        "sustantivo_detalle": "NIA 500",
    }
    key = _normalize_text(tipo).lower()
    return mapping.get(key, "NIA 500")


def _load_areas_lookup(force_reload: bool = False) -> dict[str, str]:
    signature = _safe_signature(AREAS_PATH)
    if not force_reload and _CACHE["signatures"].get("areas") == signature:
        return _CACHE["areas_lookup"]

    payload = _read_yaml(AREAS_PATH)
    areas_list = payload.get("areas") if isinstance(payload.get("areas"), list) else []
    lookup: dict[str, str] = {}
    for item in areas_list:
        if not isinstance(item, dict):
            continue
        code = _normalize_text(item.get("codigo"))
        title = _normalize_text(item.get("titulo"))
        if code:
            lookup[code] = title

    _CACHE["areas_lookup"] = lookup
    _CACHE["signatures"]["areas"] = signature
    return lookup


def load_procedures_yaml(force_reload: bool = False) -> dict[str, Any]:
    signature = _safe_signature(PROCEDURES_PATH)
    if not force_reload and _CACHE["signatures"].get("procedures") == signature:
        return _CACHE["procedures"]

    raw = _read_yaml(PROCEDURES_PATH)
    normalized: dict[str, dict[str, Any]] = {}
    for area_code_raw, area_payload in raw.items():
        area_code = _normalize_text(area_code_raw)
        if not area_code or not isinstance(area_payload, dict):
            continue
        area_name = _normalize_text(area_payload.get("nombre"))
        procedures_raw = area_payload.get("procedimientos") if isinstance(area_payload.get("procedimientos"), list) else []
        procedures: list[dict[str, Any]] = []
        for proc in procedures_raw:
            if not isinstance(proc, dict):
                continue
            tipo = _normalize_text(proc.get("tipo")).lower()
            nia_ref = _normalize_text(proc.get("nia_ref")) or _infer_nia_ref(tipo)
            procedures.append(
                {
                    "id": _normalize_text(proc.get("id")),
                    "descripcion": _normalize_text(proc.get("descripcion")),
                    "tipo": tipo,
                    "afirmacion": _normalize_text(proc.get("afirmacion")),
                    "obligatorio": _to_bool(proc.get("obligatorio"), default=False),
                    "nia_ref": nia_ref,
                }
            )
        normalized[area_code] = {
            "nombre": area_name,
            "procedimientos": procedures,
        }

    _CACHE["procedures"] = normalized
    _CACHE["signatures"]["procedures"] = signature
    return normalized


def load_risks_yaml(force_reload: bool = False) -> dict[str, Any]:
    signature = _safe_signature(RISKS_PATH)
    if not force_reload and _CACHE["signatures"].get("risks") == signature:
        return _CACHE["risks"]
    raw = _read_yaml(RISKS_PATH)
    normalized: dict[str, dict[str, Any]] = {}
    for area_code_raw, area_payload in raw.items():
        area_code = _normalize_text(area_code_raw)
        if not area_code or not isinstance(area_payload, dict):
            continue
        area_name = _normalize_text(area_payload.get("nombre"))
        riesgos_raw = area_payload.get("riesgos") if isinstance(area_payload.get("riesgos"), list) else []
        riesgos: list[dict[str, Any]] = []
        for risk in riesgos_raw:
            if not isinstance(risk, dict):
                continue
            riesgos.append(
                {
                    "id": _normalize_text(risk.get("id")),
                    "descripcion": _normalize_text(risk.get("descripcion")),
                    "nivel": _normalize_text(risk.get("nivel")).lower(),
                    "afirmacion": _normalize_text(risk.get("afirmacion")),
                }
            )
        normalized[area_code] = {"nombre": area_name, "riesgos": riesgos}
    _CACHE["risks"] = normalized
    _CACHE["signatures"]["risks"] = signature
    return normalized


def load_tax_alerts_yaml(force_reload: bool = False) -> dict[str, Any]:
    signature = _safe_signature(TAX_ALERTS_PATH)
    if not force_reload and _CACHE["signatures"].get("tax_alerts") == signature:
        return _CACHE["tax_alerts"]
    raw = _read_yaml(TAX_ALERTS_PATH)
    normalized: dict[str, dict[str, Any]] = {}
    for area_code_raw, area_payload in raw.items():
        area_code = _normalize_text(area_code_raw)
        if not area_code or not isinstance(area_payload, dict):
            continue
        area_name = _normalize_text(area_payload.get("nombre"))
        alerts_raw = area_payload.get("alertas") if isinstance(area_payload.get("alertas"), list) else []
        alerts: list[dict[str, Any]] = []
        for alert in alerts_raw:
            if not isinstance(alert, dict):
                continue
            alerts.append(
                {
                    "id": _normalize_text(alert.get("id")),
                    "descripcion": _normalize_text(alert.get("descripcion")),
                    "nivel": _normalize_text(alert.get("nivel")).lower(),
                    "norma": _normalize_text(alert.get("norma")),
                    "accion": _normalize_text(alert.get("accion")),
                }
            )
        normalized[area_code] = {"nombre": area_name, "alertas": alerts}
    _CACHE["tax_alerts"] = normalized
    _CACHE["signatures"]["tax_alerts"] = signature
    return normalized


def _area_sort_key(area_code: str) -> tuple[int, ...]:
    parts = []
    for part in str(area_code).split("."):
        try:
            parts.append(int(part))
        except Exception:
            parts.append(9999)
    return tuple(parts)


def list_areas_with_procedure_count() -> list[dict[str, Any]]:
    procedures_map = load_procedures_yaml()
    areas_lookup = _load_areas_lookup()

    all_codes = set(areas_lookup.keys()) | set(procedures_map.keys())
    rows: list[dict[str, Any]] = []
    for area_code in all_codes:
        proc_list = procedures_map.get(area_code, {}).get("procedimientos", [])
        area_name = _normalize_text(procedures_map.get(area_code, {}).get("nombre")) or areas_lookup.get(area_code, "")
        rows.append(
            {
                "area_codigo": area_code,
                "area_nombre": area_name or f"Area {area_code}",
                "procedures_count": len(proc_list) if isinstance(proc_list, list) else 0,
            }
        )
    rows.sort(key=lambda row: _area_sort_key(str(row.get("area_codigo"))))
    return rows


def get_procedures_by_area(area_codigo: str) -> dict[str, Any]:
    area_code = _normalize_text(area_codigo)
    procedures_map = load_procedures_yaml()
    areas_lookup = _load_areas_lookup()
    risks_map = load_risks_yaml()
    alerts_map = load_tax_alerts_yaml()

    procedures_entry = procedures_map.get(area_code, {})
    risks_entry = risks_map.get(area_code, {})
    alerts_entry = alerts_map.get(area_code, {})

    area_name = (
        _normalize_text(procedures_entry.get("nombre"))
        or _normalize_text(risks_entry.get("nombre"))
        or _normalize_text(alerts_entry.get("nombre"))
        or areas_lookup.get(area_code, "")
    )

    return {
        "area_codigo": area_code,
        "area_nombre": area_name or f"Area {area_code}",
        "procedimientos": procedures_entry.get("procedimientos", []) if isinstance(procedures_entry, dict) else [],
        "riesgos_tipicos": risks_entry.get("riesgos", []) if isinstance(risks_entry, dict) else [],
        "alertas_tributarias": alerts_entry.get("alertas", []) if isinstance(alerts_entry, dict) else [],
    }


def get_procedure_counts_map() -> dict[str, int]:
    rows = list_areas_with_procedure_count()
    return {str(row.get("area_codigo")): int(row.get("procedures_count") or 0) for row in rows}

