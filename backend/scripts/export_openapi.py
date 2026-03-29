from __future__ import annotations

import json
import os
from pathlib import Path

# Override JWT_SECRET_KEY for dummy schema generation
os.environ["EXPORT_OPENAPI"] = "1"

from backend.main import app  # noqa: E402


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "openapi.json"
    schema = json.dumps(app.openapi(), indent=2, ensure_ascii=False)
    out.write_text(schema, encoding="utf-8")
    print(f"OpenAPI exported to {out}")


if __name__ == "__main__":
    main()
