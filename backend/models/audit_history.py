"""
Modelo para auditoría y rastreo de cambios en el sistema.

Registra cada cambio (INSERT, UPDATE, DELETE) en tablas críticas,
incluyendo usuario, timestamp, y diff de los cambios.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


class AuditHistory:
    """Representa un registro de auditoría en el sistema."""

    def __init__(
        self,
        cliente_id: str,
        tabla_afectada: str,
        accion: str,  # INSERT, UPDATE, DELETE
        usuario: str,
        diff_data: dict[str, Any],
        timestamp: datetime | None = None,
        id: str | None = None,
    ) -> None:
        self.id = id or self._generate_id()
        self.cliente_id = cliente_id
        self.tabla_afectada = tabla_afectada
        self.accion = accion
        self.usuario = usuario
        self.diff = diff_data or {}
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.hash_cambio = self._compute_hash()

    def _generate_id(self) -> str:
        """Genera un ID único basado en timestamp y UUID."""
        from uuid import uuid4

        return f"ah_{uuid4().hex[:12]}"

    def _compute_hash(self) -> str:
        """Genera hash del cambio para integridad."""
        content = json.dumps(
            {
                "cliente_id": self.cliente_id,
                "tabla": self.tabla_afectada,
                "accion": self.accion,
                "usuario": self.usuario,
                "diff": self.diff,
                "timestamp": self.timestamp.isoformat(),
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serializa el registro a diccionario."""
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "tabla_afectada": self.tabla_afectada,
            "accion": self.accion,
            "usuario": self.usuario,
            "diff": self.diff,
            "timestamp": self.timestamp.isoformat(),
            "hash_cambio": self.hash_cambio,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> AuditHistory:
        """Reconstruye un AuditHistory desde diccionario."""
        timestamp = None
        if isinstance(data.get("timestamp"), str):
            timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        elif isinstance(data.get("timestamp"), datetime):
            timestamp = data["timestamp"]

        return AuditHistory(
            cliente_id=str(data.get("cliente_id") or ""),
            tabla_afectada=str(data.get("tabla_afectada") or ""),
            accion=str(data.get("accion") or ""),
            usuario=str(data.get("usuario") or ""),
            diff_data=dict(data.get("diff") or {}),
            timestamp=timestamp,
            id=str(data.get("id")) if data.get("id") else None,
        )
