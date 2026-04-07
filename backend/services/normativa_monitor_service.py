from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config.yaml"
RAG_DIR = ROOT / "data" / "rag"
SNAPSHOT_PATH = RAG_DIR / "normativa_sources_snapshot.json"
CHANGES_PATH = RAG_DIR / "normativa_changes.json"

DEFAULT_SOURCES = [
    {
        "id": "sri_boletines",
        "norma": "SRI",
        "tipo": "tributario",
        "url": "https://www.sri.gob.ec/web/guest/home",
    },
    {
        "id": "supercias_normativa",
        "norma": "SUPERCIAS",
        "tipo": "regulatorio",
        "url": "https://www.supercias.gob.ec/portalscvs/",
    },
    {
        "id": "tributario_interno",
        "norma": "TRIBUTARIO_INTERNO",
        "tipo": "tributario",
        "url": "file://data/conocimiento_normativo/tributario_ec",
    },
]


def _load_sources() -> list[dict[str, Any]]:
    if not CONFIG_PATH.exists():
        return list(DEFAULT_SOURCES)
    try:
        cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return list(DEFAULT_SOURCES)
    monitor = cfg.get("normative_monitor") if isinstance(cfg.get("normative_monitor"), dict) else {}
    sources = monitor.get("sources") if isinstance(monitor.get("sources"), list) else []
    out: list[dict[str, Any]] = []
    for s in sources:
        if not isinstance(s, dict):
            continue
        sid = str(s.get("id") or "").strip()
        url = str(s.get("url") or "").strip()
        if not sid or not url:
            continue
        out.append(
            {
                "id": sid,
                "norma": str(s.get("norma") or sid).strip(),
                "tipo": str(s.get("tipo") or "regulatorio").strip(),
                "url": url,
            }
        )
    return out or list(DEFAULT_SOURCES)


def _source_state(source: dict[str, Any]) -> dict[str, Any]:
    url = str(source.get("url") or "").strip()
    now = datetime.now(timezone.utc).isoformat()
    if url.startswith("file://"):
        rel = url.replace("file://", "", 1).lstrip("/")
        path = ROOT / rel
        if path.exists():
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
            return {"ok": True, "etag": "", "last_modified": mtime, "checked_at": now}
        return {"ok": False, "etag": "", "last_modified": "", "checked_at": now, "error": "path_not_found"}

    req = Request(url, method="HEAD", headers={"User-Agent": "SocioAI/1.2"})
    try:
        with urlopen(req, timeout=15) as resp:
            etag = str(resp.headers.get("ETag") or "").strip()
            lm = str(resp.headers.get("Last-Modified") or "").strip()
            return {"ok": True, "etag": etag, "last_modified": lm, "checked_at": now}
    except URLError as exc:
        return {"ok": False, "etag": "", "last_modified": "", "checked_at": now, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "etag": "", "last_modified": "", "checked_at": now, "error": str(exc)}


def run_monthly_normative_refresh() -> dict[str, Any]:
    sources = _load_sources()
    RAG_DIR.mkdir(parents=True, exist_ok=True)

    previous: dict[str, Any] = {}
    if SNAPSHOT_PATH.exists():
        try:
            loaded = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                previous = loaded
        except Exception:
            previous = {}

    snapshot: dict[str, Any] = {"generated_at": datetime.now(timezone.utc).isoformat(), "sources": {}}
    changes: list[dict[str, Any]] = []

    prev_sources = previous.get("sources") if isinstance(previous.get("sources"), dict) else {}

    for src in sources:
        sid = str(src.get("id") or "").strip()
        state = _source_state(src)
        snapshot["sources"][sid] = {**src, **state}

        prev = prev_sources.get(sid) if isinstance(prev_sources.get(sid), dict) else {}
        changed = False
        tipo_cambio = ""
        if prev:
            if str(prev.get("etag") or "") and str(prev.get("etag") or "") != str(state.get("etag") or ""):
                changed = True
                tipo_cambio = "etag_changed"
            elif str(prev.get("last_modified") or "") and str(prev.get("last_modified") or "") != str(state.get("last_modified") or ""):
                changed = True
                tipo_cambio = "last_modified_changed"
        if changed:
            changes.append(
                {
                    "norma": str(src.get("norma") or sid),
                    "source_id": sid,
                    "fecha_detectada": datetime.now(timezone.utc).date().isoformat(),
                    "tipo_cambio": tipo_cambio,
                    "url_fuente": str(src.get("url") or ""),
                    "estado_revision": "pending",
                }
            )

    SNAPSHOT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "frequency": "monthly",
        "changes": changes,
    }
    CHANGES_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"sources_checked": len(sources), "changes_detected": len(changes), "changes": changes}


def get_pending_normative_changes() -> list[dict[str, Any]]:
    if not CHANGES_PATH.exists():
        return []
    try:
        payload = json.loads(CHANGES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    changes = payload.get("changes") if isinstance(payload.get("changes"), list) else []
    out: list[dict[str, Any]] = []
    for ch in changes:
        if not isinstance(ch, dict):
            continue
        if str(ch.get("estado_revision") or "").strip().lower() == "pending":
            out.append(ch)
    return out
