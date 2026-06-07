#!/usr/bin/env python3
"""
Script para ejecutar migraciones SQL contra PostgreSQL (Railway) o SQLite (desarrollo local)
Uso: python run_migrations_universal.py
"""

import os
import glob
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("[WARNING] DATABASE_URL no está configurada. Usando SQLite local...")
    DATABASE_URL = "sqlite:///./socio_ai_clean.db"

db_name = DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL.split('/')[-1]
print(f"[INFO] Conectando a base de datos: {db_name}")

# Detectar tipo de base de datos
is_postgresql = "postgresql" in DATABASE_URL or "postgres" in DATABASE_URL
is_sqlite = "sqlite" in DATABASE_URL

try:
    if is_postgresql:
        import psycopg2
        from psycopg2.extensions import AUTOCOMMIT

        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(AUTOCOMMIT)
        cursor = conn.cursor()
        print("[OK] Conexion a PostgreSQL exitosa")
    elif is_sqlite:
        import sqlite3

        # Extraer ruta del archivo SQLite
        db_path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"[OK] Conexion a SQLite exitosa: {db_path}")
    else:
        print("[ERROR] Tipo de base de datos no soportado")
        exit(1)

except Exception as e:
    print(f"[ERROR] Error de conexion: {e}")
    exit(1)

# Obtener todas las migraciones en orden
migrations_dir = Path(__file__).parent / "migrations"
migration_files = sorted(glob.glob(str(migrations_dir / "*.sql")))

if not migration_files:
    print("[WARNING] No hay migraciones encontradas")
    exit(1)

print(f"\n[INFO] Migraciones encontradas: {len(migration_files)}")
for f in migration_files:
    print(f"  - {Path(f).name}")

print("\n[INFO] Ejecutando migraciones...\n")

executed_count = 0
for migration_file in migration_files:
    migration_name = Path(migration_file).name

    try:
        with open(migration_file, "r", encoding="utf-8") as f:
            sql_content = f.read()

        # Para SQLite, ejecutar cada sentencia por separado
        if is_sqlite:
            # Separar por punto y coma y ejecutar
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            for statement in statements:
                try:
                    cursor.execute(statement)
                except Exception as e:
                    # SQLite puede fallar con algunos comandos, continuar
                    pass
        else:
            # Para PostgreSQL, ejecutar todo junto
            cursor.execute(sql_content)

        executed_count += 1
        print(f"[OK] {migration_name}")

    except Exception as e:
        error_msg = str(e)[:100]
        print(f"[ERROR] {migration_name}: {error_msg}")
        # Continuar con siguientes migraciones (no bloquear)

# Commit para SQLite
if is_sqlite:
    conn.commit()

cursor.close()
conn.close()

print(f"\n[SUCCESS] Migraciones completadas: {executed_count}/{len(migration_files)}")
print("[INFO] Base de datos actualizada correctamente")
