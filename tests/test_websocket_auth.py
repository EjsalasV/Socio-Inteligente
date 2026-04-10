from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from fastapi.testclient import TestClient

from backend.auth import create_access_token
from backend.main import app


def test_websocket_accepts_token_via_query_param() -> None:
    """Test que WebSocket acepta token en query params"""
    token, _ = create_access_token(
        sub="ws-test-user",
        org_id="org_test",
        allowed_clientes=["cliente_demo"],
        role="auditor",
    )
    
    client = TestClient(app)
    
    # Intentar conectar vía WebSocket con token en query param
    with client.websocket_connect(
        f"/ws/clientes/cliente_demo?token={token}&module=dashboard"
    ) as websocket:
        # Debería conectarse exitosamente (no cerrar con 4401)
        data = websocket.receive_json()
        assert data.get("type") in {"presence_snapshot", "ping"}



def test_websocket_rejects_missing_token() -> None:
    """Test que WebSocket rechaza requests sin token"""
    from starlette.websockets import WebSocketDisconnect
    
    client = TestClient(app)
    
    # Intentar conectar sin token debería cerrar con código de error
    try:
        with client.websocket_connect(
            "/ws/clientes/cliente_demo?module=dashboard"
        ) as websocket:
            websocket.receive_json()
        assert False, "Debería haber cerrado la conexión sin token"
    except WebSocketDisconnect:
        # Expected - conexión rechazada sin token
        pass
