from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import areas, auth, chat, clientes, dashboard, metodologia, perfil, reportes, risk_engine

app = FastAPI(title="Socio AI Backend", version="0.1.0")

_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
_origins = [origin.strip() for origin in _origins_raw.split(",") if origin.strip()]
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
