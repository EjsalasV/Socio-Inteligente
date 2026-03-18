from __future__ import annotations

import sys
import pandas as pd

from analysis.lector_tb import leer_trial_balance
from analysis.variaciones import calcular_variaciones, marcar_movimientos_relevantes
from core.utils.normalizaciones import normalizar_ls_dataframe
from domain.services.leer_perfil import (
    cargar_perfil,
    obtener_contexto_negocio,
    obtener_riesgo_global,
    obtener_materialidad_ejecucion,
    ruta_tb_cliente,
)
from core.configuracion import obtener_riesgos_config
from core.logger import registrar_ejecucion, registrar_error


def obtener_area(df: pd.DataFrame, codigo_ls: str) -> pd.DataFrame:
    df = normalizar_ls_dataframe(df, columna_ls="ls")
    return df[df["ls"] == codigo_ls].copy()


def top_cuentas_area(area_df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    if area_df.empty:
        return area_df

    area_df = area_df.copy()
    area_df = area_df[area_df["abs_variacion_absoluta"] > 0]

    return area_df.sort_values(
        by="abs_variacion_absoluta",
        ascending=False
    ).head(top_n)


def detectar_riesgos_area(area_df: pd.DataFrame, codigo_ls: str, perfil: dict):
    """
    Detecta riesgos de una area L/S con logica mejorada que considera:
    - Materialidad relativa (variacion como % de materialidad)
    - Contexto del cliente (holding, partes relacionadas, etc.)
    - Cantidad y naturaleza de movimientos

    P5: Implementa calculos relativos en lugar de solo absolutos
    """
    riesgos = []

    contexto = obtener_contexto_negocio(perfil)
    riesgo_global = obtener_riesgo_global(perfil)
    materialidad_ejecucion = float(obtener_materialidad_ejecucion(perfil) or 0)

    # Cargar configuracion de riesgos
    config_riesgos = obtener_riesgos_config()
    config_mat_relativa = config_riesgos.get("materialidad_relativa", {})
    config_cuentas = config_riesgos.get("cuentas_relevantes", {})

    umbral_alto = config_mat_relativa.get("alto", 0.75)
    umbral_medio = config_mat_relativa.get("medio", 0.50)
    umbral_bajo = config_mat_relativa.get("bajo", 0.25)

    cuentas_thresh_alto = config_cuentas.get("alto", 5)
    cuentas_thresh_medio = config_cuentas.get("medio", 3)

    variacion_total = area_df["variacion_absoluta"].sum()
    abs_variacion_total = area_df["abs_variacion_absoluta"].sum()

    cuentas_relevantes = int(area_df["flag_movimiento_relevante"].sum())
    cuentas_sin_base = int(area_df["flag_sin_base"].sum())

    nombres_cuentas = " ".join(
        area_df["nombre_cuenta"].fillna("").astype(str).str.upper().tolist()
    )

    # Riesgo por materialidad RELATIVA (no solo absoluta)
    if materialidad_ejecucion > 0:
        riesgo_relativo = abs_variacion_total / materialidad_ejecucion

        if riesgo_relativo >= umbral_alto:
            riesgos.append({
                "nivel": "ALTO",
                "titulo": "Variacion significativa respecto a materialidad",
                "descripcion":
                    f"La variacion acumulada ({abs_variacion_total:,.2f}) representa el {riesgo_relativo:.1%} "
                    f"de la materialidad de ejecucion ({materialidad_ejecucion:,.2f}). "
                    f"Riesgo ALTO: >= {umbral_alto:.0%}"
            })
        elif riesgo_relativo >= umbral_medio:
            riesgos.append({
                "nivel": "MEDIO",
                "titulo": "Variacion considerable respecto a materialidad",
                "descripcion":
                    f"La variacion acumulada ({abs_variacion_total:,.2f}) representa el {riesgo_relativo:.1%} "
                    f"de la materialidad de ejecucion ({materialidad_ejecucion:,.2f}). "
                    f"Riesgo MEDIO: >= {umbral_medio:.0%}"
            })
        elif riesgo_relativo >= umbral_bajo:
            riesgos.append({
                "nivel": "BAJO",
                "titulo": "Variacion moderada respecto a materialidad",
                "descripcion":
                    f"La variacion acumulada ({abs_variacion_total:,.2f}) representa el {riesgo_relativo:.1%} "
                    f"de la materialidad de ejecucion, requiere atencion rutinaria."
            })

    # Riesgo por cantidad de cuentas relevantes
    if cuentas_relevantes >= cuentas_thresh_alto:
        riesgos.append({
            "nivel": "ALTO",
            "titulo": "Multiples cuentas con movimientos relevantes",
            "descripcion":
                f"Se detectaron {cuentas_relevantes} cuentas relevantes (umbral alto: >= {cuentas_thresh_alto}). "
                f"Requiere revision exhaustiva de cada movimiento."
        })
    elif cuentas_relevantes >= cuentas_thresh_medio:
        riesgos.append({
            "nivel": "MEDIO",
            "titulo": f"{cuentas_relevantes} cuentas con movimientos relevantes",
            "descripcion":
                f"Se detectaron {cuentas_relevantes} cuentas relevantes (umbral medio: >= {cuentas_thresh_medio}). "
                f"Requiere revision selectiva de movimientos."
        })

    if cuentas_sin_base >= 2:
        riesgos.append({
            "nivel": "MEDIO",
            "titulo": "Cuentas nuevas o sin comparativo",
            "descripcion":
                f"El area contiene {cuentas_sin_base} cuentas sin base comparativa. "
                f"Sugiere operaciones nuevas, reclasificaciones o cambios de estructura."
        })

    # Riesgos contextuales (por tipo de cliente)
    actividad = str(contexto.get("actividad_principal", "")).strip().lower()
    descripcion = str(contexto.get("descripcion_breve_negocio", "")).strip().lower()
    sector_cliente = str(perfil.get("cliente", {}).get("sector", "")).strip().lower()
    es_holding = (
        bool(contexto.get("es_holding", False))
        or actividad in {"holding", "holding_sociedad_cartera", "sociedad_cartera"}
        or "holding" in descripcion
        or "sociedad de cartera" in descripcion
        or sector_cliente == "holding"
        or bool(contexto.get("pertenece_a_grupo", False))
    )

    if es_holding and codigo_ls == "14":
        riesgos.append({
            "nivel": "ALTO",
            "titulo": "Riesgo en inversiones de holding",
            "descripcion":
                "La entidad es una holding con subsidiarias y uso de VPP. "
                "Debe evaluarse valuacion, soporte y calculo del valor patrimonial proporcional."
        })

    if contexto.get("tiene_partes_relacionadas", False) and codigo_ls in ["14", "425", "425.1", "425.2", "130.1", "130.2", "35"]:
        riesgos.append({
            "nivel": "ALTO",
            "titulo": "Transacciones con partes relacionadas",
            "descripcion":
                "El cliente presenta partes relacionadas. Deben evaluarse "
                "condiciones de mercado, soporte y adecuadas revelaciones."
        })

    if "VPP" in nombres_cuentas:
        riesgos.append({
            "nivel": "ALTO",
            "titulo": "Aplicacion de metodo VPP",
            "descripcion":
                "Se identifican cuentas asociadas al metodo de participacion patrimonial (VPP). "
                "Debe verificarse calculo y soporte de estados financieros de subsidiarias."
        })

    if riesgo_global.get("nivel", "").lower() in ["medio_alto", "alto"]:
        riesgos.append({
            "nivel": "MEDIO",
            "titulo": "Riesgo global del cliente",
            "descripcion":
                f"El perfil del cliente indica un riesgo global {riesgo_global.get('nivel', 'no especificado')}. "
                f"Esta area hereda riesgo del contexto general."
        })

    return riesgos


def imprimir_riesgos_area(nombre_cliente: str, codigo_ls: str) -> None:
    perfil = cargar_perfil(nombre_cliente)
    ruta_tb = ruta_tb_cliente(nombre_cliente)

    df_tb = leer_trial_balance(ruta_tb)
    if df_tb.empty:
        print("El TB esta vacio.")
        return

    df_var = calcular_variaciones(df_tb)
    df_var = marcar_movimientos_relevantes(df_var)

    area_df = obtener_area(df_var, codigo_ls)

    if area_df.empty:
        print("Area no encontrada.")
        return

    variacion_total = area_df["variacion_absoluta"].sum()
    abs_variacion_total = area_df["abs_variacion_absoluta"].sum()
    cuentas_relevantes = int(area_df["flag_movimiento_relevante"].sum())

    print("\n====================================================")
    print(f"RIESGOS DEL AREA L/S: {codigo_ls}")
    print("====================================================\n")

    print(f"Variacion total: {variacion_total:,.2f}")
    print(f"Variacion acumulada del area: {abs_variacion_total:,.2f}")
    print(f"Cuentas relevantes: {cuentas_relevantes}\n")

    riesgos = detectar_riesgos_area(area_df, codigo_ls, perfil)

    print("Riesgos detectados:\n")

    if not riesgos:
        print("No se detectaron riesgos automaticos con las reglas actuales.\n")
    else:
        for i, r in enumerate(riesgos, 1):
            print(f"{i}. [{r['nivel']}] {r['titulo']}")
            print(f"   {r['descripcion']}\n")

    print("Principales cuentas:\n")

    top = top_cuentas_area(area_df)

    if top.empty:
        print("- No se identificaron cuentas con variacion distinta de cero.")
    else:
        for _, row in top.iterrows():
            print(
                f"- {row['numero_cuenta']} | "
                f"{row['nombre_cuenta']} | "
                f"Variacion: {row['variacion_absoluta']:,.2f}"
            )


if __name__ == "__main__":
    try:
        if len(sys.argv) < 3:
            raise ValueError(
                "Debes indicar cliente y L/S. "
                "Ejemplo: python motor/riesgos_area.py bf_holding_2025 14"
            )

        cliente = sys.argv[1]
        codigo_ls = sys.argv[2]

        print(f"\nLeyendo TB real: {ruta_tb_cliente(cliente)}\n")
        imprimir_riesgos_area(cliente, codigo_ls)

    except Exception as e:
        print(f"\nError generando riesgos por area: {e}")

