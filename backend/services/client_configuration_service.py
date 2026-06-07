from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.models.client import Client
from backend.models.cliente_configuration import ClienteConfiguration
from backend.utils.database import SessionLocal


def _build_snapshot(cliente: Client | None, config: ClienteConfiguration | None) -> dict[str, Any]:
    respuestas = config.respuestas if config and isinstance(config.respuestas, dict) else {}
    return {
        "cliente_id": getattr(cliente, "client_id", ""),
        "tipo_entidad": getattr(cliente, "tipo_entidad", None) or getattr(config, "tipo_entidad", None),
        "tamano": getattr(cliente, "tamano", None),
        "normativa": getattr(cliente, "normativa", None),
        "sector": getattr(cliente, "sector", None),
        "respuestas": respuestas,
    }


def get_cliente_configuration_snapshot(cliente_id: str, session: Session | None = None) -> dict[str, Any] | None:
    owns_session = session is None
    db = session or SessionLocal()
    try:
        cliente = db.query(Client).filter(Client.client_id == cliente_id).first()
        if not cliente:
            return None
        config = (
            db.query(ClienteConfiguration)
            .filter(ClienteConfiguration.client_id == cliente.id)
            .order_by(ClienteConfiguration.updated_at.desc())
            .first()
        )
        return _build_snapshot(cliente, config)
    finally:
        if owns_session:
            db.close()


def build_configuration_context(snapshot: dict[str, Any] | None) -> str:
    if not snapshot:
        return "Configuracion de industria: no disponible."

    respuestas = snapshot.get("respuestas") if isinstance(snapshot.get("respuestas"), dict) else {}
    if respuestas:
        pairs = "\n".join([f"  - {k}: {v}" for k, v in respuestas.items()])
    else:
        pairs = "  - Sin respuestas especificas registradas"

    return (
        "CONFIGURACION DE INDUSTRIA:\n"
        f"  Tipo entidad: {snapshot.get('tipo_entidad') or 'N/D'}\n"
        f"  Tamaño: {snapshot.get('tamano') or 'N/D'}\n"
        f"  Normativa: {snapshot.get('normativa') or 'N/D'}\n"
        f"  Sector: {snapshot.get('sector') or 'N/D'}\n"
        "RESPUESTAS CLAVE:\n"
        f"{pairs}"
    )
