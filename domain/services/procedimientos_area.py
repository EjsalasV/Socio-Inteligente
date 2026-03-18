from __future__ import annotations

import sys
from typing import List
from typing import Any

from analysis.lector_tb import leer_trial_balance
from analysis.variaciones import calcular_variaciones, marcar_movimientos_relevantes
from domain.catalogos_python.estructura_ls import obtener_nombre_area_ls
from domain.services.leer_perfil import (
    cargar_perfil,
    obtener_contexto_negocio,
    ruta_tb_cliente,
)
from domain.services.riesgos_area import obtener_area, detectar_riesgos_area


def procedimientos_por_area(codigo_ls: str, perfil: dict, riesgos: list[dict]) -> List[str]:
    """
    Devuelve procedimientos sugeridos por Ã¡rea.
    """
    contexto = obtener_contexto_negocio(perfil)
    procedimientos: List[str] = []

    if codigo_ls == "14":
        procedimientos.extend([
            "Obtener el detalle de inversiones mantenidas al cierre del perÃ­odo.",
            "Verificar el porcentaje de participaciÃ³n en cada entidad participada o subsidiaria.",
            "Solicitar y revisar los estados financieros de las participadas utilizados para el cÃ¡lculo.",
            "Recalcular el valor patrimonial proporcional (VPP) cuando corresponda.",
            "Conciliar los movimientos de inversiones con los resultados reconocidos en el perÃ­odo.",
            "Verificar soporte documental de adquisiciones, aportes, bajas o reclasificaciones.",
            "Evaluar la adecuada presentaciÃ³n y revelaciÃ³n de inversiones en estados financieros.",
        ])

        if contexto.get("tiene_partes_relacionadas"):
            procedimientos.append(
                "Revisar si las inversiones involucran partes relacionadas y validar la adecuada revelaciÃ³n."
            )

        if contexto.get("pertenece_a_grupo"):
            procedimientos.append(
                "Revisar consistencia entre inversiones, subsidiarias, consolidaciÃ³n y patrimonio."
            )

    elif codigo_ls in {"1500", "1501"}:
        procedimientos.extend([
            "Obtener el detalle de ingresos del perÃ­odo por naturaleza y cuenta contable.",
            "Revisar la razonabilidad de variaciones frente al perÃ­odo anterior.",
            "Validar soporte de ingresos significativos o inusuales.",
            "Evaluar si existen ingresos no operativos o asociados a inversiones.",
            "Verificar adecuada clasificaciÃ³n y presentaciÃ³n de ingresos en estados financieros.",
            "Aplicar procedimientos analÃ­ticos y pruebas de detalle sobre partidas relevantes.",
        ])

    elif codigo_ls == "200":
        procedimientos.extend([
            "Obtener el detalle de movimientos patrimoniales del perÃ­odo.",
            "Verificar la composiciÃ³n del patrimonio y su conciliaciÃ³n con el perÃ­odo anterior.",
            "Revisar el tratamiento de utilidad o pÃ©rdida del ejercicio y su reclasificaciÃ³n.",
            "Validar si existieron capitalizaciones, dividendos o ajustes patrimoniales.",
            "Evaluar la adecuada presentaciÃ³n y revelaciÃ³n del patrimonio.",
        ])

        if contexto.get("pertenece_a_grupo"):
            procedimientos.append(
                "Analizar si existen efectos patrimoniales vinculados a inversiones o consolidaciÃ³n."
            )

    elif codigo_ls in {"425", "425.1", "425.2"}:
        procedimientos.extend([
            "Obtener el detalle de cuentas por pagar al cierre del perÃ­odo.",
            "Verificar soporte de saldos significativos o inusuales.",
            "Evaluar la clasificaciÃ³n entre corriente y no corriente.",
            "Revisar pagos posteriores cuando sea aplicable.",
            "Analizar saldos con partes relacionadas, si existen.",
            "Evaluar integridad y revelaciÃ³n del rubro.",
        ])

    elif codigo_ls == "140":
        procedimientos.extend([
            "Obtener conciliaciones bancarias al cierre del perÃ­odo.",
            "Verificar partidas conciliatorias significativas.",
            "Revisar movimientos inusuales de efectivo y sus soportes.",
            "Comparar saldos bancarios con extractos y confirmaciones, si aplica.",
            "Evaluar la razonabilidad de disminuciones o incrementos relevantes.",
        ])

    elif codigo_ls in {"136", "324", "325", "1900"}:
        procedimientos.extend([
            "Obtener conciliaciÃ³n tributaria y auxiliares tributarios del perÃ­odo.",
            "Verificar la composiciÃ³n y soporte de activos/pasivos tributarios.",
            "Revisar cÃ¡lculo del impuesto corriente o diferido, segÃºn aplique.",
            "Evaluar consistencia entre tratamiento contable y tributario.",
            "Verificar adecuada presentaciÃ³n y revelaciÃ³n de rubros tributarios.",
        ])

    elif codigo_ls in {"1600", "1601", "1700", "1701", "1800"}:
        procedimientos.extend([
            "Obtener detalle de gastos por naturaleza.",
            "Revisar variaciones relevantes frente al perÃ­odo anterior.",
            "Verificar soporte documental de gastos significativos o inusuales.",
            "Evaluar clasificaciÃ³n contable de gastos.",
            "Analizar posibles partidas no deducibles tributariamente.",
        ])

    else:
        procedimientos.extend([
            "Obtener el detalle del Ã¡rea y conciliarlo con el TB.",
            "Analizar variaciones significativas frente al perÃ­odo anterior.",
            "Verificar soporte de cuentas relevantes.",
            "Evaluar clasificaciÃ³n, presentaciÃ³n y revelaciÃ³n del Ã¡rea.",
        ])

    titulos_riesgo = {r.get("titulo", "").lower() for r in riesgos}

    if any("partes relacionadas" in t for t in titulos_riesgo):
        procedimientos.append(
            "Revisar condiciones, soporte y revelaciÃ³n de transacciones con partes relacionadas."
        )

    if any("cuentas nuevas" in t or "sin comparativo" in t for t in titulos_riesgo):
        procedimientos.append(
            "Indagar la naturaleza de cuentas nuevas o sin base comparativa y obtener soporte de su origen."
        )

    if any("materialidad" in t for t in titulos_riesgo):
        procedimientos.append(
            "Priorizar pruebas sobre cuentas que explican la mayor parte de la variaciÃ³n del Ã¡rea."
        )

    procedimientos_finales = list(dict.fromkeys(procedimientos))
    return procedimientos_finales


