from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path

from infra.repositories.cliente_repository import cargar_perfil as repo_cargar_perfil


def leer_perfil(cliente: str) -> Optional[Dict[str, Any]]:
    """
    Lee el perfil de un cliente desde el repositorio y valida su estructura básica.

    Args:
        cliente: Nombre de la carpeta del cliente.

    Returns:
        dict con el perfil cargado si es válido, o None si falla.
    """
    try:
        perfil = repo_cargar_perfil(cliente)

        if not perfil:
            print(f"⚠️ No se encontró perfil para el cliente: {cliente}")
            return None

        validar_perfil_basico(perfil)
        return perfil

    except Exception as e:
        print(f"❌ Error al leer perfil de {cliente}: {e}")
        return None


# =========================================================
# GETTERS POR BLOQUE
# =========================================================

def obtener_cliente(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("cliente", {})


def obtener_encargo(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("encargo", {})


def obtener_materialidad(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("materialidad", {})


def obtener_materialidad_preliminar(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return obtener_materialidad(perfil).get("preliminar", {})


def obtener_materialidad_final(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return obtener_materialidad(perfil).get("final", {})


def obtener_riesgo_global(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("riesgo_global", {})


def obtener_contexto_negocio(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("contexto_negocio", {})


def obtener_operacion(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("operacion", {})


def obtener_infraestructura(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("infraestructura", {})


def obtener_tesoreria(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("tesoreria", {})


def obtener_nomina(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("nomina", {})


def obtener_banderas_generales(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("banderas_generales", {})


def obtener_notas_generales(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("notas_generales", {})


def obtener_administracion(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("administracion", {})


def obtener_propiedad(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("propiedad", {})


def obtener_industria_inteligente(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return perfil.get("industria_inteligente", {})


def obtener_reguladores_secundarios(perfil: Dict[str, Any]) -> list[Any]:
    return perfil.get("reguladores_secundarios", [])


# =========================================================
# ACCESOS RÁPIDOS CLIENTE
# =========================================================

def obtener_nombre_cliente(perfil: Dict[str, Any]) -> str:
    return obtener_cliente(perfil).get("nombre_legal", "")


def obtener_nombre_corto(perfil: Dict[str, Any]) -> str:
    return obtener_cliente(perfil).get("nombre_corto", "")


def obtener_ruc(perfil: Dict[str, Any]) -> str:
    return obtener_cliente(perfil).get("ruc", "")


def obtener_tipo_entidad(perfil: Dict[str, Any]) -> str:
    return obtener_cliente(perfil).get("tipo_entidad", "")


def obtener_pais(perfil: Dict[str, Any]) -> str:
    return obtener_cliente(perfil).get("pais", "")


def obtener_domicilio(perfil: Dict[str, Any]) -> str:
    return obtener_cliente(perfil).get("domicilio", "")


def obtener_moneda_funcional(perfil: Dict[str, Any]) -> str:
    return obtener_cliente(perfil).get("moneda_funcional", "")


def obtener_sector(perfil: Dict[str, Any]) -> str:
    return obtener_cliente(perfil).get("sector", "")


def obtener_subsector(perfil: Dict[str, Any]) -> str:
    return obtener_cliente(perfil).get("subsector", "")


# =========================================================
# ACCESOS RÁPIDOS ENCARGO
# =========================================================

def obtener_periodo(perfil: Dict[str, Any]) -> int | None:
    return obtener_encargo(perfil).get("anio_activo")


def obtener_periodo_inicio(perfil: Dict[str, Any]) -> str | None:
    return obtener_encargo(perfil).get("periodo_inicio")


def obtener_periodo_fin(perfil: Dict[str, Any]) -> str | None:
    return obtener_encargo(perfil).get("periodo_fin")


def obtener_marco_referencial(perfil: Dict[str, Any]) -> str:
    return obtener_encargo(perfil).get("marco_referencial", "")


def obtener_tipo_encargo(perfil: Dict[str, Any]) -> str:
    return obtener_encargo(perfil).get("tipo_encargo", "")


def obtener_estado_trabajo(perfil: Dict[str, Any]) -> str:
    encargo = obtener_encargo(perfil)
    return encargo.get("estado_trabajo", "") or encargo.get("fase_actual", "")


def obtener_fase_actual(perfil: Dict[str, Any]) -> str:
    return obtener_encargo(perfil).get("fase_actual", "")


def obtener_socio_asignado(perfil: Dict[str, Any]) -> str:
    return obtener_encargo(perfil).get("socio_asignado", "")


def obtener_gerente_asignado(perfil: Dict[str, Any]) -> str:
    return obtener_encargo(perfil).get("gerente_asignado", "")


def obtener_encargado_asignado(perfil: Dict[str, Any]) -> str:
    return obtener_encargo(perfil).get("encargado_asignado", "")


# =========================================================
# ACCESOS RÁPIDOS MATERIALIDAD
# =========================================================

def obtener_base_materialidad(perfil: Dict[str, Any]) -> str:
    return obtener_materialidad(perfil).get("base_utilizada", "")


def obtener_estado_materialidad(perfil: Dict[str, Any]) -> str:
    return obtener_materialidad(perfil).get("estado_materialidad", "")


def obtener_materialidad_planeacion(perfil: Dict[str, Any]) -> float | None:
    estado = obtener_estado_materialidad(perfil)
    if estado == "final":
        return obtener_materialidad_final(perfil).get("materialidad_planeacion")
    return obtener_materialidad_preliminar(perfil).get("materialidad_global")


def obtener_materialidad_ejecucion(perfil: Dict[str, Any]) -> float | None:
    estado = obtener_estado_materialidad(perfil)
    if estado == "final":
        return obtener_materialidad_final(perfil).get("materialidad_ejecucion")
    return obtener_materialidad_preliminar(perfil).get("materialidad_desempeno")


def obtener_umbral_trivialidad(perfil: Dict[str, Any]) -> float | None:
    estado = obtener_estado_materialidad(perfil)
    if estado == "final":
        return obtener_materialidad_final(perfil).get("umbral_trivialidad")
    return obtener_materialidad_preliminar(perfil).get("error_trivial")


# =========================================================
# VALIDACIÓN
# =========================================================

def validar_perfil_basico(perfil: Dict[str, Any]) -> None:
    if not isinstance(perfil, dict):
        raise ValueError("El perfil debe ser un diccionario.")

    campos_minimos = [
        ("cliente", "nombre_legal"),
        ("cliente", "nombre_corto"),
        ("cliente", "ruc"),
        ("encargo", "anio_activo"),
        ("encargo", "marco_referencial"),
        ("encargo", "tipo_encargo"),
    ]

    faltantes = []

    for bloque, campo in campos_minimos:
        valor = perfil.get(bloque, {}).get(campo)
        if valor in [None, ""]:
            faltantes.append(f"{bloque}.{campo}")

    if faltantes:
        raise ValueError(
            "El perfil no tiene completos los siguientes campos mínimos: "
            + ", ".join(faltantes)
        )


# =========================================================
# RESUMEN
# =========================================================

def resumen_perfil(perfil: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "cliente": obtener_nombre_cliente(perfil),
        "nombre_corto": obtener_nombre_corto(perfil),
        "ruc": obtener_ruc(perfil),
        "tipo_entidad": obtener_tipo_entidad(perfil),
        "pais": obtener_pais(perfil),
        "domicilio": obtener_domicilio(perfil),
        "moneda_funcional": obtener_moneda_funcional(perfil),
        "sector": obtener_sector(perfil),
        "subsector": obtener_subsector(perfil),
        "periodo": obtener_periodo(perfil),
        "periodo_inicio": obtener_periodo_inicio(perfil),
        "periodo_fin": obtener_periodo_fin(perfil),
        "marco_referencial": obtener_marco_referencial(perfil),
        "tipo_encargo": obtener_tipo_encargo(perfil),
        "estado_trabajo": obtener_estado_trabajo(perfil),
        "fase_actual": obtener_fase_actual(perfil),
        "socio_asignado": obtener_socio_asignado(perfil),
        "gerente_asignado": obtener_gerente_asignado(perfil),
        "encargado_asignado": obtener_encargado_asignado(perfil),
        "materialidad": {
            "base_utilizada": obtener_base_materialidad(perfil),
            "estado_materialidad": obtener_estado_materialidad(perfil),
            "materialidad_planeacion": obtener_materialidad_planeacion(perfil),
            "materialidad_ejecucion": obtener_materialidad_ejecucion(perfil),
            "umbral_trivialidad": obtener_umbral_trivialidad(perfil),
            "comentario_base": obtener_materialidad(perfil).get("comentario_base", ""),
            "preliminar": obtener_materialidad_preliminar(perfil),
            "final": obtener_materialidad_final(perfil),
        },
        "riesgo_global": obtener_riesgo_global(perfil),
        "contexto_negocio": obtener_contexto_negocio(perfil),
        "operacion": obtener_operacion(perfil),
        "infraestructura": obtener_infraestructura(perfil),
        "tesoreria": obtener_tesoreria(perfil),
        "nomina": obtener_nomina(perfil),
        "banderas_generales": obtener_banderas_generales(perfil),
        "notas_generales": obtener_notas_generales(perfil),
        "administracion": obtener_administracion(perfil),
        "propiedad": obtener_propiedad(perfil),
        "industria_inteligente": obtener_industria_inteligente(perfil),
        "reguladores_secundarios": obtener_reguladores_secundarios(perfil),
    }


def obtener_datos_clave(cliente: str) -> Optional[Dict[str, Any]]:
    perfil = leer_perfil(cliente)

    if not perfil:
        return None

    return {
        "nombre": obtener_nombre_cliente(perfil),
        "nombre_corto": obtener_nombre_corto(perfil),
        "ruc": obtener_ruc(perfil),
        "sector": obtener_sector(perfil),
        "tipo_entidad": obtener_tipo_entidad(perfil),
        "periodo": obtener_periodo(perfil),
        "marco_referencial": obtener_marco_referencial(perfil),
    }


def validar_cliente(cliente: str) -> bool:
    perfil = leer_perfil(cliente)
    return perfil is not None


def cargar_perfil(cliente: str) -> Optional[Dict[str, Any]]:
    """Compatibilidad con nombre legacy tras refactor."""
    return leer_perfil(cliente)


def ruta_tb_cliente(cliente: str) -> str:
    """Compatibilidad con API legacy para ubicación de tb.xlsx."""
    return str(Path(__file__).resolve().parents[2] / "data" / "clientes" / cliente / "tb.xlsx")
