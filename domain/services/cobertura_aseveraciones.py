from __future__ import annotations

from typing import Any

from domain.catalogos_python.aseveraciones_ls import ASEVERACIONES_LS
from domain.catalogos_python.procedimientos_aseveraciones import (
    MAPA_PROCEDIMIENTOS_ASEVERACIONES,
)

_ESTADOS_EJECUTADOS = {"ejecutado", "completado", "cerrado"}
_ESTADOS_DEBILES = {"en_proceso"}
_ESTADOS_NO_APLICA = {"no_aplicable", "no_aplica"}


def _normalizar_codigo_ls(codigo_ls: str) -> str:
    return str(codigo_ls).strip()


def _normalizar_aseveracion(aseveracion: str) -> str:
    return str(aseveracion).strip().lower()


def _normalizar_hallazgos(hallazgos_abiertos: list[str] | None) -> list[str]:
    return [
        str(hallazgo).strip().lower()
        for hallazgo in (hallazgos_abiertos or [])
        if str(hallazgo).strip()
    ]


def evaluar_cobertura_aseveraciones(
    codigo_ls: str,
    procedimientos: list[dict[str, Any]],
    hallazgos_abiertos: list[str] | None = None,
) -> dict[str, Any]:
    """
    Evalúa la cobertura de aseveraciones esperadas para un área L/S.

    Reglas V1:
    - Usa mapeo procedimiento -> aseveraciones.
    - Considera estados ejecutados, débiles y no aplicables.
    - Hallazgos abiertos pueden debilitar aseveraciones que parecían cubiertas.

    Args:
        codigo_ls: Código de línea de significancia.
        procedimientos: Lista de procedimientos con al menos:
            - id
            - estado
        hallazgos_abiertos: Lista opcional de hallazgos abiertos.

    Returns:
        dict con:
        - esperadas
        - cubiertas
        - debiles
        - no_cubiertas
        - excluidas_no_aplica
        - cobertura_porcentaje
        - conclusion
    """
    codigo = _normalizar_codigo_ls(codigo_ls)
    esperadas = [_normalizar_aseveracion(asev) for asev in ASEVERACIONES_LS.get(codigo, [])]
    hallazgos = _normalizar_hallazgos(hallazgos_abiertos)

    cubiertas_set: set[str] = set()
    debiles_set: set[str] = set()
    no_aplica_set: set[str] = set()
    estados_por_aseveracion: dict[str, set[str]] = {}

    for procedimiento in procedimientos or []:
        estado = str(procedimiento.get("estado", "")).strip().lower()
        proc_id = str(procedimiento.get("id", "")).strip().lower()

        if not proc_id:
            continue

        aseveraciones_procedimiento = MAPA_PROCEDIMIENTOS_ASEVERACIONES.get(proc_id, [])

        for aseveracion in aseveraciones_procedimiento:
            asev = _normalizar_aseveracion(aseveracion)

            estados_por_aseveracion.setdefault(asev, set()).add(estado)

            if estado in _ESTADOS_EJECUTADOS:
                cubiertas_set.add(asev)
            elif estado in _ESTADOS_DEBILES:
                debiles_set.add(asev)
            elif estado in _ESTADOS_NO_APLICA:
                no_aplica_set.add(asev)

    excluidas: list[str] = []
    for asev in esperadas:
        if asev in no_aplica_set:
            estados = estados_por_aseveracion.get(asev, set())
            # Excluir solo si la aseveración fue marcada únicamente como no aplicable
            if estados and estados.issubset(_ESTADOS_NO_APLICA):
                excluidas.append(asev)

    esperadas_efectivas = [asev for asev in esperadas if asev not in excluidas]
    cubiertas = [asev for asev in esperadas_efectivas if asev in cubiertas_set]
    debiles = [
        asev for asev in esperadas_efectivas if asev in debiles_set and asev not in cubiertas_set
    ]
    no_cubiertas = [
        asev
        for asev in esperadas_efectivas
        if asev not in cubiertas_set and asev not in debiles_set
    ]

    # Si hay hallazgos abiertos que afectan una aseveración ya cubierta,
    # la bajamos a débil
    if hallazgos:
        impactadas = [asev for asev in cubiertas if any(asev in hallazgo for hallazgo in hallazgos)]
        if impactadas:
            debiles = list(dict.fromkeys(debiles + impactadas))
            cubiertas = [asev for asev in cubiertas if asev not in impactadas]

    cobertura_pct = (
        round((len(cubiertas) / len(esperadas_efectivas)) * 100, 1) if esperadas_efectivas else 0.0
    )

    if not esperadas:
        conclusion = "sin_mapeo"
    elif not no_cubiertas and not debiles:
        conclusion = "completa"
    elif len(no_cubiertas) <= 1 and len(debiles) <= 1:
        conclusion = "con_reservas"
    else:
        conclusion = "incompleta"

    return {
        "esperadas": esperadas_efectivas,
        "cubiertas": cubiertas,
        "debiles": debiles,
        "no_cubiertas": no_cubiertas,
        "excluidas_no_aplica": excluidas,
        "cobertura_porcentaje": cobertura_pct,
        "conclusion": conclusion,
    }
