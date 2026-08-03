import json
from pathlib import Path

import pytest

from backend.repositories.file_repository import repo
from backend.services.client_progress_service import build_client_progress


def test_client_progress_returns_real_next_action(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clients = tmp_path / "clientes"
    root = clients / "demo"
    root.mkdir(parents=True)
    monkeypatch.setattr(repo, "data_clientes", clients)
    assert build_client_progress("demo")["next_action"]["key"] == "sources"
    (root / "tb.xlsx").write_bytes(b"tb")
    (root / "entity_profile_draft.json").write_text(json.dumps({"status": "needs_answers"}), encoding="utf-8")
    assert build_client_progress("demo")["next_action"]["key"] == "profile"
    (root / "entity_profile_draft.json").write_text(json.dumps({"status": "confirmed", "analysis": {"status": "ready", "risk_hypotheses": [{"decision": {"status": "accepted"}}]}}), encoding="utf-8")
    result = build_client_progress("demo")
    assert result["next_action"]["key"] == "analysis"
    assert result["completion_pct"] == 75
