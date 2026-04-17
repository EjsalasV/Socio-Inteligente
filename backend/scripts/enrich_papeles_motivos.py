#!/usr/bin/env python3
"""
Script para enriquecer las descripciones de papeles con MOTIVO auditor
(POR QUÉ se audita esto, no CÓMO se audita)
"""
import json
from pathlib import Path

# MOTIVOS AUDITOR - POR QUÉ se audita cada papel
MOTIVOS_PAPELES = {
    # EFECTIVO (140)
    "140.03": "Validar que los saldos bancarios en libros coinciden con los estados de los bancos, identificar partidas conciliatorias",
    "140.04": "Investigar diferencias entre saldos en libros y estados bancarios para detectar errores o fraude",
    "140.05": "Verificar que solo personas autorizadas pueden hacer operaciones de efectivo",
    "140.06": "Validar que todos los egresos de efectivo están registrados correctamente en el período",
    "140.07": "Validar que todos los ingresos de efectivo están registrados correctamente en el período",
    "140.08": "Evaluar si las inversiones temporales cumplen criterios NIIF y están valuadas correctamente",
    "140.09": "Validar físicamente que existe el efectivo en caja según saldo contable",
    "140.10": "Asegurar que los anticipos a empleados están documentados y son recaudables",

    # CUENTAS POR COBRAR (130)
    "130.03": "Validar que el saldo total de CXC en libros coincide con la suma detallada de clientes",
    "130.04": "Evaluar el riesgo de cobranza identificando saldos vencidos por período",
    "130.05": "Identificar dependencia en pocos clientes (concentración de riesgo)",
    "130.06": "Aplicar metodología NIIF 9 para evaluar si CXC debe estar a valor presente",
    "130.07": "Confirmar directamente con clientes principales que los saldos en libros son correctos",
    "130.08": "Evaluar cobranzas posteriores al cierre para validar existencia de CXC",
    "130.09": "Determinar si hay pérdidas crediticias esperadas que requieren provisión",

    # INVENTARIOS (110)
    "110.03": "Validar que los movimientos de entrada y salida concuerdan con compras y costo de ventas",
    "110.04": "Conciliar detalle de inventarios contra saldo general",
    "110.05": "Muestrear documentación de compras locales para validar precio y cantidad",
    "110.06": "Validar documentación de importaciones: aduanal, aranceles, costos",
    "110.07": "Identificar inventario que no se mueve para evaluar obsolescencia",
    "110.08": "Evaluar si valor de mercado está por debajo de costo (aplicar NRV test)",

    # IMPUESTOS ACTIVO (136)
    "136.03": "Validar que movimientos de crédito tributario son correctos",
    "136.04": "Conciliar compras de IVA/RET contra formularios declarados",
    "136.05": "Validar derecho a crédito por ISD vs documentación de operaciones",
    "136.06": "Verificar que proveedores existen realmente (validar CUIT/RUC)",
    "136.07": "Evaluar que crédito tributario no ha expirado por antigüedad",

    # PPE (1)
    "1.03": "Validar que adiciones a PPE están autorizadas y capitalizadas correctamente",
    "1.04": "Verificar que depreciación acumulada se calcula correctamente por activo",
    "1.05": "Muestrear compras de activos para validar clasificación y fecha inicio depreciación",
    "1.06": "Evaluar si bienes inmuebles están correctamente clasificados (inverso vs operativo)",
    "1.07": "Validar que la firma tiene escritura registrada para bienes inmuebles",
    "1.08": "Validar que ventas de PPE están registradas correctamente (ganancia/pérdida)",

    # PROPIEDADES INVERSIÓN (5)
    "5.03": "Validar movimientos de propiedades de inversión en el período",
    "5.04": "Verificar que valor razonable está apropiadamente evaluado",

    # INTANGIBLES (10)
    "10.03": "Validar movimientos de activos intangibles adquiridos o desarrollados",
    "10.04": "Verificar que amortización se calcula en base a vida útil correcta",

    # DERECHO DE USO (11)
    "11.03": "Validar que arrendamientos se clasifican correctamente bajo NIIF 16",

    # INVERSIONES EN ACCIONES (20)
    "20.03": "Evaluar que inversiones se valúan a costo o valor de mercado según clasificación",

    # PATRIMONIO (200)
    "200.03": "Validar que capital reportado concuerda con registros del ente regulador",

    # CUENTAS POR PAGAR (425)
    "425.03": "Validar que CXP en libros coincide con suma de acreencias por pagar",
    "425.04": "Evaluar antigüedad de pasivos para identificar posibles asuntos no resueltos",
    "425.05": "Confirmar directamente con proveedores principales que saldos son correctos",
    "425.06": "Evaluar pagos posteriores para validar que pasivos existían al cierre",
    "425.07": "Aplicar metodología NIIF 9 si hay pasivos a valor presente",

    # IMPUESTOS PASIVO (324)
    "324.02": "Validar que retenciones de IR están correctamente calculadas y declaradas",
    "324.03": "Validar que retenciones de IVA están correctamente calculadas",
    "324.04": "Validar que IVA de ventas está correctamente liquidado vs compras",
    "324.05": "Validar que ATS declarado concuerda con registros de compras",
    "324.06": "Identificar otros impuestos (ganancias, contribuciones) no registrados",
    "324.07": "Validar que dividendos en suspenso están correctamente reportados",
    "324.08": "Validar que APS (aporte a seguridad social) está correctamente declarado",

    # IMPUESTO DIFERIDO (325)
    "325.03": "Validar movimientos de activo/pasivo por impuesto diferido",
    "325.04": "Recalcular impuesto diferido sobre diferencias temporarias",

    # OBLIGACIONES FINANCIERAS (330)
    "330.03": "Validar movimientos de deuda en el período (emisiones, cancelaciones)",
    "330.04": "Validar que nuevas obligaciones fueron adecuadamente aprobadas",
    "330.05": "Cruzar saldos de deuda con información en EE.FF.",
    "330.06": "Validar que pagos de deuda están registrados en cash flow correcto",

    # BENEFICIOS A EMPLEADOS (415)
    "415.03": "Validar que beneficios post-empleo están correctamente clasificados",
    "415.04": "Validar que supuestos actuariales son razonables",
    "415.05": "Validar que nómina de activos coincide con registros",
    "415.06": "Validar que pensionados están correctamente registrados",

    # INGRESOS (1500)
    "1500.03": "Validar que ingresos por ventas concuerdan con facturas emitidas",
    "1500.04": "Identificar facturas duplicadas o faltantes en secuencia",
    "1500.05": "Recalcular ingresos totales para validar razonabilidad",
    "1500.06": "Analizar ingresos por producto/cliente para detectar anomalías",
    "1500.07": "Validar que ingresos registrados post-cierre corresponden a período siguiente",
    "1500.08": "Muestrear facturas para validar existencia, autorización y correctitud",
    "1500.09": "Validar que ingresos sin factura (si aplica) están documentados",
    "1500.10": "Validar que devoluciones están correctamente registradas",

    # GASTOS (1600)
    "1600.03": "Validar que gastos registrados corresponden a operaciones reales del período",
    "1600.04": "Evaluar si hay gastos inusualmente altos o no recurrentes",
}

def enrich_papeles(json_path: str = "data/papeles_clasificados.json"):
    """Enriquece descripciones con MOTIVO auditor"""

    json_file = Path(json_path)
    if not json_file.exists():
        print(f"Error: {json_path} no existe")
        return False

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    papeles = data.get("papeles", [])
    print(f"Enriqueciendo {len(papeles)} papeles con MOTIVOS auditor...")

    updated = 0
    sin_motivo = []

    for papel in papeles:
        codigo = papel.get("codigo")

        # Buscar motivo
        if codigo in MOTIVOS_PAPELES:
            papel["descripcion"] = MOTIVOS_PAPELES[codigo]
            papel["tipo_descripcion"] = "MOTIVO_AUDITOR"
            updated += 1
        else:
            sin_motivo.append(codigo)

    # Guardar enriquecido
    output_path = Path("data/papeles_clasificados_enriquecido.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nExito! {updated}/{len(papeles)} papeles actualizados con MOTIVO")
    if sin_motivo:
        print(f"Advertencia - Sin motivo definido: {sin_motivo}")
    print(f"\nArchivo enriquecido guardado en: {output_path}")

    return True

if __name__ == "__main__":
    enrich_papeles()
