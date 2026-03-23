"""
Supabase repository for SocioAI client persistence.
Compatible with existing Sheets integration function names.
"""
from __future__ import annotations

import json
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
        supa_block = st.secrets.get("supabase", {})
        url = (
            st.secrets.get("SUPABASE_URL", "")
            or st.secrets.get("supabase_url", "")
            or st.secrets.get("PROJECT_URL", "")
            or st.secrets.get("project_url", "")
            or (supa_block.get("url", "") if hasattr(supa_block, "get") else "")
        )
        key = (
            st.secrets.get("SUPABASE_ANON_KEY", "")
            or st.secrets.get("supabase_anon_key", "")
            or st.secrets.get("SUPABASE_PUBLISHABLE_KEY", "")
            or st.secrets.get("supabase_publishable_key", "")
            or st.secrets.get("SUPABASE_KEY", "")
            or st.secrets.get("supabase_key", "")
            or st.secrets.get("ANON_KEY", "")
            or st.secrets.get("anon_key", "")
            or (supa_block.get("anon_key", "") if hasattr(supa_block, "get") else "")
            or (supa_block.get("publishable_key", "") if hasattr(supa_block, "get") else "")
            or (supa_block.get("key", "") if hasattr(supa_block, "get") else "")
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


# Backward-compatible aliases used by app_streamlit
guardar_cliente_sheets = guardar_cliente_supabase
cargar_clientes_sheets = cargar_clientes_supabase
eliminar_cliente_sheets = eliminar_cliente_supabase
