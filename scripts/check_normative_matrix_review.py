from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.normative_version_service import evaluate_matrix_review  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Comprueba la revision profesional de la matriz ecuatoriana.")
    parser.add_argument(
        "--require-approved",
        action="store_true",
        help="Devuelve codigo 1 mientras la revision no este aprobada y vinculada al hash actual.",
    )
    args = parser.parse_args()

    result = evaluate_matrix_review()
    print(f"Estado declarado: {result['status']}")
    print(f"Aprobacion valida: {'si' if result['approved'] else 'no'}")
    print(f"SHA-256 actual: {result['matrix_sha256']}")
    if result.get("reviewer_name"):
        print(f"Revisor: {result['reviewer_name']}")
    if result.get("review_date"):
        print(f"Fecha: {result['review_date']}")
    if result["issues"]:
        print("Brechas: " + ", ".join(result["issues"]))
    elif not result["approved"]:
        print("Brechas: revision profesional pendiente")
    else:
        print("Brechas: ninguna en el registro de revision")

    return 1 if args.require_approved and not result["approved"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
