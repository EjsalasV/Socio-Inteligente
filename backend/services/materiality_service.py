from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "data" / "catalogos" / "reglas_materialidad.yaml"

_CACHE: dict[str, Any] = {"signature": "", "rules": {}}

DEFAULT_AREA_PERCENTAGES: dict[str, float] = {
    "130": 0.05,
    "130.1": 0.05,
    "110": 0.03,
    "140": 0.03,
    "425": 0.04,
    "1500": 0.05,
    "1900": 0.04,
}


def _safe_signature(path: Path) -> str:
    try:
        stat = path.stat()
        return f"{int(stat.st_mtime_ns)}:{int(stat.st_size)}"
    except Exception:
        return "missing"


def _load_rules(force_reload: bool = False) -> dict[str, Any]:
    signature = _safe_signature(RULES_PATH)
    if not force_reload and _CACHE["signature"] == signature:
        return _CACHE["rules"]

    if not RULES_PATH.exists():
        _CACHE["signature"] = signature
        _CACHE["rules"] = {}
        return {}

    try:
        payload = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        payload = {}
    rules = payload if isinstance(payload, dict) else {}
    _CACHE["signature"] = signature
    _CACHE["rules"] = rules
    return rules


def _area_percentage(area_code: str) -> float:
    code = str(area_code or "").strip()
    if code in DEFAULT_AREA_PERCENTAGES:
        return DEFAULT_AREA_PERCENTAGES[code]
    prefix = code.split(".")[0]
    if prefix in DEFAULT_AREA_PERCENTAGES:
        return DEFAULT_AREA_PERCENTAGES[prefix]
    return 0.04


def calculate_materiality(cliente_ingresos: float, areas_aplicables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rules = _load_rules()
    regla_defecto = rules.get("regla_defecto") if isinstance(rules.get("regla_defecto"), dict) else {}
    minimum_threshold = float(regla_defecto.get("minimum_threshold") or 0.0)

    ingreso_base = float(cliente_ingresos or 0.0)
    if ingreso_base <= 0:
        ingreso_base = float(regla_defecto.get("minimum_threshold") or 100000.0)

    out: list[dict[str, Any]] = []
    for area in areas_aplicables:
        if not isinstance(area, dict):
            continue
        area_code = str(area.get("codigo") or "").strip()
        if not area_code:
            continue
        area_name = str(area.get("nombre") or f"Area {area_code}").strip()
        percentage = _area_percentage(area_code)
        suggested = ingreso_base * percentage
        if minimum_threshold > 0:
            suggested = max(suggested, minimum_threshold)
        out.append(
            {
                "area_codigo": area_code,
                "area_nombre": area_name,
                "porcentaje_aplicado": round(percentage * 100.0, 2),
                "base_referencia": round(ingreso_base, 2),
                "materialidad_sugerida": round(suggested, 2),
            }
        )

    return out

