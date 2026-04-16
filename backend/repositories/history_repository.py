"""
Repositorio de historia de auditoría y alertas.

Maneja persistencia de audit_history, period_snapshot y operational_alerts.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.repositories.file_repository import FileRepository

LOGGER = logging.getLogger("socio_ai.history_repository")

# Instantiate the file repository
repo = FileRepository()


def _get_history_dir(cliente_id: str, create: bool = True) -> Path:
    """Obtiene o crea directorio de historia del cliente."""
    cliente_dir = repo._resolve_cliente_dir(cliente_id, for_write=create)
    history_dir = cliente_dir / "historia"
    if create:
        history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def append_audit_log(audit_data: dict[str, Any]) -> None:
    """
    Agrega un registro de auditoría.

    Args:
        audit_data: Diccionario con datos de auditoría
    """
    cliente_id = str(audit_data.get("cliente_id") or "")
    if not cliente_id:
        LOGGER.warning("append_audit_log: cliente_id vacío")
        return

    history_dir = _get_history_dir(cliente_id, create=True)
    audit_file = history_dir / "audit_history.jsonl"

    try:
        # Append a JSONL file (uno por línea)
        line = json.dumps(audit_data, default=str)
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        LOGGER.debug(f"audit_log appended: {audit_data.get('id')}")
    except Exception as e:
        LOGGER.error(f"Error appending audit log: {e}")


def append_alert(alert_data: dict[str, Any]) -> None:
    """
    Agrega una alerta operacional.

    Args:
        alert_data: Diccionario con datos de alerta
    """
    cliente_id = str(alert_data.get("cliente_id") or "")
    if not cliente_id:
        LOGGER.warning("append_alert: cliente_id vacío")
        return

    history_dir = _get_history_dir(cliente_id, create=True)
    alerts_file = history_dir / "operational_alerts.jsonl"

    try:
        line = json.dumps(alert_data, default=str)
        with open(alerts_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        LOGGER.debug(f"alert appended: {alert_data.get('id')}")
    except Exception as e:
        LOGGER.error(f"Error appending alert: {e}")


def get_alerts(cliente_id: str, resolved_only: bool = False) -> list[dict[str, Any]]:
    """
    Obtiene alertas del cliente.

    Args:
        cliente_id: ID del cliente
        resolved_only: Si solo retornar resueltas

    Returns:
        Lista de alertas
    """
    history_dir = _get_history_dir(cliente_id, create=False)
    alerts_file = history_dir / "operational_alerts.jsonl"

    if not alerts_file.exists():
        return []

    alerts = []
    try:
        with open(alerts_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # Filtrar por status
                    if resolved_only:
                        if data.get("resuelto"):
                            alerts.append(data)
                    else:
                        if not data.get("resuelto"):
                            alerts.append(data)
                except json.JSONDecodeError:
                    LOGGER.warning(f"Invalid JSON in alerts file: {line[:50]}")
    except Exception as e:
        LOGGER.error(f"Error reading alerts: {e}")

    return alerts


def update_alert_status(alert_id: str, resolved: bool) -> dict[str, Any] | None:
    """
    Actualiza status de una alerta.

    Args:
        alert_id: ID de la alerta
        resolved: Nuevo status

    Returns:
        Alerta actualizada o None
    """
    # Buscar en todos los clientes (esto es temporal, debería pasarse cliente_id)
    # Por ahora retornamos None ya que se necesitaría iterar sobre todos los clientes
    LOGGER.warning(f"update_alert_status: No cliente_id provided, cannot update {alert_id}")
    return None


def save_period_snapshot(cliente_id: str, periodo: str, snapshot_data: dict[str, Any]) -> None:
    """
    Guarda un snapshot de período.

    Args:
        cliente_id: ID del cliente
        periodo: Período en formato YYYYMM
        snapshot_data: Datos del snapshot
    """
    history_dir = _get_history_dir(cliente_id, create=True)
    snapshots_dir = history_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    snapshot_file = snapshots_dir / f"snapshot_{periodo}.json"

    try:
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, indent=2, default=str)
        LOGGER.info(f"period_snapshot saved: {cliente_id} {periodo}")
    except Exception as e:
        LOGGER.error(f"Error saving period snapshot: {e}")


def get_period_snapshot(cliente_id: str, periodo: str) -> dict[str, Any] | None:
    """
    Obtiene un snapshot de período específico.

    Args:
        cliente_id: ID del cliente
        periodo: Período en formato YYYYMM

    Returns:
        Datos del snapshot o None
    """
    history_dir = _get_history_dir(cliente_id, create=False)
    snapshot_file = history_dir / "snapshots" / f"snapshot_{periodo}.json"

    if not snapshot_file.exists():
        return None

    try:
        with open(snapshot_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        LOGGER.error(f"Error reading period snapshot: {e}")
        return None


def get_periods(cliente_id: str) -> list[dict[str, Any]]:
    """
    Retorna lista de periodos disponibles con snapshots.

    Args:
        cliente_id: ID del cliente

    Returns:
        Lista de {periodo, fecha, snapshot_exists}
    """
    history_dir = _get_history_dir(cliente_id, create=False)
    snapshots_dir = history_dir / "snapshots"

    if not snapshots_dir.exists():
        return []

    periods = []
    try:
        for snapshot_file in sorted(snapshots_dir.glob("snapshot_*.json"), reverse=True):
            periodo = snapshot_file.stem.replace("snapshot_", "")
            try:
                with open(snapshot_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    fecha = data.get("fecha_snapshot", datetime.now(timezone.utc).isoformat())
                    periods.append({
                        "periodo": periodo,
                        "fecha": fecha,
                        "snapshot_exists": True,
                    })
            except Exception:
                pass
    except Exception as e:
        LOGGER.error(f"Error listing periods: {e}")

    return periods


def get_audit_logs(cliente_id: str, limit: int = 100) -> list[dict[str, Any]]:
    """
    Obtiene registros de auditoría.

    Args:
        cliente_id: ID del cliente
        limit: Número máximo de registros

    Returns:
        Lista de audit logs
    """
    history_dir = _get_history_dir(cliente_id, create=False)
    audit_file = history_dir / "audit_history.jsonl"

    if not audit_file.exists():
        return []

    logs = []
    try:
        with open(audit_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Retornar los últimos N registros
            for line in lines[-limit:]:
                line = line.strip()
                if not line:
                    continue
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        LOGGER.error(f"Error reading audit logs: {e}")

    return logs
