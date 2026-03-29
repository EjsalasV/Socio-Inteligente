"""
Script de integración completa: cliente_repository + leer_perfil + lector_tb

Demuestra cómo todos los componentes funcionan juntos.
Ejecutar: python test_integracion_completa.py
"""

from domain.services.leer_perfil import leer_perfil, obtener_datos_clave, validar_cliente
from analysis.lector_tb import (
    leer_tb,
    obtener_resumen_tb,
    filtrar_por_tipo,
    filtrar_por_saldo_minimo,
    obtener_cuentas_por_area,
)

# Cliente a procesar
CLIENTE = "cliente_demo"

print("=" * 70)
print("🔗 INTEGRACIÓN COMPLETA: Cliente Repository + Servicios")
print("=" * 70)

# ============================================================
# 1. VALIDAR CLIENTE
# ============================================================
print("\n1️⃣  VALIDAR CLIENTE")
print("-" * 70)
existe = validar_cliente(CLIENTE)
print(f"Cliente '{CLIENTE}' válido: {existe}")

# ============================================================
# 2. LEER PERFIL
# ============================================================
print("\n2️⃣  LEER PERFIL")
print("-" * 70)
perfil = leer_perfil(CLIENTE)
if perfil:
    print(f"Nombre: {perfil.get('nombre')}")
    print(f"RUC: {perfil.get('ruc')}")
    print(f"Sector: {perfil.get('sector')}")
    print(f"Estado: {perfil.get('estado')}")
else:
    print("No se pudo cargar el perfil (probablemente no existe el archivo)")

# ============================================================
# 3. DATOS CLAVE (RESUMEN)
# ============================================================
print("\n3️⃣  DATOS CLAVE")
print("-" * 70)
datos_clave = obtener_datos_clave(CLIENTE)
if datos_clave:
    for clave, valor in datos_clave.items():
        print(f"  {clave}: {valor}")
else:
    print("No se pudieron obtener datos clave")

# ============================================================
# 4. LEER TRIAL BALANCE
# ============================================================
print("\n4️⃣  LEER TRIAL BALANCE")
print("-" * 70)
tb = leer_tb(CLIENTE)
if tb is not None:
    print(f"Filas: {tb.shape[0]}, Columnas: {tb.shape[1]}")
    print(f"\nPrimeras 5 cuentas:")
    print(tb[["codigo", "nombre", "saldo"]].head())
else:
    print("No se pudo cargar el TB (probablemente no existe el archivo)")

# ============================================================
# 5. RESUMEN DEL TB
# ============================================================
print("\n5️⃣  RESUMEN TB (Totales por tipo)")
print("-" * 70)
resumen = obtener_resumen_tb(CLIENTE)
if resumen:
    for tipo, total in resumen.items():
        print(f"  {tipo:15} {total:>15,.2f}")
else:
    print("No se pudo obtener resumen")

# ============================================================
# 6. FILTRAR POR TIPO DE CUENTA
# ============================================================
print("\n6️⃣  FILTRAR POR TIPO: ACTIVO")
print("-" * 70)
activos = filtrar_por_tipo(CLIENTE, "ACTIVO")
if activos is not None:
    print(f"Total activos: {activos.shape[0]} cuentas")
    print("\nMayores activos:")
    print(activos[["codigo", "nombre", "saldo"]].head(3))
else:
    print("No hay activos o no se pudo procesar")

# ============================================================
# 7. CUENTAS CON SALDO MAYOR A 1,000,000
# ============================================================
print("\n7️⃣  CUENTAS CON SALDO > 1,000,000")
print("-" * 70)
cuentas_mayores = filtrar_por_saldo_minimo(CLIENTE, 1000000)
if cuentas_mayores is not None:
    print(f"Total: {cuentas_mayores.shape[0]} cuentas")
    print(cuentas_mayores[["codigo", "nombre", "saldo"]].head())
else:
    print("No hay cuentas significativas o no se pudo procesar")

# ============================================================
# 8. CUENTAS POR AREA (130 = CxC)
# ============================================================
print("\n8️⃣  CUENTAS DEL ÁREA 130 (Cuentas por Cobrar)")
print("-" * 70)
area_130 = obtener_cuentas_por_area(CLIENTE, "130")
if area_130 is not None:
    print(f"Total: {area_130.shape[0]} cuentas en área 130")
    print(area_130[["codigo", "nombre", "saldo"]].head())
else:
    print("No hay cuentas para esta área o no se pudo procesar")

# ============================================================
# 9. FLUJO COMPLETO DE NEGOCIO
# ============================================================
print("\n9️⃣  FLUJO COMPLETO DE EXEMPLE NEGOCIO")
print("-" * 70)

flujo = f"""
EJEMPLO DE USO EN SERVICIOS:

1. Cargar datos del cliente:
   perfil = leer_perfil("cliente_demo")
   tb = leer_tb("cliente_demo")

2. Obtener información por área:
   cuentas_cxc = obtener_cuentas_por_area("cliente_demo", "130")

3. Análisis de materialidad:
   resumen = obtener_resumen_tb("cliente_demo")
   total_activos = resumen.get('ACTIVO', 0)
   materialidad = total_activos * 0.05  # 5% benchmark

4. Identificar cuentas significativas:
   significativas = filtrar_por_saldo_minimo("cliente_demo", materialidad)

5. Iniciar análisis por área (usando lógica en domain/services/)
"""

print(flujo)

print("\n" + "=" * 70)
print("✨ Integración completada")
print("=" * 70)
