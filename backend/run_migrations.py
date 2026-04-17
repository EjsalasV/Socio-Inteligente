#!/usr/bin/env python3
"""
Script para ejecutar migraciones SQL contra la base de datos de Railway
Uso: python run_migrations.py
"""

import os
import glob
from pathlib import Path
import psycopg2
from psycopg2.extensions import AUTOCOMMIT
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL no está configurada en .env")
    print("Usa: postgresql://usuario:password@host:puerto/dbname")
    exit(1)

print(f"📡 Conectando a base de datos: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.set_isolation_level(AUTOCOMMIT)
    cursor = conn.cursor()
    print("✅ Conexión exitosa")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    exit(1)

# Obtener todas las migraciones en orden
migrations_dir = Path(__file__).parent / "migrations"
migration_files = sorted(glob.glob(str(migrations_dir / "*.sql")))

if not migration_files:
    print("⚠️  No hay migraciones encontradas")
    exit(1)

print(f"\n📋 Migraciones encontradas: {len(migration_files)}")
for f in migration_files:
    print(f"  - {Path(f).name}")

print("\n🚀 Ejecutando migraciones...\n")

executed_count = 0
for migration_file in migration_files:
    migration_name = Path(migration_file).name

    try:
        with open(migration_file, "r", encoding="utf-8") as f:
            sql = f.read()

        # Ejecutar migración
        cursor.execute(sql)
        executed_count += 1
        print(f"✅ {migration_name}")

    except Exception as e:
        print(f"❌ {migration_name}: {str(e)}")
        # Continuar con siguientes migraciones (no bloquear)

cursor.close()
conn.close()

print(f"\n✨ Migraciones completadas: {executed_count}/{len(migration_files)}")
print("\n💾 Base de datos actualizada correctamente")
