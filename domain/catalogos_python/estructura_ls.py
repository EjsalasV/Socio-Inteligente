from __future__ import annotations

# Mapeo centralizado de L/S (Línea Sueldaria) a nombres descriptivos
# Usado por: area_briefing.py, procedimientos_area.py
MAPA_LS_AREA = {
    "14": "Inversiones no corrientes",
    "140": "Efectivo y equivalentes de efectivo",
    "130.1": "Cuentas por cobrar corrientes",
    "130.2": "Otras cuentas por cobrar",
    "35": "Cuentas por cobrar no corrientes",
    "110": "Inventarios",
    "136": "Activos por impuestos corrientes",
    "15": "Activos por impuestos diferidos",
    "425": "Cuentas por pagar",
    "425.1": "Cuentas por pagar comerciales",
    "425.2": "Cuentas por pagar a partes relacionadas",
    "42": "Porción corriente de pasivos no corrientes",
    "45": "Pasivos por impuestos corrientes",
    "47": "Otros pasivos corrientes",
    "5": "Pasivos no corrientes",
    "52": "Pasivos por impuestos diferidos",
    "55": "Otros pasivos no corrientes",
    "3": "Patrimonio",
    "31": "Capital o fondo patrimonial",
    "32": "Reservas",
    "33": "Resultados acumulados",
    "34": "Resultados del ejercicio",
}


def obtener_nombre_area_ls(codigo_ls: str) -> str:
    """
    Obtiene el nombre descriptivo de una L/S.

    Args:
        codigo_ls: Código de L/S (ej: "14", "425.1")

    Returns:
        Nombre descriptivo o el código mismo si no está en mapa
    """
    return MAPA_LS_AREA.get(codigo_ls, codigo_ls)
