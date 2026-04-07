from __future__ import annotations

import json

from backend.services.normativa_monitor_service import run_monthly_normative_refresh


def main() -> None:
    result = run_monthly_normative_refresh()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

