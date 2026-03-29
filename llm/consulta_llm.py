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
    if codigo.startswith("42") or codigo.startswith("425"):
        return ["Integridad", "Corte", "Presentacion"]
    if codigo.startswith("15") or codigo.startswith("16") or codigo.startswith("17"):
        return ["Ocurrencia", "Corte", "Clasificacion"]
    return ["Existencia", "Integridad", "Presentacion"]


def _requiere_respaldo_normativo(consulta: str, contexto: dict[str, Any]) -> bool:
    q = consulta.lower()
    pide_norma = any(
        k in q for k in ["norma", "niif", "nia", "ifrs", "ias", "normativo", "fundamento"]
    )
    caso_delicado = any(
        k in q for k in ["sin contrato", "fraude", "manipul", "sin soporte", "incumpl", "ilegal"]
    )
    riesgo_alto = contexto.get("senales_cuantitativas", {}).get("nivel_riesgo") == "alto"
    return pide_norma or caso_delicado or riesgo_alto


def responder_consulta_area_llm(
    nombre_cliente: str,
    codigo_ls: str,
    consulta_usuario: str,
    etapa: str = "ejecucion",
) -> str:
    """
    Responde una consulta del auditor con criterio y direccion accionable.
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
            "cuentas": 0,
            "saldo_actual": 0.0,
            "variacion_neta": 0.0,
            "variacion_acumulada": 0.0,
            "cuentas_relevantes": 0,
            "cuentas_sin_base": 0,
        }
    )
    riesgos = detectar_riesgos_area(area_df, str(codigo_ls), perfil) if not area_df.empty else []
    focos = construir_foco_auditoria(str(codigo_ls), perfil, area_df) if not area_df.empty else []

    senales = contexto.get("senales_cuantitativas", {})
    relevancia = contexto.get("relevancia_contextual", {})
    area = contexto.get("area_activa", {})
    cliente = contexto.get("cliente", {})

    top_riesgos = [r for r in riesgos if str(r.get("nivel", "")).upper() in {"ALTO", "MEDIO"}][:2]
    top_focos = (
        focos[:4]
        if focos
        else [
            "Aterrizar el hecho economico con soporte primario.",
            "Verificar reconocimiento, medicion y presentacion.",
            "Conciliar movimientos contra auxiliares y evidencia externa.",
        ]
    )
    afirmaciones = _afirmaciones_por_area(str(codigo_ls))

    lectura = (
        f"En {area.get('nombre', f'L/S {codigo_ls}')}, cliente {cliente.get('nombre', nombre_cliente)}, "
        f"tu consulta apunta a un posible riesgo de criterio en etapa {etapa_norm}. "
        f"El area muestra variacion acumulada de {float(resumen.get('variacion_acumulada', 0) or 0):,.2f}, "
        f"score {senales.get('riesgo_score', 0)}/100 y nivel {senales.get('nivel_riesgo', 'bajo')}."
    )

    if relevancia.get("es_prioritaria_negocio") or relevancia.get("es_prioritaria_industria"):
        lectura += " Ademas, es un area naturalmente sensible por contexto del negocio/industria."
    if not senales.get("material", False):
        lectura += " Aunque no supera materialidad, el patron puede requerir pruebas dirigidas."

    acciones: list[str] = []
    for f in top_focos:
        acciones.append(f)
        if len(acciones) == 3:
            break
    for r in top_riesgos:
        t = str(r.get("titulo", "")).strip()
        if t:
            acciones.append(f"Responder de forma explicita el riesgo: {t}.")
        if len(acciones) == 4:
            break
    acciones = list(dict.fromkeys(acciones))[:4]

    ojo_profesional = (
        "No cierres conclusion solo por cuadre matematico del saldo final; "
        "lo critico es la sustancia del hecho, su soporte y el criterio tecnico aplicado."
    )
    if resumen.get("cuentas_sin_base", 0):
        ojo_profesional = (
            f"Hay {int(resumen['cuentas_sin_base'])} cuentas sin base comparativa. "
            "Eso requiere entender origen, autorizacion y presentacion, no solo variacion."
        )

    bloques = []
    bloques.append("LECTURA DEL CASO")
    bloques.append(lectura)
    bloques.append("")
    bloques.append("QUE HARIA")
    for i, a in enumerate(acciones, start=1):
        bloques.append(f"{i}. {a}")
    bloques.append("")
    bloques.append("AFIRMACION MAS EXPUESTA")
    bloques.append(", ".join(afirmaciones[:2]) + ".")
    bloques.append("")
    bloques.append("OJO PROFESIONAL")
    bloques.append(ojo_profesional)

    if _requiere_respaldo_normativo(consulta_usuario, contexto):
        bloques.append("")
        bloques.append("RESPALDO NORMATIVO (REFERENCIAL)")
        bloques.append("- NIIF/NIIF para PYMES: reconocimiento, medicion y revelacion del rubro.")
        bloques.append(
            "- NIA 315/330: respuesta a riesgos identificados y diseno de procedimientos."
        )
        bloques.append("- NIA 500: suficiencia y adecuacion de evidencia de auditoria.")

    return "\n".join(bloques)
