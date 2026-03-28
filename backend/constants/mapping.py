from __future__ import annotations

from domain.catalogos_python.catalogo_ls import CATALOGO_LS as CATALOGO_LS

# Mapa derivado desde el catalogo oficial de dominio (fuente unica de verdad).
AREA_CODE_MAPPING: dict[str, str] = {
    str(code): str(defn.get("nombre", "")).strip()
    for code, defn in CATALOGO_LS.items()
    if isinstance(defn, dict)
}


def get_area_name(area_code: str, fallback: str | None = None) -> str:
    code = str(area_code).strip()
    if code in AREA_CODE_MAPPING and AREA_CODE_MAPPING[code]:
        return AREA_CODE_MAPPING[code]

    # Alias operativo para CxC consolidado.
    if code == "130":
        return "Cuentas por Cobrar"

    # Fallback por prefijo (ej: 130.9 usa 130 si existiera).
    prefix = code.split(".")[0]
    if prefix in AREA_CODE_MAPPING and AREA_CODE_MAPPING[prefix]:
        return AREA_CODE_MAPPING[prefix]

    return fallback or f"Área {code}"
