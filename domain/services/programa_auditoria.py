from __future__ import annotations

import sys

from analysis.lector_tb import leer_trial_balance
from analysis.variaciones import calcular_variaciones, marcar_movimientos_relevantes
from domain.services.leer_perfil import (
    cargar_perfil,
    obtener_nombre_cliente,
    obtener_periodo,
    obtener_marco_referencial,
    ruta_tb_cliente,
)
from domain.services.riesgos_area import obtener_area, detectar_riesgos_area
from domain.catalogos_python.estructura_ls import obtener_nombre_area_ls
from domain.services.area_briefing import (
    construir_resumen_area,
    construir_lectura_inicial,
    top_cuentas_significativas,
)
from domain.services.procedimientos_area import procedimientos_por_area


def objetivo_area(codigo_ls: str) -> str:
    """
    Devuelve un objetivo general de auditoría por área.
    """
    objetivos = {
        "14": "Verificar la existencia, valuación, presentación y revelación adecuada de las inversiones no corrientes.",
        "140": "Verificar la existencia, integridad y razonabilidad del efectivo y equivalentes de efectivo.",
        "130.1": "Verificar la existencia, recuperabilidad y presentación de las cuentas por cobrar corrientes.",
        "130.2": "Verificar la razonabilidad y clasificación de otras cuentas por cobrar.",
        "35": "Verificar la recuperabilidad y presentación de cuentas por cobrar no corrientes.",
        "110": "Verificar existencia, valuación y presentación de inventarios.",
        "136": "Verificar la razonabilidad y soporte de activos por impuestos corrientes.",
        "15": "Verificar la razonabilidad y sustento de activos por impuestos diferidos.",
        "425": "Verificar integridad, clasificación y presentación de cuentas por pagar.",
        "425.1": "Verificar integridad, clasificación y presentación de cuentas por pagar no corrientes.",
        "425.2": "Verificar integridad, clasificación y presentación de otras cuentas por pagar.",
        "200": "Verificar la composición, movimientos y presentación adecuada del patrimonio.",
        "1500": "Verificar ocurrencia, integridad, corte y presentación adecuada de los ingresos.",
        "1501": "Verificar ocurrencia, integridad y presentación de ingresos financieros u otros ingresos.",
        "1600": "Verificar razonabilidad, clasificación y presentación de gastos administrativos.",
        "1601": "Verificar razonabilidad, clasificación y presentación de gastos financieros.",
        "1700": "Verificar razonabilidad, clasificación y presentación de gastos de ventas u otros ingresos según corresponda.",
        "1701": "Verificar razonabilidad y soporte de gastos de logística.",
        "1800": "Verificar razonabilidad, clasificación y presentación de otros gastos.",
        "1900": "Verificar razonabilidad y soporte del gasto por impuesto a la renta.",
    }

    return objetivos.get(
        codigo_ls,
        f"Verificar la razonabilidad, clasificación, presentación y revelación del área L/S {codigo_ls}."
    )


def imprimir_programa_auditoria(nombre_cliente: str, codigo_ls: str) -> None:
    perfil = cargar_perfil(nombre_cliente)
    ruta_tb = ruta_tb_cliente(nombre_cliente)

    df_tb = leer_trial_balance(ruta_tb)
    if df_tb.empty:
        print("El TB está vacío.")
        return

    df_var = calcular_variaciones(df_tb)
    df_var = marcar_movimientos_relevantes(df_var)

    area_df = obtener_area(df_var, codigo_ls)
    if area_df.empty:
        print("Área no encontrada.")
        return

    cliente = obtener_nombre_cliente(perfil)
    periodo = obtener_periodo(perfil)
    marco = obtener_marco_referencial(perfil)

    resumen = construir_resumen_area(area_df)
    lectura_inicial = construir_lectura_inicial(codigo_ls, area_df, perfil)
    riesgos = detectar_riesgos_area(area_df, codigo_ls, perfil)
    procedimientos = procedimientos_por_area(codigo_ls, perfil, riesgos)
    top = top_cuentas_significativas(area_df, top_n=5)

    print("\n===================================================================")
    print(f"PROGRAMA DE AUDITORÍA | {obtener_nombre_area_ls(codigo_ls)} | L/S {codigo_ls}")
    print("===================================================================\n")

    print(f"Cliente: {cliente}")
    print(f"Periodo: {periodo}")
    print(f"Marco referencial: {marco}\n")

    print("Objetivo del área:")
    print(f"- {objetivo_area(codigo_ls)}\n")

    print("Resumen cuantitativo:")
    print(f"- Número de cuentas: {resumen['cuentas']}")
    print(f"- Saldo anterior agregado: {resumen['saldo_anterior']:,.2f}")
    print(f"- Saldo actual agregado: {resumen['saldo_actual']:,.2f}")
    print(f"- Variación neta: {resumen['variacion_neta']:,.2f}")
    print(f"- Variación acumulada: {resumen['variacion_acumulada']:,.2f}")
    print(f"- Cuentas relevantes: {resumen['cuentas_relevantes']}")
    print(f"- Cuentas sin base comparativa: {resumen['cuentas_sin_base']}\n")

    print("Lectura inicial del área:")
    print(lectura_inicial)
    print()

    print("Riesgos identificados:")
    if not riesgos:
        print("- No se detectaron riesgos automáticos con las reglas actuales.")
    else:
        for r in riesgos:
            print(f"- [{r['nivel']}] {r['titulo']}: {r['descripcion']}")
    print()

    print("Cuentas principales:")
    if top.empty:
        print("- No se identificaron cuentas significativas por variación.")
    else:
        for _, row in top.iterrows():
            print(
                f"- {row['numero_cuenta']} | {row['nombre_cuenta']} | "
                f"Saldo actual: {row['saldo_actual']:,.2f} | "
                f"Variación: {row['variacion_absoluta']:,.2f}"
            )
    print()

    print("Procedimientos sugeridos:")
    for i, proc in enumerate(procedimientos, start=1):
        print(f"{i}. {proc}")
    print()


if __name__ == "__main__":
    try:
        if len(sys.argv) < 3:
            raise ValueError(
                "Debes indicar cliente y L/S. "
                "Ejemplo: python motor/programa_auditoria.py bf_holding_2025 14"
            )

        cliente = sys.argv[1]
        codigo_ls = sys.argv[2]

        imprimir_programa_auditoria(cliente, codigo_ls)

    except Exception as e:
        print(f"\nError generando programa de auditoría: {e}")
