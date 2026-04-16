"""
Modelo para snapshots de períodos contables.

Almacena un estado completo del cliente en un período específico
para permitir comparativas históricas.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class PeriodSnapshot:
    """Representa un snapshot de estado financiero en un período."""

    def __init__(
        self,
        cliente_id: str,
        periodo: str,  # YYYYMM
        fecha_snapshot: datetime | None = None,
        activo: float = 0.0,
        pasivo: float = 0.0,
        patrimonio: float = 0.0,
        ingresos: float = 0.0,
        resultado_periodo: float = 0.0,
        ratio_values: dict[str, Any] | None = None,
        top_areas: list[dict[str, Any]] | None = None,
        hallazgos_count: int = 0,
        procedimientos_ejecutados: dict[str, Any] | None = None,
        evidence_gates: dict[str, Any] | None = None,
        id: str | None = None,
    ) -> None:
        self.id = id or self._generate_id()
        self.cliente_id = cliente_id
        self.periodo = periodo
        self.fecha_snapshot = fecha_snapshot or datetime.now(timezone.utc)
        self.activo = float(activo)
        self.pasivo = float(pasivo)
        self.patrimonio = float(patrimonio)
        self.ingresos = float(ingresos)
        self.resultado_periodo = float(resultado_periodo)
        self.ratio_values = ratio_values or {}
        self.top_areas = top_areas or []
        self.hallazgos_count = int(hallazgos_count)
        self.procedimientos_ejecutados = procedimientos_ejecutados or {}
        self.evidence_gates = evidence_gates or {}

    def _generate_id(self) -> str:
        """Genera un ID único."""
        from uuid import uuid4

        return f"ps_{uuid4().hex[:12]}"

    def to_dict(self) -> dict[str, Any]:
        """Serializa el snapshot a diccionario."""
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "periodo": self.periodo,
            "fecha_snapshot": self.fecha_snapshot.isoformat(),
            "activo": self.activo,
            "pasivo": self.pasivo,
            "patrimonio": self.patrimonio,
            "ingresos": self.ingresos,
            "resultado_periodo": self.resultado_periodo,
            "ratio_values": self.ratio_values,
            "top_areas": self.top_areas,
            "hallazgos_count": self.hallazgos_count,
            "procedimientos_ejecutados": self.procedimientos_ejecutados,
            "evidence_gates": self.evidence_gates,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> PeriodSnapshot:
        """Reconstruye un PeriodSnapshot desde diccionario."""
        fecha = None
        if isinstance(data.get("fecha_snapshot"), str):
            fecha = datetime.fromisoformat(data["fecha_snapshot"].replace("Z", "+00:00"))
        elif isinstance(data.get("fecha_snapshot"), datetime):
            fecha = data["fecha_snapshot"]

        return PeriodSnapshot(
            cliente_id=str(data.get("cliente_id") or ""),
            periodo=str(data.get("periodo") or ""),
            fecha_snapshot=fecha,
            activo=float(data.get("activo") or 0.0),
            pasivo=float(data.get("pasivo") or 0.0),
            patrimonio=float(data.get("patrimonio") or 0.0),
            ingresos=float(data.get("ingresos") or 0.0),
            resultado_periodo=float(data.get("resultado_periodo") or 0.0),
            ratio_values=dict(data.get("ratio_values") or {}),
            top_areas=list(data.get("top_areas") or []),
            hallazgos_count=int(data.get("hallazgos_count") or 0),
            procedimientos_ejecutados=dict(data.get("procedimientos_ejecutados") or {}),
            evidence_gates=dict(data.get("evidence_gates") or {}),
            id=str(data.get("id")) if data.get("id") else None,
        )

    def get_delta(self, other: PeriodSnapshot) -> dict[str, Any]:
        """Calcula deltas comparativos con otro snapshot."""
        def calc_delta(actual: float, anterior: float) -> dict[str, Any]:
            if anterior == 0:
                return {"valor_absoluto": actual - anterior, "porcentaje": 0.0, "mejoró": actual > anterior}
            pct = ((actual - anterior) / abs(anterior)) * 100
            return {"valor_absoluto": actual - anterior, "porcentaje": pct, "mejoró": actual > anterior}

        return {
            "activo": calc_delta(self.activo, other.activo),
            "pasivo": calc_delta(self.pasivo, other.pasivo),
            "patrimonio": calc_delta(self.patrimonio, other.patrimonio),
            "ingresos": calc_delta(self.ingresos, other.ingresos),
            "resultado_periodo": calc_delta(self.resultado_periodo, other.resultado_periodo),
            "hallazgos_count_delta": self.hallazgos_count - other.hallazgos_count,
        }
