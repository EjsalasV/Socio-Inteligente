from __future__ import annotations

import argparse
from pathlib import Path

from backend.repositories.file_repository import (
    list_area_codes,
    list_clientes,
    read_area_yaml,
    read_hallazgos,
    read_perfil,
    read_workflow,
    read_workpapers,
    write_area_yaml,
    write_memo,
    write_perfil,
    write_workflow,
    write_workpapers,
)


def backfill_cliente(cliente_id: str) -> dict[str, int]:
    perfil = read_perfil(cliente_id)
    write_perfil(cliente_id, perfil)

    workflow = read_workflow(cliente_id)
    write_workflow(cliente_id, workflow)

    workpapers = read_workpapers(cliente_id)
    write_workpapers(cliente_id, workpapers)

    area_count = 0
    for area_code in list_area_codes(cliente_id):
        area = read_area_yaml(cliente_id, area_code)
        write_area_yaml(cliente_id, area_code, area)
        area_count += 1

    memo_path = Path(__file__).resolve().parents[2] / "data" / "clientes" / cliente_id / "memo_ejecutivo.md"
    if memo_path.exists():
        write_memo(cliente_id, memo_path.read_text(encoding="utf-8"))

    _ = read_hallazgos(cliente_id)
    return {"areas": area_count, "workpapers": len(workpapers)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill de memoria critica filesystem -> Supabase")
    parser.add_argument("--cliente", dest="cliente", default="", help="Cliente especifico (opcional)")
    args = parser.parse_args()

    clientes = [args.cliente] if args.cliente else list_clientes()
    if not clientes:
        print("No hay clientes para migrar.")
        return

    print(f"Backfill iniciado para {len(clientes)} cliente(s).")
    for cid in clientes:
        try:
            stats = backfill_cliente(cid)
            print(f"[OK] {cid}: {stats['areas']} areas, {stats['workpapers']} tasks")
        except Exception as exc:
            print(f"[ERROR] {cid}: {exc}")


if __name__ == "__main__":
    main()
