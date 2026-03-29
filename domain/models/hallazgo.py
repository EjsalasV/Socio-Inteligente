from __future__ import annotations

from typing import Any

from domain.services.area_briefing import construir_foco_auditoria, construir_resumen_area
from domain.context.contexto_auditoria import construir_contexto_auditoria
from domain.services.leer_perfil import cargar_perfil, ruta_tb_cliente
from analysis.lector_tb import leer_trial_balance
from domain.services.riesgos_area import detectar_riesgos_area, obtener_area
from analysis.variaciones import calcular_variaciones, marcar_movimientos_relevantes


def _normalizar_etapa(etapa: str | None) -> str:
    valor = str(etapa or "").strip().lower()
    aliases = {
        "planificacion": "planificacion",
        "planificación": "planificacion",
        "ejecucion": "ejecucion",
        "ejecución": "ejecucion",
        "cierre": "cierre",
    }
    return aliases.get(valor, "ejecucion")


def _afirmaciones_por_area(codigo_ls: str) -> list[str]:
    codigo = str(codigo_ls).strip()
    if codigo.startswith("13"):
        return ["Valuacion", "Existencia", "Presentacion"]
    if codigo in {"14", "15"}:
        return ["Valuacion", "Existencia", "Revelacion"]
    if codigo.startswith("425"):
        return ["Integridad", "Corte", "Presentacion"]
    if codigo.startswith("42"):
        return ["Integridad", "Corte", "Presentacion"]
    if codigo.startswith("15") or codigo.startswith("16") or codigo.startswith("17"):
        return ["Ocurrencia", "Corte", "Clasificacion"]
    return ["Existencia", "Integridad", "Presentacion"]


def _criterio_generico(codigo_ls: str) -> str:
    afirmaciones = _afirmaciones_por_area(codigo_ls)
    return (
        "El rubro debe reconocerse, medirse, presentarse y revelarse con soporte suficiente, "
        "de forma consistente con su naturaleza y con las afirmaciones de auditoria aplicables "
        f"({', '.join(afirmaciones[:2]).lower()})."
    )


def _causa_sugerida(
    riesgos: list[dict[str, Any]],
    resumen: dict[str, Any],
    contexto: dict[str, Any],
) -> str:
    partes: list[str] = []
    if resumen.get("cuentas_sin_base", 0):
        partes.append("ausencia de trazabilidad completa en cuentas nuevas o sin comparativo")
    if contexto.get("senales_cuantitativas", {}).get("material"):
        partes.append("debilidades en revision de cierre frente a partidas materiales")
    if contexto.get("relevancia_contextual", {}).get("es_prioritaria_industria"):
        partes.append(
            "criterio tecnico insuficientemente documentado en un rubro sensible por industria"
        )
    if any(str(r.get("nivel", "")).upper() == "ALTO" for r in riesgos):
        partes.append(
            "respuesta de auditoria no alineada plenamente con riesgos altos identificados"
        )

    if not partes:
        return (
            "Posible causa: documentacion insuficiente del analisis tecnico y "
            "debilidades en la supervision del cierre del rubro."
        )

    return "Posible causa: " + "; ".join(partes) + "."


def _efecto_sugerido(
    contexto: dict[str, Any],
    resumen: dict[str, Any],
) -> str:
    area = contexto.get("area_activa", {})
    senales = contexto.get("senales_cuantitativas", {})
    material_txt = (
        "con impacto potencial material"
        if senales.get("material")
        else "con impacto potencial relevante"
    )
    return (
        f"Existe riesgo de incorreccion en {area.get('nombre', 'el rubro')}, "
        f"particularmente en valuacion/presentacion, {material_txt}, "
        f"considerando variacion acumulada de {float(resumen.get('variacion_acumulada', 0) or 0):,.2f}."
    )


def _recomendacion_sugerida(
    focos: list[str],
    riesgos: list[dict[str, Any]],
) -> str:
    acciones: list[str] = []
    for foco in focos[:2]:
        acciones.append(foco.rstrip("."))
    for r in riesgos[:1]:
        titulo = str(r.get("titulo", "")).strip()
        if titulo:
            acciones.append(f"dejar evidencia explicita de respuesta al riesgo '{titulo}'")

    if not acciones:
        acciones = [
            "formalizar analisis tecnico del rubro",
            "conciliar movimientos con soportes primarios",
            "documentar conclusion de auditoria y revelacion",
        ]

    return (
        "Documentar y ejecutar: "
        + "; ".join(acciones)
        + ". Ademas, validar consistencia entre soporte, medicion y presentacion final."
    )


def estructurar_hallazgo_llm(
    nombre_cliente: str,
    codigo_ls: str,
    situacion_detectada: str,
    monto_referencia: str | None = None,
    etapa: str = "ejecucion",
) -> str:
    """
    Estructura un hallazgo en formato de auditoria usable.
    """
    etapa_norm = _normalizar_etapa(etapa)
    contexto = construir_contexto_auditoria(nombre_cliente, codigo_ls, etapa_norm)

    perfil = cargar_perfil(nombre_cliente)
    df_tb = leer_trial_balance(ruta_tb_cliente(nombre_cliente))
    df_var = marcar_movimientos_relevantes(calcular_variaciones(df_tb))
    area_df = obtener_area(df_var, str(codigo_ls))

    resumen = (
        construir_resumen_area(area_df)
        if not area_df.empty
        else {
            "variacion_acumulada": 0.0,
            "cuentas_sin_base": 0,
        }
    )
    riesgos = detectar_riesgos_area(area_df, str(codigo_ls), perfil) if not area_df.empty else []
    focos = construir_foco_auditoria(str(codigo_ls), perfil, area_df) if not area_df.empty else []

    cliente = contexto.get("cliente", {})
    area = contexto.get("area_activa", {})
    afirmaciones = _afirmaciones_por_area(str(codigo_ls))
    riesgo_principal = contexto.get("senales_cuantitativas", {}).get("nivel_riesgo", "medio")

    monto_txt = f" Monto de referencia reportado: {monto_referencia}." if monto_referencia else ""
    condicion = (
        f"Durante la etapa de {etapa_norm}, en {area.get('nombre', f'L/S {codigo_ls}')} "
        f"del cliente {cliente.get('nombre', nombre_cliente)}, se detecto lo siguiente: "
        f"{situacion_detectada.strip()}."
        f"{monto_txt}"
    )

    criterio = _criterio_generico(str(codigo_ls))
    causa = _causa_sugerida(riesgos, resumen, contexto)
    efecto = _efecto_sugerido(contexto, resumen)
    recomendacion = _recomendacion_sugerida(focos, riesgos)

    bloques = []
    bloques.append("CONDICION")
    bloques.append(condicion)
    bloques.append("")
    bloques.append("CRITERIO")
    bloques.append(criterio)
    bloques.append("")
    bloques.append("CAUSA")
    bloques.append(causa)
    bloques.append("")
    bloques.append("EFECTO")
    bloques.append(efecto)
    bloques.append("")
    bloques.append("RECOMENDACION")
    bloques.append(recomendacion)
    bloques.append("")
    bloques.append("RIESGO / AFIRMACION AFECTADA")
    bloques.append(
        f"Riesgo estimado: {riesgo_principal}. "
        f"Afirmaciones mas expuestas: {', '.join(afirmaciones[:2])}."
    )

    return "\n".join(bloques)
