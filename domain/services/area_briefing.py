from __future__ import annotations

from typing import Any

import pandas as pd

from domain.services.leer_perfil import (
    obtener_contexto_negocio,
    obtener_materialidad_final,
)


def _sum_col(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0.0).sum())


def _count_true(df: pd.DataFrame, col: str) -> int:
    if col not in df.columns:
        return 0
    return int(df[col].fillna(False).astype(bool).sum())


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


def construir_resumen_area(area_df: pd.DataFrame) -> dict:
    area_df = area_df.copy() if isinstance(area_df, pd.DataFrame) else pd.DataFrame()
    return {
        "cuentas": int(len(area_df)),
        "saldo_anterior": _sum_col(area_df, "saldo_anterior"),
        "saldo_actual": _sum_col(area_df, "saldo_actual"),
        "variacion_neta": _sum_col(area_df, "variacion_absoluta"),
        "variacion_acumulada": _sum_col(area_df, "abs_variacion_absoluta"),
        "cuentas_relevantes": _count_true(area_df, "flag_movimiento_relevante"),
        "cuentas_sin_base": _count_true(area_df, "flag_sin_base"),
    }


def top_cuentas_significativas(area_df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    area_df = area_df.copy() if isinstance(area_df, pd.DataFrame) else pd.DataFrame()
    if area_df.empty:
        return area_df
    if "abs_variacion_absoluta" not in area_df.columns:
        return area_df.head(top_n)
    area_df = area_df[pd.to_numeric(area_df["abs_variacion_absoluta"], errors="coerce").fillna(0.0) > 0].copy()
    if area_df.empty:
        return area_df
    return area_df.sort_values(by="abs_variacion_absoluta", ascending=False).head(top_n)


def construir_foco_holding(codigo_ls: str, perfil: dict, area_df: pd.DataFrame | None = None) -> list[str]:
    if not _is_holding_profile(perfil):
        return []

    code = str(codigo_ls).strip()
    focos: list[str] = []

    if code == "14":
        focos.extend(
            [
                "Revisar aplicacion del metodo de participacion patrimonial (VPP) cuando corresponda.",
                "Validar composicion de inversiones y soporte de valuacion.",
                "Conciliar movimientos del periodo con informacion financiera de participadas.",
                "Verificar presentacion y revelacion de inversiones no corrientes.",
            ]
        )
    elif code == "200":
        focos.extend(
            [
                "Validar consistencia entre utilidades/perdidas acumuladas y resultados del periodo.",
                "Revisar soporte de movimientos patrimoniales y su vinculo con efectos VPP.",
                "Confirmar adecuada presentacion del patrimonio en estados financieros.",
            ]
        )
    elif code == "425.2":
        focos.extend(
            [
                "Analizar naturaleza de saldos por pagar y posible relacion con partes relacionadas.",
                "Revisar origen, condiciones y expectativa de cancelacion.",
                "Evaluar clasificacion corriente/no corriente y revelaciones.",
            ]
        )
    elif code == "1600":
        focos.extend(
            [
                "Evaluar gastos administrativos propios de estructura holding.",
                "Revisar servicios centralizados y posibles cargos intercompanias.",
                "Contrastar nivel de gasto con la naturaleza operativa limitada de una holding.",
            ]
        )
    elif code == "1500":
        focos.extend(
            [
                "Si el saldo es cero, evitar sobre-priorizacion por monto.",
                "Si hay movimientos, distinguir ingresos operativos vs financieros/VPP/otros.",
                "Validar coherencia de la naturaleza del ingreso con una estructura holding.",
            ]
        )

    return focos


def construir_lectura_inicial(codigo_ls: str, area_df: pd.DataFrame, perfil: dict) -> str:
    resumen = construir_resumen_area(area_df)
    contexto = obtener_contexto_negocio(perfil) or {}
    materialidad_final = obtener_materialidad_final(perfil) or {}
    mat_ejec = float(materialidad_final.get("materialidad_ejecucion") or 0.0)

    partes: list[str] = []
    partes.append(
        f"El area L/S {codigo_ls} presenta {resumen['cuentas']} cuentas, saldo actual agregado de "
        f"{resumen['saldo_actual']:,.2f}, variacion neta de {resumen['variacion_neta']:,.2f} "
        f"y variacion acumulada de {resumen['variacion_acumulada']:,.2f}."
    )

    if mat_ejec > 0:
        if resumen["variacion_acumulada"] >= mat_ejec:
            partes.append(
                f"La variacion acumulada supera la materialidad de ejecucion ({mat_ejec:,.2f}), por lo que requiere atencion prioritaria."
            )
        else:
            partes.append(
                f"La variacion acumulada no supera la materialidad de ejecucion ({mat_ejec:,.2f}), pero puede seguir siendo sensible por su composicion."
            )

    if resumen["cuentas_relevantes"] > 0:
        partes.append(f"Se detectan {resumen['cuentas_relevantes']} cuentas con movimiento relevante.")

    if resumen["cuentas_sin_base"] > 0:
        partes.append(f"Existen {resumen['cuentas_sin_base']} cuentas sin base comparativa.")

    if _is_holding_profile(perfil) and str(codigo_ls).strip() in {"14", "200", "425.2", "1600", "1500"}:
        partes.append(
            "Por naturaleza holding, el analisis debe enfatizar relaciones con inversiones, patrimonio, relacionadas y consistencia de presentacion."
        )

    if bool(contexto.get("tiene_partes_relacionadas")) and str(codigo_ls).strip() in {"14", "425", "425.1", "425.2", "200"}:
        partes.append("La presencia de partes relacionadas incrementa la necesidad de revisar condiciones y revelaciones.")

    return " ".join(partes)


def construir_foco_auditoria(codigo_ls: str, perfil: dict, area_df: pd.DataFrame) -> list[str]:
    code = str(codigo_ls).strip()
    contexto = obtener_contexto_negocio(perfil) or {}
    focos: list[str] = []

    if code == "14":
        focos.extend(
            [
                "Verificar medicion y soporte de inversiones.",
                "Revisar aplicacion del metodo VPP cuando corresponda.",
                "Contrastar movimientos con estados financieros de participadas.",
                "Evaluar consistencia entre inversiones, resultados asociados y patrimonio.",
            ]
        )
    elif code in {"1500", "1501"}:
        focos.extend(
            [
                "Analizar naturaleza de ingresos y su presentacion.",
                "Revisar si existen ingresos no operativos o asociados a inversiones.",
                "Aplicar pruebas de corte, ocurrencia y soporte.",
            ]
        )
    elif code == "200":
        focos.extend(
            [
                "Revisar composicion del patrimonio y naturaleza de movimientos.",
                "Validar tratamiento de utilidad/perdida y reclasificaciones.",
                "Evaluar efectos de inversiones/relacionadas en patrimonio.",
            ]
        )
    elif code in {"425", "425.1", "425.2"}:
        focos.extend(
            [
                "Revisar integridad de cuentas por pagar y clasificacion corriente/no corriente.",
                "Verificar soporte de obligaciones nuevas o inusuales.",
                "Analizar saldos con relacionadas cuando existan.",
            ]
        )
    elif code == "140":
        focos.extend(
            [
                "Revisar conciliaciones bancarias y movimientos relevantes.",
                "Validar soporte de variaciones significativas en efectivo.",
            ]
        )
    elif code in {"136", "324", "325", "1900", "15"}:
        focos.extend(
            [
                "Analizar razonabilidad de saldos tributarios.",
                "Conciliar tratamiento contable y tributario.",
                "Verificar calculo y soporte de impuestos corriente/diferido.",
            ]
        )
    else:
        focos.extend(
            [
                "Revisar cuentas con mayor variacion del area.",
                "Validar soporte, clasificacion y consistencia de saldos.",
                "Considerar impacto en presentacion y revelacion.",
            ]
        )

    if bool(contexto.get("tiene_partes_relacionadas")) and code in {"14", "425", "425.1", "425.2", "200"}:
        focos.append("Reforzar analisis de condiciones y revelacion de transacciones con relacionadas.")

    # Integra foco holding de forma incremental.
    focos.extend(construir_foco_holding(code, perfil, area_df))
    return list(dict.fromkeys([f for f in focos if str(f).strip()]))

