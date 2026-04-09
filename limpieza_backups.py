from __future__ import annotations

import shutil
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KNOWLEDGE_DIR = ROOT / "data" / "conocimiento_normativo"


def main() -> None:
    use_ascii = os.name == "nt"
    ok_badge = "[OK]" if use_ascii else "✅"
    warn_badge = "[WARN]" if use_ascii else "⚠️"
    err_badge = "[ERR]" if use_ascii else "❌"
    note_badge = "[NOTE]" if use_ascii else "📋"

    if not KNOWLEDGE_DIR.exists():
        print(f"{err_badge} No existe la ruta: {KNOWLEDGE_DIR}")
        return

    backup_dirs = sorted(
        p for p in KNOWLEDGE_DIR.rglob("*") if p.is_dir() and p.name == "_backup"
    )

    if not backup_dirs:
        print(f"{ok_badge} No se encontraron carpetas _backup para eliminar.")
        return

    print(f"{note_badge} Carpetas _backup detectadas:")
    for d in backup_dirs:
        print(f" - {d}")

    confirm = input("¿Eliminar backups? s/n: ").strip().lower()
    if confirm != "s":
        print(f"{warn_badge} Operación cancelada por el usuario.")
        return

    ok = 0
    err = 0
    for d in backup_dirs:
        try:
            shutil.rmtree(d)
            ok += 1
            print(f"{ok_badge} Eliminado: {d}")
        except Exception as exc:
            err += 1
            print(f"{err_badge} Error eliminando {d}: {exc}")

    print("\n=== RESUMEN LIMPIEZA BACKUPS ===")
    print(f"{ok_badge} Eliminados: {ok}")
    print(f"{err_badge} Errores: {err}")


if __name__ == "__main__":
    main()
