from __future__ import annotations

import json
import os
from pathlib import Path

# Permite exportar esquema en CI sin requerir secreto real de JWT.
os.environ["EXPORT_OPENAPI"] = "1"

from backend.main import app


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "openapi.json"
    out.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OpenAPI exported to {out}")


if __name__ == "__main__":
    main()
