"""
Servicio de Materialidad Asistida

Sugiere valores de materialidad basado en NIAs y reglas de negocio.
El auditor siempre decide el valor final.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml

from analysis.lector_tb import obtener_resumen_tb
from core.configuracion import obtener_materialidad_config
from core.logger import obtener_logger
from domain.services.leer_perfil import leer_perfil


LOGGER = obtener_logger()

# Rutas
DATA_ROOT = Path(__file__).parent.parent.parent / "data"
REGLAS_PATH = DATA_ROOT / "catalogos" / "reglas_materialidad.yaml"


def obtener_reglas() -> dict[str, Any]:
    """Carga las reglas de materialidad desde YAML."""
    if not REGLAS_PATH.exists():
        LOGGER.warning("materialidad.reglas_path_no_encontrado", extra={"path": str(REGLAS_PATH)})
        return _reglas_por_defecto()

    try:
        with open(REGLAS_PATH, "r", encoding="utf-8") as f:
            reglas = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as exc:
        LOGGER.error(
            "materialidad.error_cargando_reglas",
            extra={"path": str(REGLAS_PATH), "error": str(exc)},
        )
        return _reglas_por_defecto()

    return reglas if isinstance(reglas, dict) else _reglas_por_defecto()


def _reglas_por_defecto() -> dict[str, Any]:
    """Retorna reglas por defecto si no se encuentran las del YAML."""
    return {
        "regla_defecto": {
            "base": "activos",
            "porcentaje_min": 0.03,
            "porcentaje_max": 0.05,
            "descripcion": "Regla por defecto",
        }
    }


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _resolver_minimum_threshold(
    perfil: dict[str, Any] | None,
    regla: dict[str, Any] | None,
) -> tuple[float, str]:
    # 1) cliente
    cliente_cfg = perfil.get("materialidad", {}) if isinstance(perfil, dict) else {}
    cliente_threshold = _safe_float(cliente_cfg.get("minimum_threshold"), -1)
    if cliente_threshold >= 0:
        return cliente_threshold, "cliente"

    # 2) sector (regla específica)
    if isinstance(regla, dict):
        regla_threshold = _safe_float(regla.get("minimum_threshold"), -1)
        if regla_threshold >= 0:
            return regla_threshold, "sector"

    # 3) global config
    global_cfg = obtener_materialidad_config()
    global_threshold = _safe_float(global_cfg.get("minimum_threshold"), 0)
    return max(global_threshold, 0), "global"


def obtener_regla_materialidad(cliente: str) -> dict[str, Any] | None:
    """
    Obtiene la regla de materialidad aplicable para un cliente.
    Busca primero por tipo_entidad, luego por sector.
    """
    perfil = leer_perfil(cliente)
    reglas = obtener_reglas()
    reglas_entidad = reglas.get("reglas_por_entidad", {})
    reglas_sector = reglas.get("reglas_por_sector", {})
    regla_defecto = reglas.get("regla_defecto", {})

    if not isinstance(reglas_entidad, dict):
        reglas_entidad = {}
    if not isinstance(reglas_sector, dict):
        reglas_sector = {}
    if not isinstance(regla_defecto, dict):
        regla_defecto = _reglas_por_defecto()["regla_defecto"]

    if not perfil:
        rule = dict(regla_defecto)
        rule["origen"] = "regla_defecto"
        return rule

    tipo_entidad = str(
        perfil.get("cliente", {}).get("tipo_entidad", "")
    ).upper().replace(" ", "_")
    if tipo_entidad and tipo_entidad in reglas_entidad:
        rule = dict(reglas_entidad[tipo_entidad])
        rule["origen"] = f"tipo_entidad:{tipo_entidad}"
        return rule

    sector = str(perfil.get("cliente", {}).get("sector", "")).lower().replace(" ", "_")
    if sector and sector in reglas_sector:
        rule = dict(reglas_sector[sector])
        rule["origen"] = f"sector:{sector}"
        return rule

    rule = dict(regla_defecto)
    rule["origen"] = "regla_defecto"
    return rule


def obtener_base_materialidad(cliente: str, base_requerida: str) -> float | None:
    """Obtiene el valor de la base para calcular materialidad."""
    resumen_tb = obtener_resumen_tb(cliente)
    if not isinstance(resumen_tb, dict):
        LOGGER.warning("materialidad.tb_no_disponible", extra={"cliente": cliente})
        return None

    mapa_bases = {
        "activos": _safe_float(resumen_tb.get("ACTIVO", 0)),
        "pasivos": _safe_float(resumen_tb.get("PASIVO", 0)),
        "patrimonio": _safe_float(resumen_tb.get("PATRIMONIO", 0)),
        "ingresos": _safe_float(resumen_tb.get("INGRESOS", 0)),
    }
    base_normalizada = str(base_requerida).lower().strip()
    if base_normalizada not in mapa_bases:
        LOGGER.warning(
            "materialidad.base_desconocida",
            extra={"cliente": cliente, "base_requerida": base_requerida},
        )
        return None

    valor = mapa_bases[base_normalizada]
    if valor == 0:
        return None

    # Se toma absoluto para escenarios de pérdida/patrimonio negativo.
    return abs(valor)


def _resolver_base_valor(cliente: str, base_requerida: str) -> tuple[float | None, str]:
    valor = obtener_base_materialidad(cliente, base_requerida)
    if valor and valor > 0:
        return valor, base_requerida

    for fallback in ["ingresos", "activos", "patrimonio", "pasivos"]:
        if fallback == base_requerida:
            continue
        v = obtener_base_materialidad(cliente, fallback)
        if v and v > 0:
            LOGGER.warning(
                "materialidad.base_fallback",
                extra={"cliente": cliente, "base_original": base_requerida, "base_fallback": fallback},
            )
            return v, fallback

    return None, base_requerida


def calcular_materialidad(cliente: str, base_valor: float | None = None) -> dict[str, Any] | None:
    """Calcula materialidad sugerida para un cliente."""
    regla = obtener_regla_materialidad(cliente)
    if not isinstance(regla, dict):
        LOGGER.error("materialidad.regla_no_disponible", extra={"cliente": cliente})
        return None

    base_requerida = str(regla.get("base", "activos")).lower()
    pct_min = max(_safe_float(regla.get("porcentaje_min", 0.03), 0.03), 0.0)
    pct_max = max(_safe_float(regla.get("porcentaje_max", 0.05), 0.05), pct_min)

    if base_valor is None:
        base_valor, base_utilizada = _resolver_base_valor(cliente, base_requerida)
    else:
        base_utilizada = base_requerida
        base_valor = abs(float(base_valor))

    if base_valor is None:
        LOGGER.error("materialidad.base_no_disponible", extra={"cliente": cliente, "base": base_requerida})
        return None

    materialidad_min = base_valor * pct_min
    materialidad_max = base_valor * pct_max
    materialidad_sugerida = (materialidad_min + materialidad_max) / 2

    perfil = leer_perfil(cliente) or {}
    minimum_threshold, threshold_origen = _resolver_minimum_threshold(perfil, regla)
    if materialidad_sugerida < minimum_threshold:
        materialidad_sugerida = minimum_threshold

    materialidad_desempeno = materialidad_sugerida * 0.75
    error_trivial = materialidad_sugerida * 0.05

    return {
        "cliente": cliente,
        "base_utilizada": base_utilizada,
        "valor_base": round(base_valor, 2),
        "porcentaje_minimo": round(pct_min * 100, 2),
        "porcentaje_maximo": round(pct_max * 100, 2),
        "materialidad_minima": round(materialidad_min, 2),
        "materialidad_maxima": round(materialidad_max, 2),
        "materialidad_sugerida": round(materialidad_sugerida, 2),
        "materialidad_desempeno": round(materialidad_desempeno, 2),
        "error_trivial": round(error_trivial, 2),
        "origen_regla": regla.get("origen", "unknown"),
        "descripcion_regla": regla.get("descripcion", "N/A"),
        "minimum_threshold_aplicado": round(minimum_threshold, 2),
        "minimum_threshold_origen": threshold_origen,
    }


def sugerir_materialidad(cliente: str) -> dict[str, Any] | None:
    """Obtiene sugerencia completa de materialidad para el auditor."""
    calculo = calcular_materialidad(cliente)
    if not isinstance(calculo, dict):
        return None

    perfil = leer_perfil(cliente) or {}
    nombre = perfil.get("cliente", {}).get("nombre_legal", "Cliente")
    sector = perfil.get("cliente", {}).get("sector", "N/A")
    recomendacion = (
        f"Para {nombre}, se sugiere materialidad de ${calculo['materialidad_sugerida']:,.0f} "
        f"(base {calculo['base_utilizada']}). "
        f"Rango tecnico: ${calculo['materialidad_minima']:,.0f} - ${calculo['materialidad_maxima']:,.0f}."
    )
    return {
        "cliente": cliente,
        "nombre_cliente": nombre,
        "sector": sector,
        "calculo": calculo,
        "recomendacion": recomendacion,
        "proximos_pasos": [
            f"1. Revisar recomendacion: ${calculo['materialidad_sugerida']:,.0f}",
            f"2. Confirmar valor final (rango: ${calculo['materialidad_minima']:,.0f} - ${calculo['materialidad_maxima']:,.0f})",
            f"3. Guardar materialidad elegida",
            f"4. Materialidad de desempeno: ${calculo['materialidad_desempeno']:,.0f}",
            f"5. Error trivial: ${calculo['error_trivial']:,.0f}",
        ],
    }


def guardar_sugerencia_materialidad(cliente: str, materialidad_elegida: float | None = None) -> bool:
    """Guarda la materialidad elegida por el auditor."""
    sugerencia = sugerir_materialidad(cliente)
    if not isinstance(sugerencia, dict):
        LOGGER.error("materialidad.no_guardada_sin_sugerencia", extra={"cliente": cliente})
        return False

    calculo = sugerencia["calculo"]
    if materialidad_elegida is None:
        materialidad_elegida = float(calculo["materialidad_sugerida"])

    materialidad_elegida = abs(float(materialidad_elegida))
    datos = {
        "cliente": cliente,
        "fecha": date.today().isoformat(),
        "materialidad_sugerida": calculo["materialidad_sugerida"],
        "materialidad_elegida": materialidad_elegida,
        "materialidad_desempeno": materialidad_elegida * 0.75,
        "error_trivial": materialidad_elegida * 0.05,
        "base_utilizada": calculo["base_utilizada"],
        "valor_base": calculo["valor_base"],
        "porcentaje_aplicado": round((materialidad_elegida / max(float(calculo["valor_base"]), 1.0)) * 100, 2),
        "origen_regla": calculo["origen_regla"],
        "minimum_threshold_aplicado": calculo.get("minimum_threshold_aplicado", 0),
        "minimum_threshold_origen": calculo.get("minimum_threshold_origen", "global"),
        "notas": "Materialidad establecida por auditor",
    }

    from infra.repositories.cliente_repository import guardar_materialidad

    exito = guardar_materialidad(cliente, datos)
    if not exito:
        LOGGER.error("materialidad.error_guardando", extra={"cliente": cliente})
    return bool(exito)


def obtener_materialidad_guardada(cliente: str) -> dict[str, Any] | None:
    """Obtiene la materialidad previamente guardada para un cliente."""
    client_path = DATA_ROOT / "clientes" / cliente / "materialidad.yaml"
    if not client_path.exists():
        return None

    try:
        with open(client_path, "r", encoding="utf-8") as f:
            datos = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as exc:
        LOGGER.error(
            "materialidad.error_cargando_guardada",
            extra={"cliente": cliente, "error": str(exc)},
        )
        return None

    return datos if isinstance(datos, dict) else None


def resumen_materialidad(cliente: str) -> dict[str, Any] | None:
    """Obtiene un resumen ejecutivo de materialidad."""
    sugerencia = sugerir_materialidad(cliente)
    guardada = obtener_materialidad_guardada(cliente)
    if not isinstance(sugerencia, dict):
        return None

    calculo = sugerencia["calculo"]
    return {
        "cliente": cliente,
        "nombre_cliente": sugerencia["nombre_cliente"],
        "materialidad_sugerida": calculo["materialidad_sugerida"],
        "materialidad_elegida": guardada.get("materialidad_elegida") if isinstance(guardada, dict) else None,
        "materialidad_desempeno": calculo["materialidad_desempeno"],
        "error_trivial": calculo["error_trivial"],
        "base": f"{calculo['porcentaje_maximo']}% de {calculo['base_utilizada']}",
        "estado": "ESTABLECIDA" if isinstance(guardada, dict) else "PENDIENTE",
    }
