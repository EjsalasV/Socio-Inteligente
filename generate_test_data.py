"""
Generador de datos de prueba para cliente_demo

Ejecutar una sola vez: python generate_test_data.py

Esto creará:
- tb.xlsx con trial balance de ejemplo
- hallazgos_previos.yaml
- patrones.yaml

Después podrás ejecutar la app con datos reales.
"""

import pandas as pd
import yaml
from pathlib import Path

# Ruta al cliente demo
cliente_path = Path("data/clientes/cliente_demo")

print("🔧 Generando datos de prueba para cliente_demo...\n")

# ============================================================
# 1. CREAR TRIAL BALANCE (TB.XLSX)
# ============================================================
print("1️⃣  Creando Trial Balance...")

# Datos de ejemplo
datos_tb = []

# Activos
codigos_activos = {
    "1005": ("Caja", 250000),
    "1010": ("Bancos", 1500000),
    "1015": ("Inversiones Corto Plazo", 800000),
    "1105": ("Cuentas por Cobrar - Clientes", 3500000),
    "1110": ("Provisión CxC", -175000),
    "1205": ("Inventario Mercadería", 2000000),
    "1210": ("Mercadería en Transito", 300000),
    "1705": ("Propiedad Planta Equipo", 5000000),
    "1710": ("Deprec. Acumulada PPE", -1500000),
    "1805": ("Intangibles", 500000),
}

# Pasivos
codigos_pasivos = {
    "2005": ("Cuentas por Pagar", 1200000),
    "2010": ("Anticipos de Clientes", 150000),
    "2105": ("Impuestos por Pagar", 300000),
    "2110": ("IVA por Pagar", 180000),
    "2205": ("Provisión para Beneficios", 400000),
    "2305": ("Préstamo Bancario CP", 1000000),
    "2405": ("Préstamo Bancario LP", 500000),
}

# Patrimonio
codigos_patrimonio = {
    "3005": ("Capital Social", 5000000),
    "3010": ("Reserva Legal", 500000),
    "3015": ("Resultados Acumulados", 1500000),
    "3020": ("Resultado del Ejercicio", 825000),
}

# Ingresos
codigos_ingresos = {
    "4005": ("Ventas", -8000000),
    "4010": ("Devoluciones en Ventas", 150000),
    "4105": ("Descuentos en Ventas", 100000),
    "4205": ("Otros Ingresos", -200000),
}

# Gastos
codigos_gastos = {
    "5005": ("Costo de Ventas", 4000000),
    "5105": ("Sueldos y Salarios", 1200000),
    "5110": ("Aportes Patronales", 300000),
    "5205": ("Arriendo", 240000),
    "5210": ("Servicios Básicos", 60000),
    "5305": ("Depreciación", 150000),
    "5405": ("Gastos Administrativos", 200000),
    "5505": ("Gastos Financieros", 50000),
}

# Compilar todo
todos_codigos = {
    **codigos_activos,
    **codigos_pasivos,
    **codigos_patrimonio,
    **codigos_ingresos,
    **codigos_gastos,
}

# Crear DataFrame
for codigo, (nombre, saldo) in todos_codigos.items():
    datos_tb.append({"codigo": codigo, "nombre": nombre, "saldo": saldo})

df_tb = pd.DataFrame(datos_tb)

# Guardar a Excel
tb_path = cliente_path / "tb.xlsx"
df_tb.to_excel(tb_path, index=False, sheet_name="TrialBalance")
print(f"✅ Trial Balance creado: {tb_path}")
print(f"   - {len(df_tb)} cuentas")
print(f"   - Saldo total: ${df_tb['saldo'].sum():,.0f}")

# ============================================================
# 2. CREAR HALLAZGOS PREVIOS
# ============================================================
print("\n2️⃣  Creando hallazgos previos...")

hallazgos = [
    {
        "id": "H001",
        "area": "130",
        "titulo": "CxC antiguas sin cobrar",
        "descripcion": "Se identificaron cuentas por cobrar con más de 90 días sin movimiento",
        "riesgo": "ALTO",
    },
    {
        "id": "H002",
        "area": "140",
        "titulo": "Diferencia en arqueo de caja",
        "descripcion": "Diferencia de $5,000 en el arqueo mensual de caja",
        "riesgo": "MEDIO",
    },
    {
        "id": "H003",
        "area": "200",
        "titulo": "Capital parcialmente pagado",
        "descripcion": "Aportes de capital aún pendientes por depositar",
        "riesgo": "BAJO",
    },
]

hallazgos_path = cliente_path / "hallazgos_previos.yaml"
with open(hallazgos_path, "w", encoding="utf-8") as f:
    yaml.dump({"hallazgos": hallazgos}, f, default_flow_style=False, allow_unicode=True)

print(f"✅ Hallazgos creados: {hallazgos_path}")
print(f"   - {len(hallazgos)} hallazgos")

# ============================================================
# 3. CREAR PATRONES
# ============================================================
print("\n3️⃣  Creando patrones...")

patrones = [
    {
        "id": "P001",
        "nombre": "Movimientos Inusuales",
        "descripcion": "Se detectaron transacciones fuera del patrón normal",
        "tipo": "ANOMALIA",
        "severidad": "MEDIA",
    },
    {
        "id": "P002",
        "nombre": "Concentración de Ventas",
        "descripcion": "45% de ventas concentradas en 3 clientes",
        "tipo": "RIESGO",
        "severidad": "ALTA",
    },
    {
        "id": "P003",
        "nombre": "Ciclo de Cartera Alargado",
        "descripcion": "Días promedio de cobro aumentaron 20 días",
        "tipo": "TENDENCIA",
        "severidad": "MEDIA",
    },
]

patrones_path = cliente_path / "patrones.yaml"
with open(patrones_path, "w", encoding="utf-8") as f:
    yaml.dump({"patrones": patrones}, f, default_flow_style=False, allow_unicode=True)

print(f"✅ Patrones creados: {patrones_path}")
print(f"   - {len(patrones)} patrones")

# ============================================================
# RESUMEN
# ============================================================
print("\n" + "=" * 60)
print("✅ DATOS DE PRUEBA GENERADOS EXITOSAMENTE")
print("=" * 60)
print(f"\n📁 Ubicación: {cliente_path}")
print(f"\n📊 Archivos creados:")
print(f"   ✓ tb.xlsx - Trial balance ({len(df_tb)} cuentas)")
print(f"   ✓ hallazgos_previos.yaml - {len(hallazgos)} hallazgos")
print(f"   ✓ patrones.yaml - {len(patrones)} patrones")
print(f"\n🚀 Ahora puedes ejecutar:")
print(f"   streamlit run app/app_streamlit.py")
print("\n" + "=" * 60)
