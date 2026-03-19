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
    Devuelve procedimientos sugeridos por área.
    """
    contexto = obtener_contexto_negocio(perfil)
    procedimientos: List[str] = []

    if codigo_ls == "14":
        procedimientos.extend([
            "Obtener el detalle de inversiones mantenidas al cierre del período.",
            "Verificar el porcentaje de participación en cada entidad participada o subsidiaria.",
            "Solicitar y revisar los estados financieros de las participadas utilizados para el cálculo.",
            "Recalcular el valor patrimonial proporcional (VPP) cuando corresponda.",
            "Conciliar los movimientos de inversiones con los resultados reconocidos en el período.",
            "Verificar soporte documental de adquisiciones, aportes, bajas o reclasificaciones.",
            "Evaluar la adecuada presentación y revelación de inversiones en estados financieros.",
        ])

        if contexto.get("tiene_partes_relacionadas"):
            procedimientos.append(
                "Revisar si las inversiones involucran partes relacionadas y validar la adecuada revelación."
            )

        if contexto.get("pertenece_a_grupo"):
            procedimientos.append(
                "Revisar consistencia entre inversiones, subsidiarias, consolidación y patrimonio."
            )

    elif codigo_ls in {"1500", "1501"}:
        procedimientos.extend([
            "Obtener el detalle de ingresos del período por naturaleza y cuenta contable.",
            "Revisar la razonabilidad de variaciones frente al período anterior.",
            "Validar soporte de ingresos significativos o inusuales.",
            "Evaluar si existen ingresos no operativos o asociados a inversiones.",
            "Verificar adecuada clasificación y presentación de ingresos en estados financieros.",
            "Aplicar procedimientos analíticos y pruebas de detalle sobre partidas relevantes.",
        ])

    elif codigo_ls == "200":
        procedimientos.extend([
            "Obtener el detalle de movimientos patrimoniales del período.",
            "Verificar la composición del patrimonio y su conciliación con el período anterior.",
            "Revisar el tratamiento de utilidad o pérdida del ejercicio y su reclasificación.",
            "Validar si existieron capitalizaciones, dividendos o ajustes patrimoniales.",
            "Evaluar la adecuada presentación y revelación del patrimonio.",
        ])

        if contexto.get("pertenece_a_grupo"):
            procedimientos.append(
                "Analizar si existen efectos patrimoniales vinculados a inversiones o consolidación."
            )

    elif codigo_ls in {"425", "425.1", "425.2"}:
        procedimientos.extend([
            "Obtener el detalle de cuentas por pagar al cierre del período.",
            "Verificar soporte de saldos significativos o inusuales.",
            "Evaluar la clasificación entre corriente y no corriente.",
            "Revisar pagos posteriores cuando sea aplicable.",
            "Analizar saldos con partes relacionadas, si existen.",
            "Evaluar integridad y revelación del rubro.",
        ])

    elif codigo_ls == "140":
        procedimientos.extend([
            "Obtener conciliaciones bancarias al cierre del período.",
            "Verificar partidas conciliatorias significativas.",
            "Revisar movimientos inusuales de efectivo y sus soportes.",
            "Comparar saldos bancarios con extractos y confirmaciones, si aplica.",
            "Evaluar la razonabilidad de disminuciones o incrementos relevantes.",
        ])

    elif codigo_ls in {"136", "324", "325", "1900"}:
        procedimientos.extend([
            "Obtener conciliación tributaria y auxiliares tributarios del período.",
            "Verificar la composición y soporte de activos/pasivos tributarios.",
            "Revisar cálculo del impuesto corriente o diferido, según aplique.",
            "Evaluar consistencia entre tratamiento contable y tributario.",
            "Verificar adecuada presentación y revelación de rubros tributarios.",
        ])

    elif codigo_ls in {"1600", "1601", "1700", "1701", "1800"}:
        procedimientos.extend([
            "Obtener detalle de gastos por naturaleza.",
            "Revisar variaciones relevantes frente al período anterior.",
            "Verificar soporte documental de gastos significativos o inusuales.",
            "Evaluar clasificación contable de gastos.",
            "Analizar posibles partidas no deducibles tributariamente.",
        ])

    else:
        procedimientos.extend([
            "Obtener el detalle del área y conciliarlo con el TB.",
            "Analizar variaciones significativas frente al período anterior.",
            "Verificar soporte de cuentas relevantes.",
            "Evaluar clasificación, presentación y revelación del área.",
        ])

    titulos_riesgo = {r.get("titulo", "").lower() for r in riesgos}

    if any("partes relacionadas" in t for t in titulos_riesgo):
        procedimientos.append(
            "Revisar condiciones, soporte y revelación de transacciones con partes relacionadas."
        )

    if any("cuentas nuevas" in t or "sin comparativo" in t for t in titulos_riesgo):
        procedimientos.append(
            "Indagar la naturaleza de cuentas nuevas o sin base comparativa y obtener soporte de su origen."
        )

    if any("materialidad" in t for t in titulos_riesgo):
        procedimientos.append(
            "Priorizar pruebas sobre cuentas que explican la mayor parte de la variación del área."
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
        print("El TB está vacío.")
        return

    df_var = calcular_variaciones(df_tb)
    df_var = marcar_movimientos_relevantes(df_var)

    area_df = obtener_area(df_var, codigo_ls)
    if area_df.empty:
        print("Área no encontrada.")
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
        print(f"\nError generando procedimientos del área: {e}")
