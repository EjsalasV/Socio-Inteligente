"""
Supabase repository for SocioAI client persistence.
Compatible with existing Sheets integration function names.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import requests

_LAST_REMOTE_ERROR = ""
TABLE_CLIENTES = "clientes"


def _set_last_error(msg: str) -> None:
    global _LAST_REMOTE_ERROR
    _LAST_REMOTE_ERROR = str(msg or "").strip()


def obtener_ultimo_error_sheets() -> str:
    return _LAST_REMOTE_ERROR


def _get_cfg() -> tuple[str, str]:
    try:
        import streamlit as st
        # Direct access first (most reliable in Streamlit Cloud)
        def _sg(name: str) -> str:
            try:
                v = st.secrets.get(name, "")
                return str(v or "").strip()
            except Exception:
                return ""

        direct_url = (
            _sg("SUPABASE_URL")
            or _sg("supabase_url")
            or _sg("PROJECT_URL")
            or _sg("project_url")
        )
        direct_key = (
            _sg("SUPABASE_ANON_KEY")
            or _sg("supabase_anon_key")
            or _sg("SUPABASE_PUBLISHABLE_KEY")
            or _sg("supabase_publishable_key")
            or _sg("SUPABASE_KEY")
            or _sg("supabase_key")
            or _sg("ANON_KEY")
            or _sg("anon_key")
        )

        # Runtime fallback (manual inputs in UI)
        runtime_url = str(
            st.session_state.get("runtime_supabase_url", "") or ""
        ).strip()
        runtime_key = str(
            st.session_state.get("runtime_supabase_key", "") or ""
        ).strip()
        if runtime_url and runtime_key:
            return runtime_url, runtime_key

        # Nested block access
        block_url = ""
        block_key = ""
        for bn in ["supabase", "SUPABASE"]:
            try:
                blk = st.secrets.get(bn, {})
                if hasattr(blk, "get"):
                    block_url = block_url or str(blk.get("url", "") or "").strip()
                    block_key = (
                        block_key
                        or str(blk.get("anon_key", "") or "").strip()
                        or str(blk.get("publishable_key", "") or "").strip()
                        or str(blk.get("key", "") or "").strip()
                    )
            except Exception:
                pass

        if direct_url and direct_key:
            return direct_url, direct_key

        # Fallback map build (case-insensitive scan)
        secrets_map: dict[str, Any] = {}
        try:
            secrets_map = st.secrets.to_dict()  # type: ignore[attr-defined]
        except Exception:
            try:
                secrets_map = dict(st.secrets)
            except Exception:
                secrets_map = {}

        # Flatten nested dicts and match keys case-insensitively
        flat: dict[str, Any] = {}

        def _walk(prefix: str, obj: Any) -> None:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    k2 = f"{prefix}.{k}" if prefix else str(k)
                    flat[k2.lower()] = v
                    _walk(k2, v)

        _walk("", secrets_map)

        def _pick(candidates: list[str]) -> str:
            for c in candidates:
                v = flat.get(c.lower(), "")
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return ""

        url = (
            direct_url
            or block_url
            or
            _pick([
                "SUPABASE_URL",
                "supabase_url",
                "PROJECT_URL",
                "project_url",
                "supabase.url",
                "SUPABASE.url",
                "SUPABASE.URL",
            ])
            or os.environ.get("SUPABASE_URL", "")
            or os.environ.get("PROJECT_URL", "")
        )
        key = (
            direct_key
            or block_key
            or
            _pick([
                "SUPABASE_ANON_KEY",
                "supabase_anon_key",
                "SUPABASE_PUBLISHABLE_KEY",
                "supabase_publishable_key",
                "SUPABASE_KEY",
                "supabase_key",
                "ANON_KEY",
                "anon_key",
                "supabase.anon_key",
                "SUPABASE.anon_key",
                "supabase.publishable_key",
                "SUPABASE.publishable_key",
                "supabase.key",
                "SUPABASE.key",
            ])
            or os.environ.get("SUPABASE_ANON_KEY", "")
            or os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
            or os.environ.get("SUPABASE_KEY", "")
        )
        return str(url or "").strip(), str(key or "").strip()
    except Exception:
        return "", ""


def _headers() -> dict[str, str]:
    _, key = _get_cfg()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def sheets_disponible() -> bool:
    url, key = _get_cfg()
    return bool(url and key)


def _rest_url(table: str) -> str:
    url, _ = _get_cfg()
    return f"{url.rstrip('/')}/rest/v1/{table}"


def guardar_cliente_supabase(
    cliente_id: str,
    perfil: dict[str, Any],
) -> bool:
    try:
        if not sheets_disponible():
            _set_last_error("Missing SUPABASE_URL or SUPABASE_ANON_KEY.")
            return False

        c = perfil.get("cliente", {})
        enc = perfil.get("encargo", {})
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        payload = {
            "cliente_id": cliente_id,
            "nombre_legal": c.get("nombre_legal", ""),
            "ruc": c.get("ruc", ""),
            "sector": c.get("sector", ""),
            "tipo_entidad": c.get("tipo_entidad", ""),
            "periodo": str(enc.get("anio_activo", "")),
            "marco": enc.get("marco_referencial", ""),
            "riesgo_global": perfil.get("riesgo_global", {}).get("nivel", ""),
            "moneda": c.get("moneda_funcional", "USD"),
            "fecha_actualizacion": now,
            "perfil_json": json.dumps(perfil, ensure_ascii=False),
        }

        h = _headers()
        h["Prefer"] = "resolution=merge-duplicates,return=representation"
        r = requests.post(
            _rest_url(TABLE_CLIENTES),
            params={"on_conflict": "cliente_id"},
            headers=h,
            json=payload,
            timeout=20,
        )
        if r.status_code >= 300:
            _set_last_error(
                f"Supabase save failed [{r.status_code}]: {r.text[:500]}"
            )
            return False
        _set_last_error("")
        return True
    except Exception as e:
        _set_last_error(
            f"Supabase save error [{type(e).__name__}]: {e!r}"
        )
        return False


def cargar_clientes_supabase() -> list[dict[str, Any]]:
    try:
        if not sheets_disponible():
            return []
        r = requests.get(
            _rest_url(TABLE_CLIENTES),
            params={
                "select": "cliente_id,nombre_legal,sector,periodo,fecha_creacion,perfil_json",
                "order": "fecha_actualizacion.desc",
            },
            headers=_headers(),
            timeout=20,
        )
        if r.status_code >= 300:
            _set_last_error(
                f"Supabase load failed [{r.status_code}]: {r.text[:500]}"
            )
            return []
        rows = r.json() if isinstance(r.json(), list) else []
        out: list[dict[str, Any]] = []
        for row in rows:
            perfil = {}
            try:
                perfil = json.loads(row.get("perfil_json", "") or "{}")
            except Exception:
                perfil = {}
            out.append(
                {
                    "cliente_id": str(row.get("cliente_id", "")),
                    "nombre_legal": str(row.get("nombre_legal", "")),
                    "sector": str(row.get("sector", "")),
                    "periodo": str(row.get("periodo", "")),
                    "fecha_creacion": str(row.get("fecha_creacion", "")),
                    "perfil": perfil,
                }
            )
        _set_last_error("")
        return [x for x in out if x.get("cliente_id")]
    except Exception as e:
        _set_last_error(
            f"Supabase load error [{type(e).__name__}]: {e!r}"
        )
        return []


def eliminar_cliente_supabase(cliente_id: str) -> bool:
    try:
        if not sheets_disponible():
            return False
        r = requests.delete(
            _rest_url(TABLE_CLIENTES),
            params={"cliente_id": f"eq.{cliente_id}"},
            headers=_headers(),
            timeout=20,
        )
        if r.status_code >= 300:
            _set_last_error(
                f"Supabase delete failed [{r.status_code}]: {r.text[:500]}"
            )
            return False
        _set_last_error("")
        return True
    except Exception as e:
        _set_last_error(
            f"Supabase delete error [{type(e).__name__}]: {e!r}"
        )
        return False


def diagnosticar_sheets() -> dict[str, Any]:
    out = {
        "ok": False,
        "auth_ok": False,
        "open_ok": False,
        "sheet_ok": False,
        "read_ok": False,
        "write_ok": False,
        "spreadsheet_title": "Supabase",
        "sheet_id": "",
        "error": "",
    }
    try:
        url, key = _get_cfg()
        out["sheet_id"] = url
        if not url or not key:
            out["error"] = "Missing SUPABASE_URL or SUPABASE_ANON_KEY."
            return out
        out["auth_ok"] = True
        out["open_ok"] = True

        rows = cargar_clientes_supabase()
        out["read_ok"] = True

        probe_ok = guardar_cliente_supabase(
            "__probe__",
            {"cliente": {"nombre_legal": "probe"}, "encargo": {}},
        )
        if not probe_ok:
            out["error"] = obtener_ultimo_error_sheets()
            return out
        eliminar_cliente_supabase("__probe__")
        out["sheet_ok"] = True
        out["write_ok"] = True
        out["ok"] = True
        out["error"] = ""
        return out
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e!r}"
        _set_last_error(out["error"])
        return out


def diagnosticar_config_supabase() -> dict[str, Any]:
    """
    Returns non-sensitive debug info about detected key names.
    """
    try:
        import streamlit as st
        keys = []
        try:
            keys = list((st.secrets.to_dict()).keys())  # type: ignore[attr-defined]
        except Exception:
            try:
                keys = list(dict(st.secrets).keys())
            except Exception:
                keys = []
        # Direct key visibility check
        direct_present = {}
        for k in [
            "SUPABASE_URL", "supabase_url", "PROJECT_URL", "project_url",
            "SUPABASE_ANON_KEY", "supabase_anon_key",
            "SUPABASE_PUBLISHABLE_KEY", "supabase_publishable_key",
            "SUPABASE_KEY", "supabase_key",
        ]:
            try:
                direct_present[k] = bool(str(st.secrets.get(k, "")).strip())
            except Exception:
                direct_present[k] = False
        env_keys = [k for k in [
            "SUPABASE_URL", "PROJECT_URL", "SUPABASE_ANON_KEY",
            "SUPABASE_PUBLISHABLE_KEY", "SUPABASE_KEY"
        ] if os.environ.get(k)]
        url, key = _get_cfg()
        return {
            "secrets_keys": keys,
            "direct_present": direct_present,
            "env_keys": env_keys,
            "runtime_present": {
                "runtime_supabase_url": bool(
                    str(st.session_state.get("runtime_supabase_url", "") or "").strip()
                ),
                "runtime_supabase_key": bool(
                    str(st.session_state.get("runtime_supabase_key", "") or "").strip()
                ),
            },
            "has_url": bool(url),
            "has_key": bool(key),
        }
    except Exception as e:
        return {
            "secrets_keys": [],
            "env_keys": [],
            "has_url": False,
            "has_key": False,
            "error": f"{type(e).__name__}: {e!r}",
        }


# Backward-compatible aliases used by app_streamlit
guardar_cliente_sheets = guardar_cliente_supabase
cargar_clientes_sheets = cargar_clientes_supabase
eliminar_cliente_sheets = eliminar_cliente_supabase
