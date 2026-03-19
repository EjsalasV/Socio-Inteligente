from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from domain.services.area_briefing import obtener_nombre_area_ls
from domain.services.leer_perfil import (
    cargar_perfil,
    obtener_estado_trabajo,
    obtener_marco_referencial,
    obtener_materialidad_ejecucion,
    obtener_nombre_cliente,
    obtener_periodo,
    ruta_tb_cliente,
)
from analysis.lector_tb import leer_trial_balance
from domain.context.motor_contexto import construir_contexto_cliente
from domain.context.motor_industria import construir_contexto_industrial
from core.utils.normalizaciones import normalizar_ls
from analysis.ranking_areas import obtener_ranking_areas_cliente
from domain.services.riesgos_area import detectar_riesgos_area, obtener_area
from analysis.variaciones import calcular_variaciones, marcar_movimientos_relevantes


_ETAPAS_VALIDAS = {"planificacion", "ejecucion", "cierre"}


def _normalizar_etapa(etapa: str | None) -> str:
    if etapa is None:
        return "planificacion"

    valor = str(etapa).strip().lower()
    if not valor:
        return "planificacion"

    aliases = {
        "planificación": "planificacion",
        "planning": "planificacion",
        "execution": "ejecucion",
    }
    valor = aliases.get(valor, valor)

    if valor not in _ETAPAS_VALIDAS:
        return "planificacion"
    return valor


def _nivel_riesgo_desde_score(score: float) -> str:
    if score >= 70:
        return "alto"
    if score >= 40:
        return "medio"
    return "bajo"


def obtener_senal_area(nombre_cliente: str, codigo_area: str) -> Dict[str, Any]:
    """
    Obtiene senales cuantitativas reales de un area L/S.
    """
    codigo_area = normalizar_ls(codigo_area)
    df_rank_areas = obtener_ranking_areas_cliente(nombre_cliente)
    if df_rank_areas is None:
        df_rank_areas = pd.DataFrame()
    if df_rank_areas.empty:
        return {
            "riesgo_score": 0,
            "nivel_riesgo": "bajo",
            "variacion_absoluta": 0.0,
            "variacion_porcentual": 0.0,
            "material": False,
            "banderas": ["sin datos de ranking de areas"],
            "tendencia": "sin_datos",
        }

    fila_area = df_rank_areas[df_rank_areas["area"].astype(str) == codigo_area]
    if fila_area.empty:
        return {
            "riesgo_score": 0,
            "nivel_riesgo": "bajo",
            "variacion_absoluta": 0.0,
            "variacion_porcentual": 0.0,
            "material": False,
            "banderas": [f"area {codigo_area} sin datos en ranking"],
            "tendencia": "sin_datos",
        }

    fila = fila_area.iloc[0]
    return {
        "riesgo_score": float(fila.get("score_riesgo", 0.0) or 0.0),
        "nivel_riesgo": _nivel_riesgo_desde_score(float(fila.get("score_riesgo", 0.0) or 0.0)),
        "variacion_absoluta": float(fila.get("variacion_abs_total", 0.0) or 0.0),
        "variacion_porcentual": float(fila.get("pct_total", 0.0) or 0.0),
        "material": bool(float(fila.get("materialidad_relativa", 0.0) or 0.0) >= 1.0),
        "banderas": fila.get("expert_flags", []) if isinstance(fila.get("expert_flags", []), list) else [],
        "tendencia": "positiva" if float(fila.get("variacion_abs_total", 0.0) or 0.0) > 0 else "negativa",
    }


def construir_contexto_auditoria(
    nombre_cliente: str,
    codigo_area: str,
    etapa: str = "planificacion",
) -> Dict[str, Any]:
    """
    Orquesta contexto cliente + industria + senales cuantitativas del area.
    """
    codigo_area = normalizar_ls(codigo_area)
    etapa_normalizada = _normalizar_etapa(etapa)

    perfil = cargar_perfil(nombre_cliente)
    contexto_cliente = construir_contexto_cliente(perfil)
    contexto_industria = construir_contexto_industrial(perfil)
    senal_area = obtener_senal_area(nombre_cliente, codigo_area)

    etapa_perfil = _normalizar_etapa(obtener_estado_trabajo(perfil))
    etapa_final = (
        etapa_perfil
        if etapa is None or not str(etapa).strip()
        else etapa_normalizada
    )

    areas_prioritarias_negocio = contexto_cliente.get("areas_prioritarias", [])
    areas_prioritarias_industria = contexto_industria.get("areas_prioritarias", [])

    return {
        "cliente": {
            "nombre": obtener_nombre_cliente(perfil),
            "periodo": obtener_periodo(perfil),
            "marco": obtener_marco_referencial(perfil),
            "sector_base": contexto_industria.get("sector_base"),
            "subtipo_negocio": contexto_industria.get("subtipo_negocio"),
            "tipo_contexto": contexto_cliente.get("tipo_contexto"),
        },
        "auditoria": {
            "materialidad_ejecucion": obtener_materialidad_ejecucion(perfil),
            "estado_trabajo": obtener_estado_trabajo(perfil),
        },
        "area_activa": {
            "codigo": codigo_area,
            "nombre": obtener_nombre_area_ls(codigo_area),
            "etapa": etapa_final,
        },
        "contexto_negocio": {
            "areas_prioritarias_negocio": areas_prioritarias_negocio,
            "areas_secundarias_negocio": contexto_cliente.get("areas_secundarias", []),
            "areas_prioritarias_industria": areas_prioritarias_industria,
            "areas_secundarias_industria": contexto_industria.get("areas_secundarias", []),
            "riesgos_esperados_negocio": contexto_cliente.get("riesgos_esperados", []),
            "riesgos_esperados_industria": contexto_industria.get("riesgos_esperados", []),
            "alertas_profesionales": contexto_industria.get("alertas_profesionales", []),
        },
        "relevancia_contextual": {
            "es_prioritaria_negocio": codigo_area in areas_prioritarias_negocio,
            "es_prioritaria_industria": codigo_area in areas_prioritarias_industria,
        },
        "senales_cuantitativas": senal_area,
    }
