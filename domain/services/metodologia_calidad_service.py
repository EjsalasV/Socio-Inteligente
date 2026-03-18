from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from infra.repositories.catalogo_repository import (
    obtener_area_por_codigo,
    obtener_aseveraciones_sugeridas_por_ls,
)

CATALOGO_PATH = Path(__file__).resolve().parents[2] / "data" / "catalogos" / "metodologia_calidad.yaml"


def _safe_load_yaml(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


_CAT = _safe_load_yaml(CATALOGO_PATH)


def _cat_get(*keys: str, default: Any = None) -> Any:
    cur: Any = _CAT
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return cur if cur is not None else default


def _to_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def _norm(v: Any) -> str:
    return str(v or "").strip().lower()


def _collect_strings(obj: Any) -> str:
    out: list[str] = []

    def rec(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                out.append(str(k))
                rec(v)
        elif isinstance(x, list):
            for item in x:
                rec(item)
        else:
            txt = str(x or "").strip()
            if txt:
                out.append(txt)

    rec(obj)
    return " ".join(out).lower()


def _procedimientos_desde_contexto(ws_context: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(ws_context, dict):
        return []
    proc_df = ws_context.get("proc_df")
    if isinstance(proc_df, pd.DataFrame) and not proc_df.empty:
        return proc_df.to_dict("records")
    procedimientos = ws_context.get("procedimientos", [])
    if isinstance(procedimientos, list):
        return [p for p in procedimientos if isinstance(p, dict)]
    return []


def _texto_operativo(ws_context: dict[str, Any]) -> str:
    manual = ws_context.get("estado_area", {}) if isinstance(ws_context, dict) else {}
    notas = manual.get("notas", []) if isinstance(manual, dict) else []
    pendientes = manual.get("pendientes", []) if isinstance(manual, dict) else []
    conclusion = manual.get("conclusion_preliminar", "") if isinstance(manual, dict) else ""
    cierre = ws_context.get("cierre_texto", "") if isinstance(ws_context, dict) else ""
    parts = []
    if isinstance(notas, list):
        parts.extend([str(x) for x in notas])
    if isinstance(pendientes, list):
        parts.extend([str(x) for x in pendientes])
    parts.append(str(conclusion))
    parts.append(str(cierre))
    return " ".join(parts).lower()


def _area_nombre(ws_context: dict[str, Any]) -> str:
    return str(ws_context.get("area_name", ws_context.get("nombre", "")) or "").strip()


def _is_revenue_area(codigo_ls: str, area_name: str) -> bool:
    ingresos_codigos = set(_cat_get("grupos_area", "ingresos_codigos", default=["1500", "1501", "1700_ALT"]))
    code = str(codigo_ls).strip()
    txt = _norm(area_name)
    return code in ingresos_codigos or any(k in txt for k in ["ingres", "venta", "revenue"])


def _is_expense_area(codigo_ls: str, area_name: str) -> bool:
    gastos_codigos = set(_cat_get("grupos_area", "gastos_codigos", default=["1600", "1600.5", "1601", "1700", "1701", "1800", "1900"]))
    code = str(codigo_ls).strip()
    txt = _norm(area_name)
    return code in gastos_codigos or any(k in txt for k in ["gasto", "cost"])


def _is_estimate_area(codigo_ls: str, area_name: str) -> bool:
    estim_codigos = set(_cat_get("grupos_area", "estimaciones_codigos", default=["130.1", "110", "15", "325", "415", "420"]))
    code = str(codigo_ls).strip()
    txt = _norm(area_name)
    return code in estim_codigos or any(k in txt for k in ["estim", "deterioro", "provision", "incobr", "impuesto diferido", "actuar"])


def _is_holding_profile(perfil: dict[str, Any]) -> bool:
    if not isinstance(perfil, dict):
        return False
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    contexto = perfil.get("contexto_negocio", {}) if isinstance(perfil.get("contexto_negocio"), dict) else {}
    industria = perfil.get("industria_inteligente", {}) if isinstance(perfil.get("industria_inteligente"), dict) else {}
    blob = " ".join(
        [
            str(cliente.get("sector", "")),
            str(cliente.get("subsector", "")),
            str(contexto.get("actividad_principal", "")),
            str(industria.get("sector_base", "")),
            str(industria.get("subtipo_negocio", "")),
        ]
    ).lower()
    return "holding" in blob or "sociedad_cartera" in blob or "cartera" in blob


def _alerta(codigo: str, nivel: str, mensaje: str, critica: bool = False, detalle: str = "") -> dict[str, Any]:
    return {
        "codigo": codigo,
        "nivel": nivel,
        "critica": bool(critica),
        "mensaje": mensaje,
        "detalle": detalle,
    }


def evaluar_rim_fraude(cliente: str, perfil: dict[str, Any] | None, contexto: dict[str, Any] | None) -> dict[str, Any]:
    perfil = perfil or {}
    contexto = contexto or {}
    corpus = _collect_strings({"perfil": perfil, "contexto": contexto})
    rebut_keywords = [str(x).lower() for x in _cat_get("palabras_clave", "rebuttal", default=[])]

    riesgos_ingresos = [str(x).lower() for x in _cat_get("fraude_presunto", "ingresos", default=["reconocimiento de ingresos"])]
    riesgos_gerencia = [str(x).lower() for x in _cat_get("fraude_presunto", "gerencia", default=["evasion de controles por parte de la gerencia"])]

    ingresos_presente = any(k in corpus for k in riesgos_ingresos) or "fraude" in corpus and "ingres" in corpus
    gerencia_presente = any(k in corpus for k in riesgos_gerencia) or ("gerencia" in corpus and ("control" in corpus or "override" in corpus))

    rebut_ing = any(k in corpus and "ingres" in corpus for k in rebut_keywords)
    rebut_ger = any(k in corpus and "gerencia" in corpus for k in rebut_keywords)

    alertas: list[dict[str, Any]] = []
    if not ingresos_presente and not rebut_ing:
        alertas.append(
            _alerta(
                "rim_fraude_ingresos_ausente",
                "alto",
                "No se evidencia RIM de fraude por reconocimiento de ingresos ni rebuttal documentado.",
                critica=True,
            )
        )
    if not gerencia_presente and not rebut_ger:
        alertas.append(
            _alerta(
                "rim_fraude_gerencia_ausente",
                "alto",
                "No se evidencia riesgo de evasion de controles por gerencia ni rebuttal documentado.",
                critica=True,
            )
        )

    return {
        "cliente": cliente,
        "ingresos_presente": ingresos_presente,
        "gerencia_presente": gerencia_presente,
        "rebuttal_ingresos": rebut_ing,
        "rebuttal_gerencia": rebut_ger,
        "alertas": alertas,
    }


def evaluar_requerimiento_procedimientos_por_materialidad(
    codigo_ls: str,
    ws_context: dict[str, Any],
    rim_eval: dict[str, Any] | None = None,
) -> dict[str, Any]:
    procedimientos = _procedimientos_desde_contexto(ws_context)
    proc_count = len(procedimientos)

    saldo = _to_float(ws_context.get("saldo_total", ws_context.get("area_summary", {}).get("saldo_actual", 0)))
    materialidad_ejecucion = _to_float(ws_context.get("materialidad_ejecucion", 0))
    area_name = _area_nombre(ws_context)
    es_ingresos = _is_revenue_area(codigo_ls, area_name)

    material = materialidad_ejecucion > 0 and saldo >= materialidad_ejecucion
    riesgo_fraude_relacionado = bool(es_ingresos and rim_eval and rim_eval.get("ingresos_presente", False))

    alertas: list[dict[str, Any]] = []
    if material and proc_count == 0:
        alertas.append(
            _alerta(
                "proc_materialidad_faltante",
                "alto",
                "Area material (saldo >= materialidad de ejecucion) sin procedimientos/papeles clave.",
                critica=True,
            )
        )
    if riesgo_fraude_relacionado and proc_count == 0:
        alertas.append(
            _alerta(
                "proc_fraude_faltante",
                "alto",
                "Area asociada a riesgo de fraude sin procedimientos/papeles definidos.",
                critica=True,
            )
        )

    return {
        "es_material": material,
        "saldo_area": saldo,
        "materialidad_ejecucion": materialidad_ejecucion,
        "riesgo_fraude_relacionado": riesgo_fraude_relacionado,
        "procedimientos_count": proc_count,
        "alertas": alertas,
    }


def evaluar_pruebas_control_y_recorrido(ws_context: dict[str, Any]) -> dict[str, Any]:
    procedimientos = _procedimientos_desde_contexto(ws_context)
    texto_operativo = _texto_operativo(ws_context)

    control_kw = [str(x).lower() for x in _cat_get("palabras_clave", "control_walkthrough", default=[])]
    soporte_kw = [str(x).lower() for x in _cat_get("palabras_clave", "soporte_control_walkthrough", default=[])]

    texto_proc = " ".join(
        [
            f"{str(p.get('descripcion', ''))} {str(p.get('id', ''))} {str(p.get('estado', ''))}".lower()
            for p in procedimientos
        ]
    )
    hay_control_o_walkthrough = any(k in texto_proc for k in control_kw)

    corpus = f"{texto_proc} {texto_operativo}"
    tiene_soporte_base = any(k in corpus for k in soporte_kw)

    alertas: list[dict[str, Any]] = []
    if hay_control_o_walkthrough and not tiene_soporte_base:
        alertas.append(
            _alerta(
                "control_walkthrough_sin_base",
                "alto",
                "Se detectan pruebas de control/recorrido sin evidencia de base de muestra o transaccion identificada.",
                critica=True,
            )
        )

    return {
        "hay_control_o_walkthrough": hay_control_o_walkthrough,
        "tiene_soporte_base": tiene_soporte_base,
        "alertas": alertas,
    }


def evaluar_ingresos_metodologia(codigo_ls: str, ws_context: dict[str, Any], perfil: dict[str, Any] | None) -> dict[str, Any]:
    perfil = perfil or {}
    area_name = _area_nombre(ws_context)
    aplica = _is_revenue_area(codigo_ls, area_name)
    if not aplica:
        return {"aplica": False, "marco": "no_aplica", "checklist": [], "faltantes": [], "alertas": []}

    procedimientos = _procedimientos_desde_contexto(ws_context)
    texto = " ".join([str(p.get("descripcion", "")) for p in procedimientos]).lower() + " " + _texto_operativo(ws_context)
    marco = _norm(perfil.get("encargo", {}).get("marco_referencial", ""))

    niif_completas = "completa" in marco and "pyme" not in marco
    if niif_completas:
        checklist = [str(x) for x in _cat_get("palabras_clave", "ingresos_niif_completas", default=[])]
    else:
        checklist = [str(x) for x in _cat_get("palabras_clave", "ingresos_pymes", default=[])]

    faltantes = [item for item in checklist if item.lower() not in texto]
    alertas: list[dict[str, Any]] = []
    if faltantes:
        alertas.append(
            _alerta(
                "ingresos_metodologia_incompleta",
                "medio",
                "La revision de ingresos no evidencia todos los elementos metodologicos esperados.",
                critica=False,
                detalle=f"Faltantes: {', '.join(faltantes)}",
            )
        )

    return {
        "aplica": True,
        "marco": "niif_completas" if niif_completas else "niif_pymes",
        "checklist": checklist,
        "faltantes": faltantes,
        "alertas": alertas,
    }


def evaluar_gastos_metodologia(codigo_ls: str, ws_context: dict[str, Any]) -> dict[str, Any]:
    area_name = _area_nombre(ws_context)
    aplica = _is_expense_area(codigo_ls, area_name)
    if not aplica:
        return {"aplica": False, "tiene_resumen_cruce": False, "alertas": []}

    texto = _texto_operativo(ws_context)
    resumen_kw = [str(x).lower() for x in _cat_get("palabras_clave", "resumen_gastos", default=[])]
    tiene_resumen_cruce = any(k in texto for k in resumen_kw)

    saldo = _to_float(ws_context.get("saldo_total", ws_context.get("area_summary", {}).get("saldo_actual", 0)))
    materialidad_ejecucion = _to_float(ws_context.get("materialidad_ejecucion", 0))
    pending_count = int(ws_context.get("pending_count", 0) or 0)

    alertas: list[dict[str, Any]] = []
    if not tiene_resumen_cruce:
        alertas.append(
            _alerta(
                "gastos_sin_resumen_cruce",
                "medio",
                "No se evidencia resumen/cruce de gastos con otras cuentas o ciclos.",
                critica=False,
            )
        )
    if materialidad_ejecucion > 0 and saldo >= materialidad_ejecucion and pending_count > 0:
        alertas.append(
            _alerta(
                "gastos_materiales_pendientes",
                "alto",
                "Existen gastos materiales con pendientes sin evidencia de prueba suficiente.",
                critica=True,
            )
        )

    return {
        "aplica": True,
        "tiene_resumen_cruce": tiene_resumen_cruce,
        "saldo_area": saldo,
        "materialidad_ejecucion": materialidad_ejecucion,
        "pending_count": pending_count,
        "alertas": alertas,
    }


def evaluar_estimaciones_nia540(codigo_ls: str, ws_context: dict[str, Any]) -> dict[str, Any]:
    area_name = _area_nombre(ws_context)
    aplica = _is_estimate_area(codigo_ls, area_name)
    if not aplica:
        return {"aplica": False, "checklist": [], "enfoques_detectados": [], "alertas": []}

    procedimientos = _procedimientos_desde_contexto(ws_context)
    texto = " ".join([str(p.get("descripcion", "")) for p in procedimientos]).lower() + " " + _texto_operativo(ws_context)
    checklist = [str(x) for x in _cat_get("palabras_clave", "nia540_enfoques", default=[])]
    enfoques_detectados = [k for k in checklist if k.lower() in texto]

    alertas: list[dict[str, Any]] = []
    if not enfoques_detectados:
        alertas.append(
            _alerta(
                "nia540_sin_enfoque",
                "alto",
                "Area de estimaciones sin evidencia de enfoques NIA 540 (proceso gerencia, estimacion auditor o hechos posteriores).",
                critica=True,
            )
        )

    return {
        "aplica": True,
        "checklist": checklist,
        "enfoques_detectados": enfoques_detectados,
        "alertas": alertas,
        "sugerencias": [
            "Aplicar procedimientos sustantivos sobre supuestos y calculos.",
            "Evaluar pruebas de control cuando los controles soporten la estimacion.",
        ],
    }


def evaluar_sensibilidad_holding(codigo_ls: str, ws_context: dict[str, Any], perfil: dict[str, Any] | None) -> dict[str, Any]:
    perfil = perfil or {}
    if not _is_holding_profile(perfil):
        return {"aplica": False, "observaciones": [], "alertas": []}

    code = str(codigo_ls).strip()
    saldo = _to_float(ws_context.get("saldo_total", ws_context.get("area_summary", {}).get("saldo_actual", 0)))
    observaciones: list[str] = []
    alertas: list[dict[str, Any]] = []

    if code == "14":
        observaciones.extend(
            [
                "Holding: validar VPP/metodo de participacion cuando aplique.",
                "Holding: contrastar movimientos de inversiones con informacion de participadas.",
            ]
        )
    elif code == "200":
        observaciones.extend(
            [
                "Holding: revisar enlace entre resultados del periodo, VPP y patrimonio.",
                "Holding: verificar soporte de movimientos patrimoniales.",
            ]
        )
    elif code == "425.2":
        observaciones.extend(
            [
                "Holding: evaluar si saldos por pagar tienen naturaleza de relacionadas.",
                "Holding: revisar condiciones de cancelacion y revelacion.",
            ]
        )
    elif code == "1600":
        observaciones.extend(
            [
                "Holding: validar consistencia de gastos administrativos con estructura operativa limitada.",
                "Holding: revisar cargos centralizados/intercompanias.",
            ]
        )
    elif code == "1500":
        if abs(saldo) <= 0.01:
            observaciones.append("Holding: ingresos con saldo cero no deben sobre-priorizarse por monto.")
        else:
            observaciones.append("Holding: distinguir ingreso operativo vs financiero/VPP/otros.")

    return {"aplica": True, "observaciones": observaciones, "alertas": alertas}


def obtener_aseveraciones_guia_por_area_o_grupo(codigo_ls: str, area_nombre: str = "") -> dict[str, Any]:
    """
    Compatibilidad de nombre legacy:
    ahora resuelve guia por codigo LS directamente, sin renombrar areas.
    """
    codigo = str(codigo_ls).strip()
    guia = obtener_aseveraciones_sugeridas_por_ls(codigo)
    area = obtener_area_por_codigo(codigo) or {}

    titulo = ""
    if isinstance(guia, dict):
        titulo = str(guia.get("titulo_ls", "")).strip()
    if not titulo:
        titulo = str(area.get("titulo", "")).strip() or (str(area_nombre).strip() if area_nombre else f"LS {codigo}")

    if not isinstance(guia, dict):
        return {
            "codigo_ls": codigo,
            "titulo_ls": titulo,
            "aseveraciones_sugeridas": [],
            "nota": "Sin guia especifica disponible",
        }

    asev = guia.get("aseveraciones_sugeridas", [])
    if not isinstance(asev, list):
        asev = []
    nota = str(guia.get("nota", "")).strip() or "Guia referencial, no exhaustiva."
    return {
        "codigo_ls": codigo,
        "titulo_ls": titulo,
        "aseveraciones_sugeridas": [str(x) for x in asev if str(x).strip()],
        "nota": nota,
    }


def evaluar_alertas_metodologia(cliente: str, codigo_ls: str, ws_context: dict[str, Any]) -> dict[str, Any]:
    ws_context = ws_context or {}
    perfil = ws_context.get("perfil", {}) if isinstance(ws_context, dict) else {}
    contexto = ws_context.get("contexto", perfil)

    rim = evaluar_rim_fraude(cliente, perfil, contexto)
    req_proc = evaluar_requerimiento_procedimientos_por_materialidad(codigo_ls, ws_context, rim_eval=rim)
    ctrl_walk = evaluar_pruebas_control_y_recorrido(ws_context)
    ingresos = evaluar_ingresos_metodologia(codigo_ls, ws_context, perfil)
    gastos = evaluar_gastos_metodologia(codigo_ls, ws_context)
    est = evaluar_estimaciones_nia540(codigo_ls, ws_context)
    holding = evaluar_sensibilidad_holding(codigo_ls, ws_context, perfil)
    asev = obtener_aseveraciones_guia_por_area_o_grupo(codigo_ls, _area_nombre(ws_context))

    alertas = []
    for bloque in [rim, req_proc, ctrl_walk, ingresos, gastos, est, holding]:
        for a in bloque.get("alertas", []) if isinstance(bloque, dict) else []:
            if isinstance(a, dict):
                alertas.append(a)

    criticas = [a for a in alertas if bool(a.get("critica"))]
    resumen = {
        "total_alertas": len(alertas),
        "alertas_criticas": len(criticas),
        "estado_general": "bloqueado" if criticas else ("con_alertas" if alertas else "ok"),
    }

    return {
        "cliente": cliente,
        "codigo_ls": str(codigo_ls),
        "rim_fraude": rim,
        "procedimientos_materialidad": req_proc,
        "pruebas_control_walkthrough": ctrl_walk,
        "ingresos_metodologia": ingresos,
        "gastos_metodologia": gastos,
        "estimaciones_nia540": est,
        "holding_sensibilidad": holding,
        "aseveraciones_guia": asev.get("aseveraciones_sugeridas", []),
        "aseveraciones_guia_detalle": asev,
        "alertas": alertas,
        "alertas_criticas": criticas,
        "resumen": resumen,
    }

