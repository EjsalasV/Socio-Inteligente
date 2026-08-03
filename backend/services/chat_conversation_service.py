from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.repositories.file_repository import repo, read_chat_history, write_chat_history

_SAFE_ID = re.compile(r"^[a-f0-9]{12,32}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _path(cliente_id: str) -> Path:
    return repo.cliente_dir(cliente_id) / "chat_conversations.json"


def _read(cliente_id: str) -> list[dict[str, Any]]:
    path = _path(cliente_id)
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return value if isinstance(value, list) else []


def _write(cliente_id: str, rows: list[dict[str, Any]]) -> None:
    path = _path(cliente_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def list_conversations(cliente_id: str) -> list[dict[str, Any]]:
    return sorted(_read(cliente_id), key=lambda row: str(row.get("updated_at") or ""), reverse=True)


def create_conversation(cliente_id: str, title: str = "Nueva conversación") -> dict[str, Any]:
    now = _now()
    row = {"id": uuid4().hex[:20], "title": title.strip()[:80] or "Nueva conversación", "created_at": now, "updated_at": now}
    rows = _read(cliente_id)
    rows.append(row)
    _write(cliente_id, rows)
    return row


def ensure_conversation(cliente_id: str, conversation_id: str, first_message: str = "") -> dict[str, Any]:
    cid = str(conversation_id or "").strip().lower()
    if not _SAFE_ID.fullmatch(cid):
        raise ValueError("Identificador de conversación inválido.")
    rows = _read(cliente_id)
    row = next((item for item in rows if item.get("id") == cid), None)
    if row is None:
        now = _now()
        title = first_message.strip().replace("\n", " ")[:60] or "Nueva conversación"
        row = {"id": cid, "title": title, "created_at": now, "updated_at": now}
        rows.append(row)
    else:
        row["updated_at"] = _now()
        if row.get("title") == "Nueva conversación" and first_message.strip():
            row["title"] = first_message.strip().replace("\n", " ")[:60]
    _write(cliente_id, rows)
    return row


def rename_conversation(cliente_id: str, conversation_id: str, title: str) -> dict[str, Any] | None:
    rows = _read(cliente_id)
    row = next((item for item in rows if item.get("id") == conversation_id), None)
    if row is None:
        return None
    row["title"] = title.strip()[:80] or "Conversación"
    row["updated_at"] = _now()
    _write(cliente_id, rows)
    return row


def delete_conversation(cliente_id: str, conversation_id: str) -> bool:
    rows = _read(cliente_id)
    if not any(item.get("id") == conversation_id for item in rows):
        return False
    _write(cliente_id, [item for item in rows if item.get("id") != conversation_id])
    history = read_chat_history(cliente_id)
    write_chat_history(cliente_id, [item for item in history if item.get("conversation_id") != conversation_id])
    return True
