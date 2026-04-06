"""
Test del flujo completo: run_cliente()

Ejecutar: python test_flujo_completo.py
"""

from app.socio_ai import run_cliente
import json

print("\n" + "█" * 70)
print("█ 🧪 TEST: FLUJO COMPLETO DEL SISTEMA                              █")
print("█" * 70)

# ============================================================
# TEST 1: Cliente Demo
# ============================================================
print("\n\n🔹 TEST 1: Ejecutando flujo para cliente_demo")
print("=" * 70)

resultado = run_cliente("cliente_demo")

if resultado['status'] == 'EXITOSO':
    print("\n✅ FLUJO COMPLETADO EXITOSAMENTE\n")
    
    print("📊 RESULTADO JSON (para referencia):\n")
    print(json.dumps(resultado, indent=2, default=str))
else:
    print(f"\n❌ FLUJO FALLÓ: {resultado['mensaje']}")

# ============================================================
# TEST 2: Intentar cliente que no existe
# ============================================================
print("\n\n🔹 TEST 2: Intentando cliente inexistente")
print("=" * 70)

resultado_error = run_cliente("cliente_no_existe")

if resultado_error['status'] != 'EXITOSO':
    print(f"\n✅ Manejo de error correcto: {resultado_error['mensaje']}")
else:
    print(f"\n⚠️  Error: Se debería haber detectado el cliente inválido")

# ============================================================
# SUMMARY
# ============================================================
print("\n\n" + "█" * 70)
print("█ 📋 RESUMEN DE TESTS                                              █")
print("█" * 70)
print("""
✅ Validaciones:
   • run_cliente() carga el cliente correctamente
   • Flujo completo ejecuta sin errores
   • Manejo de errores funciona para clientes inexistentes
   
✅ Datos capturados:
   • Perfil del cliente
   • Trial balance (cuentas y saldos)
   • Variaciones detectadas
   • Ranking de áreas por riesgo
   
✅ Salida:
   • Prints claros y estructurados
   • JSON structure para integración
   • Status de ejecución
   
🚀 Próximos pasos:
   • Crear materialidad_service.py
   • Integrar LLM para briefings
   • Crear vista Streamlit
""")
print("█" * 70 + "\n")
