"""
Este archivo define todas las áreas L/S del sistema.
Las L/S corresponden a la clasificación de cuentas.
"""

CATALOGO_LS = {
    # ===============================
    # ACTIVOS CORRIENTES
    # ===============================
    "140": {
        "nombre": "Efectivo y equivalentes a efectivo",
        "clase": "Activo Corriente - Disponibilidades",
    },
    "141": {
        "nombre": "Inversiones corrientes",
        "clase": "Activo Corriente - Inversiones",
    },
    "130.1": {
        "nombre": "Cuentas por cobrar corrientes",
        "clase": "Activo Corriente - Cuentas por cobrar",
    },
    "130.2": {
        "nombre": "Otras cuentas por cobrar",
        "clase": "Activo Corriente - Cuentas por cobrar",
    },
    "120": {
        "nombre": "Otros activos financieros corrientes",
        "clase": "Activo Corriente - Cuentas por cobrar",
    },
    "110": {
        "nombre": "Inventarios",
        "clase": "Activo Corriente - Inventarios",
    },
    "135": {
        "nombre": "Gastos pagados por adelantado",
        "clase": "Activo Corriente - Otros",
    },
    "136": {
        "nombre": "Activos por impuestos corrientes",
        "clase": "Activo Corriente - Impuestos",
    },
    # ===============================
    # ACTIVOS NO CORRIENTES
    # ===============================
    "35": {
        "nombre": "Cuentas por cobrar no corrientes",
        "clase": "Activo No Corriente - Cuentas por cobrar",
    },
    "111": {
        "nombre": "Activos mantenidos para la venta",
        "clase": "Activo No Corriente",
    },
    "1": {
        "nombre": "Propiedad planta y equipo",
        "clase": "Activo No Corriente - PPE",
    },
    "10": {
        "nombre": "Activos intangibles y fondo de comercio",
        "clase": "Activo No Corriente - Intangibles",
    },
    "11": {
        "nombre": "Activo por derecho de uso",
        "clase": "Activo No Corriente - Arrendamientos",
    },
    "5": {
        "nombre": "Propiedades para inversión",
        "clase": "Activo No Corriente - Inversiones",
    },
    "12": {
        "nombre": "Activos biológicos",
        "clase": "Activo No Corriente - Activos biológicos",
    },
    "14": {
        "nombre": "Inversiones no corrientes",
        "clase": "Activo No Corriente - Inversiones",
    },
    "15": {
        "nombre": "Activos por impuestos diferidos",
        "clase": "Activo No Corriente - Impuestos",
    },
    "16": {
        "nombre": "Otros activos financieros no corrientes",
        "clase": "Activo No Corriente - Otros",
    },
    # ===============================
    # PASIVOS
    # ===============================
    "425": {
        "nombre": "Cuentas por pagar",
        "clase": "Pasivo Corriente - Cuentas por pagar",
    },
    "425.1": {
        "nombre": "Cuentas por pagar no corriente",
        "clase": "Pasivo No Corriente - Cuentas por pagar",
    },
    "425.2": {
        "nombre": "Otras cuentas por pagar",
        "clase": "Pasivo Corriente - Cuentas por pagar",
    },
    "300.1": {
        "nombre": "Préstamos corrientes",
        "clase": "Pasivo Corriente - Préstamos",
    },
    "300.2": {
        "nombre": "Préstamos no corrientes",
        "clase": "Pasivo No Corriente - Préstamos",
    },
    "310": {
        "nombre": "Obligaciones emitidas corrientes",
        "clase": "Pasivo Corriente - Obligaciones",
    },
    "310.1": {
        "nombre": "Obligaciones emitidas no corrientes",
        "clase": "Pasivo No Corriente - Obligaciones",
    },
    "324": {
        "nombre": "Pasivos por impuestos corrientes",
        "clase": "Pasivo Corriente - Impuestos",
    },
    "325": {
        "nombre": "Pasivos por impuestos diferidos",
        "clase": "Pasivo No Corriente - Impuestos",
    },
    "410": {
        "nombre": "Obligaciones por beneficios a empleados",
        "clase": "Pasivo Corriente - Beneficios empleados",
    },
    "415": {
        "nombre": "Obligaciones por beneficios definidos",
        "clase": "Pasivo No Corriente - Beneficios empleados",
    },
    "420": {
        "nombre": "Provisiones",
        "clase": "Pasivo Corriente - Provisiones",
    },
    "421": {
        "nombre": "Pasivos por ingresos diferidos",
        "clase": "Pasivo Corriente - Otros",
    },
    "430": {
        "nombre": "Otros pasivos corrientes",
        "clase": "Pasivo Corriente - Otros",
    },
    # ===============================
    # PATRIMONIO
    # ===============================
    "200": {
        "nombre": "Patrimonio",
        "clase": "Patrimonio",
    },
    # ===============================
    # RESULTADOS
    # ===============================
    "1500": {
        "nombre": "Ingresos operativos",
        "clase": "Ingresos - Ventas",
    },
    "1501": {
        "nombre": "Ingresos financieros",
        "clase": "Ingresos - Otros",
    },
    "1600.5": {
        "nombre": "Costo de ventas",
        "clase": "Costos",
    },
    "1600": {
        "nombre": "Gastos administrativos",
        "clase": "Gastos operativos",
    },
    "1700": {
        "nombre": "Gastos de ventas",
        "clase": "Gastos operativos",
    },
    "1701": {
        "nombre": "Gastos logísticos",
        "clase": "Gastos operativos",
    },
    "1601": {
        "nombre": "Gastos financieros",
        "clase": "Gastos financieros",
    },
    "1800": {
        "nombre": "Otros gastos",
        "clase": "Gastos - Otros",
    },
    "1900": {
        "nombre": "Impuesto a la renta",
        "clase": "Impuesto a la renta",
    },
}
