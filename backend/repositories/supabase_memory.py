from __future__ import annotations

import json
import os
from typing import Any

import requests


class SupabaseMemoryStore:
    def __init__(self) -> None:
        self.url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
        self.service_key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
        self.enabled = (os.getenv("USE_SUPABASE_MEMORY") or "0").strip() in {"1", "true", "yes"}
        self.timeout = float((os.getenv("SUPABASE_TIMEOUT_SECONDS") or "8").strip() or "8")

    def is_configured(self) -> bool:
        return self.enabled and bool(self.url) and bool(self.service_key)

    @property
    def _base(self) -> str:
        return f"{self.url}/rest/v1"

    def _headers(self, *, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def _request(self, method: str, path: str, *, params: dict[str, Any] | None = None, body: Any | None = None) -> Any:
        if not self.is_configured():
            return None
        try:
            resp = requests.request(
                method=method,
                url=f"{self._base}/{path}",
                params=params,
                data=json.dumps(body) if body is not None else None,
                headers=self._headers(prefer="return=representation"),
                timeout=self.timeout,
            )
            if resp.status_code >= 400:
                return None
            if not resp.text.strip():
                return None
            return resp.json()
        except Exception:
            return None

    def fetch_single_json(self, table: str, filters: dict[str, str], json_field: str) -> dict[str, Any] | None:
        params = {"select": json_field, "limit": "1"}
        for key, value in filters.items():
            params[key] = f"eq.{value}"
        result = self._request("GET", table, params=params)
        if not isinstance(result, list) or not result:
            return None
        row = result[0] if isinstance(result[0], dict) else {}
        payload = row.get(json_field)
        return payload if isinstance(payload, dict) else None

    def fetch_rows(self, table: str, *, filters: dict[str, str] | None = None, select: str = "*") -> list[dict[str, Any]]:
        params: dict[str, str] = {"select": select}
        for key, value in (filters or {}).items():
            params[key] = f"eq.{value}"
        result = self._request("GET", table, params=params)
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]

    def upsert_row(self, table: str, payload: dict[str, Any], *, on_conflict: str) -> bool:
        if not self.is_configured():
            return False
        try:
            resp = requests.post(
                f"{self._base}/{table}",
                params={"on_conflict": on_conflict},
                headers=self._headers(prefer="resolution=merge-duplicates,return=representation"),
                data=json.dumps(payload),
                timeout=self.timeout,
            )
            return 200 <= resp.status_code < 300
        except Exception:
            return False

    def delete_where(self, table: str, filters: dict[str, str]) -> bool:
        if not self.is_configured():
            return False
        params = {k: f"eq.{v}" for k, v in filters.items()}
        try:
            resp = requests.delete(
                f"{self._base}/{table}",
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
            return 200 <= resp.status_code < 300
        except Exception:
            return False

    def list_clientes(self) -> list[str]:
        if not self.is_configured():
            return []
        params = {"select": "cliente_id", "order": "cliente_id.asc"}
        result = self._request("GET", "clientes", params=params)
        if not isinstance(result, list):
            return []
        out: list[str] = []
        for row in result:
            if isinstance(row, dict):
                cid = str(row.get("cliente_id") or "").strip()
                if cid:
                    out.append(cid)
        return out


store = SupabaseMemoryStore()
