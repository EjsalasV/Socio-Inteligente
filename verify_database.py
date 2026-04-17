#!/usr/bin/env python3
"""
Script de verificación: Comprueba que la BD está lista
Uso: python verify_database.py
"""

import os
import sys
from pathlib import Path

# Asegurar UTF-8 encoding en Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Agregar el proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def check_environment():
    """Verificar variables de entorno"""
    print("=" * 60)
    print("📋 VERIFICACIÓN DE CONFIGURACIÓN")
    print("=" * 60)

    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        print("❌ DATABASE_URL no configurada")
        print("   Configura en .env: DATABASE_URL=postgresql://...")
        return False

    print(f"✅ DATABASE_URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
    return True


def check_models():
    """Verificar que los modelos se pueden importar"""
    print("\n" + "=" * 60)
    print("🔍 VERIFICACIÓN DE MODELOS")
    print("=" * 60)

    try:
        from backend.models.client import Client
        print("✅ Client model: OK")
    except Exception as e:
        print(f"❌ Client model: {e}")
        return False

    try:
        from backend.models.audit import Audit
        print("✅ Audit model: OK")
    except Exception as e:
        print(f"❌ Audit model: {e}")
        return False

    try:
        from backend.models.workpapers_template import WorkpapersTemplate
        print("✅ WorkpapersTemplate model: OK")
    except Exception as e:
        print(f"❌ WorkpapersTemplate model: {e}")
        return False

    try:
        from backend.models.workpapers_observation import WorkpapersObservation
        print("✅ WorkpapersObservation model: OK")
    except Exception as e:
        print(f"❌ WorkpapersObservation model: {e}")
        return False

    return True


def check_database_connection():
    """Intentar conectar a la BD"""
    print("\n" + "=" * 60)
    print("🌐 VERIFICACIÓN DE CONEXIÓN A BD")
    print("=" * 60)

    try:
        from backend.utils.database import engine

        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Conexión a PostgreSQL: OK")
            return True

    except Exception as e:
        print(f"❌ Conexión a PostgreSQL: {e}")
        return False


def check_migrations():
    """Verificar que las migraciones existen"""
    print("\n" + "=" * 60)
    print("📄 VERIFICACIÓN DE MIGRACIONES SQL")
    print("=" * 60)

    migrations_dir = Path(__file__).parent / "backend" / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("❌ No migrations found")
        return False

    print(f"✅ Migraciones encontradas: {len(migration_files)}")
    for f in migration_files:
        print(f"   - {f.name}")

    return True


def main():
    """Ejecutar todas las verificaciones"""
    checks = [
        ("Variables de entorno", check_environment),
        ("Modelos SQLAlchemy", check_models),
        ("Conexión a BD", check_database_connection),
        ("Migraciones SQL", check_migrations),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error en {name}: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)

    all_ok = True
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
        if not result:
            all_ok = False

    if all_ok:
        print("\n🎉 ¡Todo OK! La BD está lista para usar.")
        print("\nSiguiente paso:")
        print("1. Redeploy en Vercel")
        print("2. Crear clientes vía API POST /api/clientes")
        print("3. Verificar en Railway PostgreSQL")
    else:
        print("\n❌ Hay problemas. Revisa los errores arriba.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