def _inferir_id_procedimiento(descripcion: str, idx: int) -> str:
    texto = str(descripcion).strip().lower()
    reglas = [
        ("confirmacion_clientes", ["confirm", "circular"]),
        ("antiguedad_cartera", ["antig", "cartera"]),
        ("cobranzas_posteriores", ["pagos posteriores", "cobranzas posteriores", "pagos posterior"]),
        ("prueba_corte_ventas", ["corte", "ventas"]),
        ("observacion_inventario", ["inventario", "conteo", "observacion fisica"]),
        ("recalculo_deterioro", ["deterioro", "provision", "incobr"]),
        ("conciliacion_bancaria", ["conciliaciones bancarias", "conciliacion bancaria", "extractos"]),
        ("conciliacion_tributaria", ["conciliacion tributaria", "impuesto", "tributar"]),
        ("analitica_variaciones", ["variaciones", "analitico", "analitica"]),
        ("soporte_transacciones", ["soporte", "transaccion", "documental"]),
    ]

    for proc_id, keywords in reglas:
        if any(k in texto for k in keywords):
            return proc_id

    return f"procedimiento_generico_{idx}"


def procedimientos_por_area_estructurados(
    codigo_ls: str,
    perfil: dict,
    riesgos: list[dict],
    estado_default: str = "planificado",
) -> list[dict[str, Any]]:
    descripciones = procedimientos_por_area(codigo_ls, perfil, riesgos)
    salida: list[dict[str, Any]] = []
    for idx, desc in enumerate(descripciones, start=1):
        salida.append(
            {
                "id": _inferir_id_procedimiento(desc, idx),
                "descripcion": desc,
                "estado": estado_default,
            }
        )
    return salida


def imprimir_procedimientos_area(nombre_cliente: str, codigo_ls: str) -> None:
    perfil = cargar_perfil(nombre_cliente)
    ruta_tb = ruta_tb_cliente(nombre_cliente)

    df_tb = leer_trial_balance(ruta_tb)
    if df_tb.empty:
        print("El TB estÃ¡ vacÃ­o.")
        return

    df_var = calcular_variaciones(df_tb)
    df_var = marcar_movimientos_relevantes(df_var)

    area_df = obtener_area(df_var, codigo_ls)
    if area_df.empty:
        print("Ãrea no encontrada.")
        return

    riesgos = detectar_riesgos_area(area_df, codigo_ls, perfil)
    procedimientos = procedimientos_por_area(codigo_ls, perfil, riesgos)

    print("\n====================================================")
    print(f"PROCEDIMIENTOS SUGERIDOS | {obtener_nombre_area_ls(codigo_ls)} | L/S {codigo_ls}")
    print("====================================================\n")

    for i, proc in enumerate(procedimientos, start=1):
        print(f"{i}. {proc}")


if __name__ == "__main__":
    try:
        if len(sys.argv) < 3:
            raise ValueError(
                "Debes indicar cliente y L/S. "
                "Ejemplo: python motor/procedimientos_area.py bf_holding_2025 14"
            )

        cliente = sys.argv[1]
        codigo_ls = sys.argv[2]

        imprimir_procedimientos_area(cliente, codigo_ls)

    except Exception as e:
        print(f"\nError generando procedimientos del Ã¡rea: {e}")
