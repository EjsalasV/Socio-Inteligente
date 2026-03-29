"""
Test del servicio de Materialidad Asistida

Ejecutar: python test_materialidad_service.py
"""

from domain.services.materialidad_service import (
    obtener_regla_materialidad,
    obtener_base_materialidad,
    calcular_materialidad,
    sugerir_materialidad,
    obtener_materialidad_guardada,
    resumen_materialidad,
)

print("\n" + "=" * 70)
print("🧪 TEST: Servicio de Materialidad Asistida")
print("=" * 70)

cliente = "cliente_demo"

# ============================================================
# 1. OBTENER REGLA
# ============================================================
print("\n1️⃣  Obtener Regla de Materialidad")
print("-" * 70)

regla = obtener_regla_materialidad(cliente)
if regla:
    print(f"✅ Regla encontrada:")
    print(f"   Base: {regla.get('base')}")
    print(f"   Porcentaje: {regla.get('porcentaje_min')*100:.1f}% - {regla.get('porcentaje_max')*100:.1f}%")
    print(f"   Origen: {regla.get('origen', 'Unknown')}")
else:
    print("❌ No se encontró regla")

# ============================================================
# 2. OBTENER BASE
# ============================================================
print("\n2️⃣  Obtener Base de Materialidad")
print("-" * 70)

base = obtener_base_materialidad(cliente, "activos")
if base:
    print(f"✅ Base (Activos): ${base:,.2f}")
else:
    print("❌ No se pudo obtener la base")

# ============================================================
# 3. CALCULAR MATERIALIDAD
# ============================================================
print("\n3️⃣  Calcular Materialidad")
print("-" * 70)

calculo = calcular_materialidad(cliente)
if calculo:
    print(f"✅ Cálculos generados:")
    print(f"   Base utilizada: {calculo['base_utilizada']} (${calculo['valor_base']:,.2f})")
    print(f"   Porcentaje: {calculo['porcentaje_minimo']:.2f}% - {calculo['porcentaje_maximo']:.2f}%")
    print(f"\n   📊 Valores de Materialidad:")
    print(f"   ├─ Mínima:     ${calculo['materialidad_minima']:>12,.2f}")
    print(f"   ├─ Sugerida:   ${calculo['materialidad_sugerida']:>12,.2f}")
    print(f"   ├─ Máxima:     ${calculo['materialidad_maxima']:>12,.2f}")
    print(f"\n   📋 NIA 320:")
    print(f"   ├─ Desempeño:  ${calculo['materialidad_desempeno']:>12,.2f} (75% de sugerida)")
    print(f"   └─ Error Trivial: ${calculo['error_trivial']:>10,.2f} (5% de sugerida)")
else:
    print("❌ No se pudo calcular")

# ============================================================
# 4. SUGERIR MATERIALIDAD (Recomendación Completa)
# ============================================================
print("\n4️⃣  Sugerir Materialidad (Recomendación)")
print("-" * 70)

sugerencia = sugerir_materialidad(cliente)
if sugerencia:
    print(f"✅ Sugerencia generada:")
    print(f"   Cliente: {sugerencia['nombre_cliente']}")
    print(f"   Sector: {sugerencia['sector']}")
    print(f"\n   💡 Recomendación:")
    print(f"   {sugerencia['recomendacion']}")
    print(f"\n   📋 Próximos pasos:")
    for paso in sugerencia['proximos_pasos']:
        print(f"   {paso}")
else:
    print("❌ No se pudo generar sugerencia")

# ============================================================
# 5. OBTENER MATERIALIDAD GUARDADA
# ============================================================
print("\n5️⃣  Obtener Materialidad Guardada")
print("-" * 70)

guardada = obtener_materialidad_guardada(cliente)
if guardada:
    print(f"✅ Materialidad guardada encontrada:")
    print(f"   Elegida: ${guardada.get('materialidad_elegida', 'N/A')}")
    print(f"   Desempeño: ${guardada.get('materialidad_desempeno', 'N/A')}")
    print(f"   Error Trivial: ${guardada.get('error_trivial', 'N/A')}")
    print(f"   Estado: {guardada.get('estado', 'N/A')}")
else:
    print("ℹ️  No hay materialidad guardada (primera vez)")

# ============================================================
# 6. RESUMEN
# ============================================================
print("\n6️⃣  Resumen Ejecutivo de Materialidad")
print("-" * 70)

resumen = resumen_materialidad(cliente)
if resumen:
    print(f"✅ Resumen:")
    print(f"   Cliente: {resumen['nombre_cliente']}")
    print(f"   Sugerida: ${resumen['materialidad_sugerida']:,.2f}")
    print(f"   Elegida: {resumen['materialidad_elegida'] or 'Pendiente'}")
    print(f"   Base: {resumen['base']}")
    print(f"   Estado: {resumen['estado']}")
else:
    print("❌ Error generando resumen")

# ============================================================
# 7. GUARDAR MATERIALIDAD (Opcional)
# ============================================================
print("\n7️⃣  Guardar Materialidad (Demo)")
print("-" * 70)

print("⏭️  Saltando guardada (ya existe archivo de ejemplo)")
print("   En producción, el auditor usaría:")
print("   guardar_sugerencia_materialidad('cliente_demo', 420000.00)")

# ============================================================
# RESUMEN FINAL
# ============================================================
print("\n" + "=" * 70)
print("✨ TEST COMPLETADO")
print("=" * 70)
print("""
📋 Funciones disponibles:

1. obtener_regla_materialidad()      → Dict con regla aplicable
2. obtener_base_materialidad()       → Float con valor de base
3. calcular_materialidad()           → Dict con cálculos completos
4. sugerir_materialidad()            → Dict con recomendación
5. guardar_sugerencia_materialidad() → Bool (éxito de guardada)
6. obtener_materialidad_guardada()   → Dict con lo guardado
7. resumen_materialidad()            → Dict con resumen ejecutivo

💡 Flujo típico:
   1. sugerir_materialidad() → obtiene recomendación
   2. Auditor revisa y decide
   3. guardar_sugerencia_materialidad() → guarda decisión
   4. obtener_materialidad_guardada() → carga para usar
   5. resumen_materialidad() → para reportes

🎯 Ejemplo de uso en código:

   from domain.services.materialidad_service import sugerir_materialidad
   
   suggestion = sugerir_materialidad("cliente_demo")
   print(f"Sugerida: ${suggestion['calculo']['materialidad_sugerida']}")
   
   # Auditor elige...
   from domain.services.materialidad_service import guardar_sugerencia_materialidad
   guardar_sugerencia_materialidad("cliente_demo", 420000)
""")
print("=" * 70 + "\n")
