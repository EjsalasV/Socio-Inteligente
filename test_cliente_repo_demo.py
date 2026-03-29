"""
Script de prueba para verificar que cliente_repository funciona correctamente.
Ejecutar: python test_cliente_repo_demo.py
"""

from infra.repositories.cliente_repository import (
    cargar_perfil,
    cargar_tb,
    cargar_hallazgos,
    cargar_patrones,
    guardar_materialidad,
)

# Cliente a utilizar
CLIENTE = "cliente_demo"

print("=" * 60)
print("🧪 PRUEBA: Cliente Repository")
print("=" * 60)

# 1. Cargar perfil
print("\n1️⃣  Cargando perfil...")
perfil = cargar_perfil(CLIENTE)
print(f"   Perfil: {perfil if perfil else 'No existe o está vacío'}")

# 2. Cargar Trial Balance
print("\n2️⃣  Cargando Trial Balance...")
tb = cargar_tb(CLIENTE)
print(f"   TB shape: {tb.shape if not tb.empty else 'Vacío'}")
if not tb.empty:
    print(f"   Primeras filas:\n{tb.head()}")

# 3. Cargar hallazgos
print("\n3️⃣  Cargando hallazgos previos...")
hallazgos = cargar_hallazgos(CLIENTE)
print(f"   Total hallazgos: {len(hallazgos)}")
print(f"   Hallazgos: {hallazgos if hallazgos else 'Sin hallazgos'}")

# 4. Cargar patrones
print("\n4️⃣  Cargando patrones...")
patrones = cargar_patrones(CLIENTE)
print(f"   Total patrones: {len(patrones)}")
print(f"   Patrones: {patrones if patrones else 'Sin patrones'}")

# 5. Guardar materialidad (ejemplo)
print("\n5️⃣  Guardando materialidad...")
materl_data = {
    "revenue_threshold": 5000000,
    "profit_threshold": 500000,
    "assets_threshold": 10000000,
    "fecha_actualizacion": "2026-03-16",
}
exito = guardar_materialidad(CLIENTE, materl_data)
print(f"   Resultado: {'✅ Exitoso' if exito else '❌ Falló'}")

print("\n" + "=" * 60)
print("✨ Prueba completada")
print("=" * 60)
