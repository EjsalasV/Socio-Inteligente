from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import WebSocket

LOGGER = logging.getLogger("socio_ai.realtime")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_module(value: str) -> str:
    module = str(value or "").strip().lower()
    return module[:64] if module else "general"


class ClienteRealtimeHub:
    """Hub en memoria para presencia y eventos colaborativos por cliente."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._connections: dict[str, dict[str, dict[str, Any]]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(
        self,
        *,
        cliente_id: str,
        websocket: WebSocket,
        user: dict[str, Any],
        module: str = "general",
    ) -> str:
        connection_id = str(uuid4())
        await websocket.accept()
        connection = {
            "connection_id": connection_id,
            "websocket": websocket,
            "user_id": str(user.get("user_id") or ""),
            "sub": str(user.get("sub") or ""),
            "display_name": str(user.get("display_name") or user.get("sub") or "Usuario"),
            "role": str(user.get("role") or "auditor"),
            "module": _normalize_module(module),
            "connected_at": _now_iso(),
            "last_seen_at": _now_iso(),
        }
        async with self._lock:
            self._connections.setdefault(cliente_id, {})[connection_id] = connection
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.get_running_loop()

        await self._broadcast_presence(cliente_id)
        return connection_id

    async def disconnect(self, *, cliente_id: str, connection_id: str) -> None:
        removed = False
        async with self._lock:
            bucket = self._connections.get(cliente_id, {})
            if connection_id in bucket:
                bucket.pop(connection_id, None)
                removed = True
            if not bucket:
                self._connections.pop(cliente_id, None)
        if removed:
            await self._broadcast_presence(cliente_id)

    async def touch(self, *, cliente_id: str, connection_id: str) -> None:
        async with self._lock:
            connection = self._connections.get(cliente_id, {}).get(connection_id)
            if isinstance(connection, dict):
                connection["last_seen_at"] = _now_iso()

    async def update_module(self, *, cliente_id: str, connection_id: str, module: str) -> None:
        changed = False
        async with self._lock:
            connection = self._connections.get(cliente_id, {}).get(connection_id)
            if isinstance(connection, dict):
                normalized = _normalize_module(module)
                if connection.get("module") != normalized:
                    connection["module"] = normalized
                    changed = True
                connection["last_seen_at"] = _now_iso()
        if changed:
            await self._broadcast_presence(cliente_id)

    async def publish_event(
        self,
        *,
        cliente_id: str,
        event_name: str,
        payload: dict[str, Any] | None = None,
        actor: str = "",
    ) -> None:
        message = {
            "type": "cliente_event",
            "cliente_id": cliente_id,
            "event_name": str(event_name or "updated"),
            "actor": str(actor or ""),
            "payload": payload or {},
            "sent_at": _now_iso(),
        }
        await self._broadcast(cliente_id, message)

    def publish_event_sync(
        self,
        *,
        cliente_id: str,
        event_name: str,
        payload: dict[str, Any] | None = None,
        actor: str = "",
    ) -> bool:
        loop = self._loop
        if loop is None or loop.is_closed() or not loop.is_running():
            return False
        future = asyncio.run_coroutine_threadsafe(
            self.publish_event(
                cliente_id=cliente_id,
                event_name=event_name,
                payload=payload,
                actor=actor,
            ),
            loop,
        )
        try:
            future.result(timeout=0.05)
        except Exception:
            # Non-blocking path: if timeout/failure occurs, we only log.
            LOGGER.debug("realtime publish_event_sync timeout/failure cliente_id=%s event=%s", cliente_id, event_name)
        return True

    async def _broadcast_presence(self, cliente_id: str) -> None:
        participants, count = await self._presence_snapshot(cliente_id)
        message = {
            "type": "presence_snapshot",
            "cliente_id": cliente_id,
            "online_count": count,
            "participants": participants,
            "sent_at": _now_iso(),
        }
        await self._broadcast(cliente_id, message)

    async def _presence_snapshot(self, cliente_id: str) -> tuple[list[dict[str, Any]], int]:
        async with self._lock:
            raw = list(self._connections.get(cliente_id, {}).values())
        participants = [
            {
                "user_id": str(row.get("user_id") or ""),
                "sub": str(row.get("sub") or ""),
                "display_name": str(row.get("display_name") or "Usuario"),
                "role": str(row.get("role") or "auditor"),
                "module": str(row.get("module") or "general"),
                "connected_at": str(row.get("connected_at") or ""),
                "last_seen_at": str(row.get("last_seen_at") or ""),
            }
            for row in raw
            if isinstance(row, dict)
        ]
        return participants, len(participants)

    async def _broadcast(self, cliente_id: str, message: dict[str, Any]) -> None:
        async with self._lock:
            bucket = dict(self._connections.get(cliente_id, {}))

        if not bucket:
            return

        stale_ids: list[str] = []
        for connection_id, row in bucket.items():
            ws = row.get("websocket")
            if not isinstance(ws, WebSocket):
                stale_ids.append(connection_id)
                continue
            try:
                await ws.send_json(message)
            except Exception:
                stale_ids.append(connection_id)

        if not stale_ids:
            return

        async with self._lock:
            current = self._connections.get(cliente_id, {})
            for connection_id in stale_ids:
                current.pop(connection_id, None)
            if not current:
                self._connections.pop(cliente_id, None)
        LOGGER.debug("realtime cleaned stale connections cliente_id=%s count=%s", cliente_id, len(stale_ids))


hub = ClienteRealtimeHub()
