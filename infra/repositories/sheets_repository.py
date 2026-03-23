"""
Google Sheets repository for SocioAI client persistence.
Stores client profiles and TB metadata across sessions.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pandas as pd

_LAST_SHEETS_ERROR = ""


# Sheet tab names
SHEET_CLIENTES = "Clientes"
SHEET_TB_META = "tb_metadata"
SHEET_ESTADOS = "estados_areas"


def _set_last_error(msg: str) -> None:
    global _LAST_SHEETS_ERROR
    _LAST_SHEETS_ERROR = str(msg or "").strip()


def obtener_ultimo_error_sheets() -> str:
    """Returns last Sheets error captured by this repository."""
    return _LAST_SHEETS_ERROR


def _get_client():
    """Returns authenticated gspread client."""
    try:
        import gspread
        import streamlit as st
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        # Load from Streamlit secrets
        # Preferred format:
        # [gcp_service_account]
        # type = "...", project_id = "...", ...
        creds_dict: dict[str, Any] = {}
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
        else:
            # Fallback: flat keys at top-level secrets
            keys = [
                "type", "project_id", "private_key_id",
                "private_key", "client_email", "client_id",
                "auth_uri", "token_uri",
                "auth_provider_x509_cert_url",
                "client_x509_cert_url",
                "universe_domain",
            ]
            creds_dict = {
                k: st.secrets.get(k, "")
                for k in keys
                if st.secrets.get(k, "")
            }

        if not creds_dict:
            return None

        # Normalize private key newlines
        pk = str(creds_dict.get("private_key", "") or "")
        if "\\n" in pk:
            creds_dict["private_key"] = pk.replace("\\n", "\n")

        creds = Credentials.from_service_account_info(
            creds_dict, scopes=scopes
        )
        _set_last_error("")
        return gspread.authorize(creds)
    except Exception as e:
        _set_last_error(
            f"Error connecting [{type(e).__name__}]: {e!r}"
        )
        print(f"[SHEETS] Error connecting: {e}")
        return None


def _get_sheet(tab_name: str):
    """Returns a specific worksheet, creates it if missing."""
    try:
        import streamlit as st
        client = _get_client()
        if not client:
            return None

        sheet_id = (
            st.secrets.get("GOOGLE_SHEETS_ID", "")
            or st.secrets.get("google_sheets_id", "")
        )
        if not sheet_id:
            _set_last_error("Missing GOOGLE_SHEETS_ID in secrets.")
            return None

        spreadsheet = client.open_by_key(sheet_id)

        # Get existing tab (case-insensitive) or create it
        try:
            _set_last_error("")
            return spreadsheet.worksheet(tab_name)
        except Exception:
            for ws in spreadsheet.worksheets():
                if str(ws.title).strip().lower() == str(tab_name).strip().lower():
                    _set_last_error("")
                    return ws

            # Create tab with headers
            ws = spreadsheet.add_worksheet(
                title=tab_name, rows=1000, cols=20
            )
            _init_headers(ws, tab_name)
            _set_last_error("")
            return ws
    except Exception as e:
        _set_last_error(
            f"Error getting sheet {tab_name} "
            f"[{type(e).__name__}]: {e!r}"
        )
        print(f"[SHEETS] Error getting sheet {tab_name}: {e}")
        return None


def _init_headers(ws: Any, tab_name: str) -> None:
    """Initialize headers for each sheet tab."""
    headers = {
        SHEET_CLIENTES: [
            "cliente_id", "nombre_legal", "ruc",
            "sector", "tipo_entidad", "periodo",
            "marco", "riesgo_global", "moneda",
            "partes_relacionadas", "inventarios",
            "cartera", "prestamos_socios",
            "anticipos", "empleados",
            "doc_debil", "riesgo_tributario",
            "fecha_creacion", "fecha_actualizacion",
            "perfil_json",
        ],
        SHEET_TB_META: [
            "cliente_id", "tipo_tb", "filas",
            "columnas", "fecha_carga",
            "tiene_saldo_2024", "tiene_saldo_2025",
            "total_activos", "total_pasivos",
            "total_patrimonio",
        ],
        SHEET_ESTADOS: [
            "cliente_id", "codigo_area",
            "nombre_area", "estado_area",
            "decision_cierre", "conclusion",
            "notas", "pendientes",
            "fecha_actualizacion",
        ],
    }
    if tab_name in headers:
        ws.append_row(headers[tab_name])


# ── Client CRUD ───────────────────────────────────────────────
def guardar_cliente_sheets(
    cliente_id: str,
    perfil: dict[str, Any],
) -> bool:
    """Save or update a client profile in Google Sheets."""
    try:
        ws = _get_sheet(SHEET_CLIENTES)
        if not ws:
            return False

        c = perfil.get("cliente", {})
        enc = perfil.get("encargo", {})
        rg = perfil.get("riesgo_global", {})
        op = perfil.get("operacion", {})
        banderas = perfil.get("banderas_generales", {})

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        perfil_json = json.dumps(perfil, ensure_ascii=False)

        row = [
            cliente_id,
            c.get("nombre_legal", ""),
            c.get("ruc", ""),
            c.get("sector", ""),
            c.get("tipo_entidad", ""),
            str(enc.get("anio_activo", "")),
            enc.get("marco_referencial", ""),
            rg.get("nivel", ""),
            c.get("moneda_funcional", "USD"),
            str(bool(perfil.get("contexto_negocio", {})
                     .get("tiene_partes_relacionadas"))),
            str(bool(op.get("tiene_inventarios_significativos"))),
            str(bool(op.get("tiene_cartera_significativa"))),
            str(bool(op.get("tiene_prestamos_socios"))),
            str(bool(op.get("tiene_anticipos_proveedores"))),
            str(bool(perfil.get("nomina", {})
                     .get("tiene_empleados"))),
            str(bool(banderas.get("documentacion_debil"))),
            str(bool(banderas.get("riesgo_tributario_general"))),
            now,
            now,
            perfil_json,
        ]

        # Check if client already exists → update row
        existing = ws.get_all_values()
        for i, existing_row in enumerate(existing[1:], start=2):
            if existing_row and existing_row[0] == cliente_id:
                # Update existing row
                row[-2] = existing_row[-2]  # keep created date
                ws.update(range_name=f"A{i}:T{i}", values=[row])
                _set_last_error("")
                print(f"[SHEETS] Updated client: {cliente_id}")
                return True

        # New client → append
        ws.append_row(row)
        _set_last_error("")
        print(f"[SHEETS] Saved new client: {cliente_id}")
        return True

    except Exception as e:
        _set_last_error(
            f"Error saving client [{type(e).__name__}]: {e!r}"
        )
        print(f"[SHEETS] Error saving client: {e}")
        return False


def cargar_clientes_sheets() -> list[dict[str, Any]]:
    """Load all clients from Google Sheets."""
    try:
        ws = _get_sheet(SHEET_CLIENTES)
        if not ws:
            return []

        rows = ws.get_all_records()
        clientes = []
        for row in rows:
            if not row.get("cliente_id"):
                continue
            # Try to restore full perfil from JSON
            perfil_json = row.get("perfil_json", "")
            try:
                perfil = json.loads(perfil_json) if perfil_json else {}
            except Exception:
                perfil = {}

            clientes.append({
                "cliente_id": str(row["cliente_id"]),
                "nombre_legal": str(row.get("nombre_legal", "")),
                "sector": str(row.get("sector", "")),
                "periodo": str(row.get("periodo", "")),
                "fecha_creacion": str(
                    row.get("fecha_creacion", "")
                ),
                "perfil": perfil,
            })
        _set_last_error("")
        return clientes
    except Exception as e:
        _set_last_error(
            f"Error loading clients [{type(e).__name__}]: {e!r}"
        )
        print(f"[SHEETS] Error loading clients: {e}")
        return []


def eliminar_cliente_sheets(cliente_id: str) -> bool:
    """Delete a client row from Google Sheets."""
    try:
        ws = _get_sheet(SHEET_CLIENTES)
        if not ws:
            return False

        rows = ws.get_all_values()
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0] == cliente_id:
                ws.delete_rows(i)
                _set_last_error("")
                print(f"[SHEETS] Deleted client: {cliente_id}")
                return True
        return False
    except Exception as e:
        _set_last_error(
            f"Error deleting client [{type(e).__name__}]: {e!r}"
        )
        print(f"[SHEETS] Error deleting client: {e}")
        return False


def sheets_disponible() -> bool:
    """Check if Google Sheets connection works."""
    try:
        import streamlit as st
        _sid = (
            st.secrets.get("GOOGLE_SHEETS_ID", "")
            or st.secrets.get("google_sheets_id", "")
        )
        _svc = st.secrets.get("gcp_service_account", {})
        _flat = bool(
            st.secrets.get("client_email", "")
            and st.secrets.get("private_key", "")
        )
        return bool(
            _sid and (_svc or _flat)
        )
    except Exception:
        return False


def diagnosticar_sheets() -> dict[str, Any]:
    """
    Performs a read/write probe and returns diagnostic details.
    """
    out: dict[str, Any] = {
        "ok": False,
        "auth_ok": False,
        "open_ok": False,
        "sheet_ok": False,
        "read_ok": False,
        "write_ok": False,
        "spreadsheet_title": "",
        "sheet_id": "",
        "error": "",
    }
    try:
        import streamlit as st
        client = _get_client()
        if not client:
            out["error"] = obtener_ultimo_error_sheets() or "Auth failed."
            return out
        out["auth_ok"] = True

        sid = (
            st.secrets.get("GOOGLE_SHEETS_ID", "")
            or st.secrets.get("google_sheets_id", "")
        )
        out["sheet_id"] = str(sid or "")
        if not sid:
            out["error"] = "Missing GOOGLE_SHEETS_ID."
            return out

        ss = client.open_by_key(sid)
        out["open_ok"] = True
        out["spreadsheet_title"] = str(getattr(ss, "title", "") or "")

        ws = _get_sheet(SHEET_CLIENTES)
        if not ws:
            out["error"] = obtener_ultimo_error_sheets() or "Worksheet access failed."
            return out
        out["sheet_ok"] = True

        _ = ws.get_all_values()
        out["read_ok"] = True

        probe = [
            "__probe__",
            "probe",
            "",
            "",
            "",
            "",
            "",
            "",
            "USD",
            "False",
            "False",
            "False",
            "False",
            "False",
            "False",
            "False",
            "False",
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "{}",
        ]
        ws.append_row(probe)
        rows = ws.get_all_values()
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0] == "__probe__":
                ws.delete_rows(i)
                break
        out["write_ok"] = True
        out["ok"] = True
        _set_last_error("")
        return out
    except Exception as e:
        _set_last_error(
            f"Diagnostic failed [{type(e).__name__}]: {e!r}"
        )
        out["error"] = (
            f"{type(e).__name__}: {e!r}"
        )
        print(f"[SHEETS_DIAG] {out['error']}")
        return out
