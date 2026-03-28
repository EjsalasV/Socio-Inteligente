from __future__ import annotations

AREA_CODE_MAPPING: dict[str, str] = {
    "130": "Cuentas por Cobrar",
    "140": "Efectivo y Equivalentes",
}


def get_area_name(area_code: str, fallback: str | None = None) -> str:
    return AREA_CODE_MAPPING.get(str(area_code), fallback or f"Área {area_code}")
