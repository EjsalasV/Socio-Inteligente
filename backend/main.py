from __future__ import annotations

import os
import time
from uuid import uuid4

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import logging

from backend.routes import areas, auth, briefing, chat, clientes, dashboard, hallazgos, metodologia, perfil, reportes, risk_engine, workpapers, workflow

app = FastAPI(title="Socio AI Backend", version="0.1.0")
LOGGER = logging.getLogger("socio_ai.api")
if not LOGGER.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")


def _normalize_origin(origin: str) -> str:
    # Browsers send Origin without trailing slash. Normalize env values to avoid
    # mismatches like https://site.vercel.app/ vs https://site.vercel.app
    return origin.strip().rstrip("/")


_origins = []
for _origin in _origins_raw.split(","):
    cleaned = _normalize_origin(_origin)
    if cleaned and cleaned not in _origins:
        _origins.append(cleaned)
_is_prod = os.getenv("ENV", "development").lower() == "production"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=[] if _is_prod else ["X-Request-ID"],
)

app.include_router(auth.router)
app.include_router(clientes.router)
app.include_router(perfil.router)
app.include_router(dashboard.router)
app.include_router(risk_engine.router)
app.include_router(areas.router)
app.include_router(chat.router)
app.include_router(metodologia.router)
app.include_router(reportes.router)
app.include_router(workpapers.router)
app.include_router(workflow.router)
app.include_router(briefing.router)
app.include_router(hallazgos.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.middleware("http")
async def request_observability(request: Request, call_next) -> Response:
    start = time.perf_counter()
    request_id = str(uuid4())
    response: Response
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = int((time.perf_counter() - start) * 1000)
        LOGGER.exception(
            "api.request.failed method=%s path=%s request_id=%s duration_ms=%s",
            request.method,
            request.url.path,
            request_id,
            duration_ms,
        )
        raise

    duration_ms = int((time.perf_counter() - start) * 1000)
    path = request.url.path
    if any(
        path.startswith(prefix)
        for prefix in [
            "/auth/",
            "/clientes",
            "/perfil/",
            "/dashboard/",
            "/risk-engine/",
            "/chat/",
            "/papeles-trabajo/",
            "/workflow/",
            "/reportes/",
            "/api/briefing/",
            "/api/hallazgos/",
        ]
    ):
        LOGGER.info(
            "api.request method=%s path=%s status=%s duration_ms=%s request_id=%s",
            request.method,
            path,
            response.status_code,
            duration_ms,
            request_id,
        )
    if not _is_prod:
        response.headers["X-Request-ID"] = request_id
    return response
