from pathlib import Path

import pytest

from backend.services import learning_progress_service as service


def test_progress_is_aggregated_without_client_or_response_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "learning.yaml"
    monkeypatch.setattr(service, "PROGRESS_FILE", path)
    service.record_mentor_learning("ana", progress_stage="test", ready_to_continue=True, resource_codes=["NIA-500", "ING-01"])
    progress = service.record_mentor_learning("ana", progress_stage="test", ready_to_continue=False, resource_codes=["NIA-500"])
    stored = path.read_text(encoding="utf-8")
    assert progress["total_practices"] == 2
    assert progress["competencies"][0]["practice_count"] == 2
    assert progress["competencies"][0]["progress_pct"] == 50
    assert "client_id" not in stored.lower()
    assert "account_name" not in stored.lower()
    assert "auditor_response" not in stored.lower()
    assert service.delete_learning_progress("ana") is True
    assert service.build_learning_progress("ana")["total_practices"] == 0
