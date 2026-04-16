"""
Modelo para alertas operacionales del sistema.

Detecta y registra eventos críticos como materialidad excedida,
gates bloqueados, procedimientos faltantes, etc.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AlertType(str, Enum):
    """Tipos de alertas operacionales."""

    MATERIALIDAD_EXCEDIDA = "MATERIALIDAD_EXCEDIDA"
    GATE_BLOQUEADO = "GATE_BLOQUEADO"
    PROCEDIMIENTO_FALTANTE = "PROCEDIMIENTO_FALTANTE"
    HALLAZGO_ELIMINADO = "HALLAZGO_ELIMINADO"
    OTRO = "OTRO"


class AlertSeverity(str, Enum):
    """Niveles de severidad."""

    CRITICO = "CRITICO"
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAJO = "BAJO"


class OperationalAlert:
    """Representa una alerta operacional en el sistema."""

    def __init__(
        self,
        cliente_id: str,
        tipo: str | AlertType,
        severidad: str | AlertSeverity,
        mensaje: str,
        fecha_creada: datetime | None = None,
        resuelto: bool = False,
        metadata: dict[str, Any] | None = None,
        id: str | None = None,
    ) -> None:
        self.id = id or self._generate_id()
        self.cliente_id = cliente_id
        self.tipo = str(tipo)
        self.severidad = str(severidad)
        self.mensaje = mensaje
        self.fecha_creada = fecha_creada or datetime.now(timezone.utc)
        self.resuelto = resuelto
        self.metadata = metadata or {}

    def _generate_id(self) -> str:
        """Genera un ID único."""
        from uuid import uuid4

        return f"oa_{uuid4().hex[:12]}"

    def to_dict(self) -> dict[str, Any]:
        """Serializa la alerta a diccionario."""
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "tipo": self.tipo,
            "severidad": self.severidad,
            "mensaje": self.mensaje,
            "fecha_creada": self.fecha_creada.isoformat(),
            "resuelto": self.resuelto,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OperationalAlert:
        """Reconstruye una OperationalAlert desde diccionario."""
        fecha = None
        if isinstance(data.get("fecha_creada"), str):
            fecha = datetime.fromisoformat(data["fecha_creada"].replace("Z", "+00:00"))
        elif isinstance(data.get("fecha_creada"), datetime):
            fecha = data["fecha_creada"]

        return OperationalAlert(
            cliente_id=str(data.get("cliente_id") or ""),
            tipo=str(data.get("tipo") or AlertType.OTRO),
            severidad=str(data.get("severidad") or AlertSeverity.MEDIO),
            mensaje=str(data.get("mensaje") or ""),
            fecha_creada=fecha,
            resuelto=bool(data.get("resuelto")),
            metadata=dict(data.get("metadata") or {}),
            id=str(data.get("id")) if data.get("id") else None,
        )
