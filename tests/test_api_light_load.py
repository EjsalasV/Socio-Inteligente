from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from backend.auth import create_access_token
from backend.main import app


def _headers() -> dict[str, str]:
    token, _ = create_access_token(
        sub="load-tester",
        org_id="org_demo",
        allowed_clientes=["*"],
        role="socio",
    )
    return {"Authorization": f"Bearer {token}"}


def test_light_concurrent_load_health_and_protected_routes() -> None:
    client = TestClient(app)
    headers = _headers()

    jobs: list[tuple[str, str, dict[str, str] | None]] = []
    jobs.extend([("GET", "/health", None) for _ in range(25)])
    jobs.extend([("GET", "/clientes", headers) for _ in range(25)])

    def _request(method: str, path: str, req_headers: dict[str, str] | None) -> tuple[int, str]:
        if method == "GET":
            res = client.get(path, headers=req_headers or {})
        else:
            res = client.post(path, headers=req_headers or {})
        return res.status_code, path

    statuses: list[tuple[int, str]] = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(_request, method, path, req_headers) for method, path, req_headers in jobs]
        for f in as_completed(futures):
            statuses.append(f.result())

    assert len(statuses) == 50
    assert all(code < 500 for code, _ in statuses), f"Se detectaron 5xx bajo carga ligera: {statuses}"

    health_codes = [code for code, path in statuses if path == "/health"]
    clientes_codes = [code for code, path in statuses if path == "/clientes"]
    assert len(health_codes) == 25 and all(code == 200 for code in health_codes)
    assert len(clientes_codes) == 25 and all(code == 200 for code in clientes_codes)
