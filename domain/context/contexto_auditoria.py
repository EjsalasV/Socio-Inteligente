from __future__ import annotations

from typing import Any, Dict

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
        "planificaciÃ³n": "planificacion",
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
    perfil = cargar_perfil(nombre_cliente)

    df_rank_areas, _, _ = obtener_ranking_areas_cliente(nombre_cliente)
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

    fila_area = df_rank_areas[df_rank_areas["ls"].astype(str) == codigo_area]
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
    score_hibrido = float(fila.get("score_total_hibrido", 0.0) or 0.0)
    variacion_neta = float(fila.get("variacion_total", 0.0) or 0.0)
    variacion_abs = float(fila.get("abs_variacion_total", 0.0) or 0.0)
    variacion_pct = float(fila.get("variacion_porcentual", 0.0) or 0.0)
    cuentas_relevantes = int(fila.get("cuentas_relevantes", 0) or 0)
    cuentas_sin_base = int(fila.get("cuentas_sin_base", 0) or 0)

    max_score = float(df_rank_areas["score_total_hibrido"].max() or 0.0)
    if max_score <= 0:
        riesgo_score = 0
    else:
        riesgo_score = int(round((score_hibrido / max_score) * 100))

    materialidad_ejecucion = float(obtener_materialidad_ejecucion(perfil) or 0.0)
    es_material = materialidad_ejecucion > 0 and variacion_abs >= materialidad_ejecucion

    tendencia = "estable"
    if variacion_neta > 0:
        tendencia = "creciente"
    elif variacion_neta < 0:
        tendencia = "decreciente"

    ruta_tb = ruta_tb_cliente(nombre_cliente)
    df_tb = leer_trial_balance(ruta_tb)
    df_var = marcar_movimientos_relevantes(calcular_variaciones(df_tb))
    area_df = obtener_area(df_var, codigo_area)
    riesgos = detectar_riesgos_area(area_df, codigo_area, perfil) if not area_df.empty else []

    banderas: list[str] = []
    if abs(variacion_pct) >= 30:
        if variacion_neta >= 0:
            banderas.append("crecimiento superior al 30%")
        else:
            banderas.append("caida superior al 30%")
    if es_material:
        banderas.append("variacion material frente a materialidad de ejecucion")
    if cuentas_relevantes >= 3:
        banderas.append(f"{cuentas_relevantes} cuentas con movimiento relevante")
    if cuentas_sin_base > 0:
        banderas.append(f"{cuentas_sin_base} cuentas sin base comparativa")

    for riesgo in riesgos:
        if str(riesgo.get("nivel", "")).upper() == "ALTO":
            titulo = str(riesgo.get("titulo", "")).strip()
            if titulo:
                banderas.append(titulo)

    # deduplicar conservando orden
    banderas = list(dict.fromkeys(banderas))

    return {
        "riesgo_score": riesgo_score,
        "nivel_riesgo": _nivel_riesgo_desde_score(riesgo_score),
        "variacion_absoluta": variacion_abs,
        "variacion_porcentual": variacion_pct,
        "material": es_material,
        "banderas": banderas,
        "tendencia": tendencia,
        "score_total_hibrido": score_hibrido,
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

