from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from backend.auth import AUTH_COOKIE_NAME, authorize_cliente_access, get_user_from_token
from backend.services.realtime_collab_service import hub

router = APIRouter(tags=["realtime"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _close_code_from_http(status_code: int) -> int:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return 4401
    if status_code == status.HTTP_403_FORBIDDEN:
        return 4403
    return 4400


@router.websocket("/ws/clientes/{cliente_id}")
async def ws_cliente(cliente_id: str, websocket: WebSocket) -> None:
    token = str(websocket.query_params.get("token") or "").strip()
    if not token:
        token = str(websocket.cookies.get(AUTH_COOKIE_NAME) or "").strip()
    module = str(websocket.query_params.get("module") or "general").strip()

    if not token:
        await websocket.close(code=4401, reason="Falta token bearer")
        return

    try:
        user = get_user_from_token(token)
        authorize_cliente_access(cliente_id, user)
    except HTTPException as exc:
        await websocket.close(code=_close_code_from_http(exc.status_code), reason=str(exc.detail))
        return
    except Exception:
        await websocket.close(code=4401, reason="Token invalido")
        return

    connection_id = await hub.connect(
        cliente_id=cliente_id,
        websocket=websocket,
        user={
            "user_id": user.user_id,
            "sub": user.sub,
            "display_name": user.display_name or user.sub,
            "role": user.role,
        },
        module=module or "general",
    )
    await hub.publish_event(
        cliente_id=cliente_id,
        event_name="presence_join",
        actor=user.display_name or user.sub,
        payload={"module": module or "general"},
    )

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=45)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping", "sent_at": _now_iso()})
                await hub.touch(cliente_id=cliente_id, connection_id=connection_id)
                continue

            await hub.touch(cliente_id=cliente_id, connection_id=connection_id)

            message: dict[str, object] = {}
            if raw.strip():
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        message = parsed
                except Exception:
                    message = {"type": "raw", "payload": raw[:256]}

            mtype = str(message.get("type") or "").strip().lower()
            if mtype == "ping":
                await websocket.send_json({"type": "pong", "sent_at": _now_iso()})
                continue
            if mtype == "set_module":
                next_module = str(message.get("module") or "general").strip() or "general"
                await hub.update_module(cliente_id=cliente_id, connection_id=connection_id, module=next_module)
                continue
    except WebSocketDisconnect:
        pass
    finally:
        await hub.disconnect(cliente_id=cliente_id, connection_id=connection_id)
        await hub.publish_event(
            cliente_id=cliente_id,
            event_name="presence_leave",
            actor=user.display_name or user.sub,
            payload={},
        )
