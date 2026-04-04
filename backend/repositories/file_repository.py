from __future__ import annotations

import json
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from backend.constants.mapping import get_area_name
from backend.repositories.supabase_memory import store as supabase_store
from backend.validation import (
    VALID_SCHEMA_VERSION,
    normalize_area_doc_v1,
    normalize_perfil_doc_v1,
    normalize_workpapers_doc_v1,
    normalize_workflow_doc_v1,
    validate_workpapers_doc_v1,
)

ROOT = Path(__file__).resolve().parents[2]
DATA_CLIENTES = ROOT / "data" / "clientes"
CATALOGOS = ROOT / "data" / "catalogos"


class FileRepository:
    """Repositorio de archivos local para aislar el acceso a disco.

    Esta clase permite mantener la misma API de negocio cuando se migre
    a una base de datos en fases futuras.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ROOT
        self.data_clientes = self.root / "data" / "clientes"
        self.catalogos = self.root / "data" / "catalogos"

    def cliente_dir(self, cliente_id: str) -> Path:
        return self.data_clientes / cliente_id

    def _resolve_cliente_dir(self, cliente_id: str, *, for_write: bool = False) -> Path:
        cid = str(cliente_id or "").strip()
        exact = self.cliente_dir(cid)
        if exact.exists():
            return exact

        if not self.data_clientes.exists() or not cid:
            return exact

        year_pattern_exact = re.compile(rf"^{re.escape(cid)}_(20\d{{2}})$")
        year_pattern_generic = re.compile(r"^(?P<base>.+)_(?P<year>20\d{2})$")
        cid_norm = cid.lower()
        best_dir: Path | None = None
        best_year = -1
        for item in self.data_clientes.iterdir():
            if not item.is_dir():
                continue
            m = year_pattern_exact.match(item.name)
            if not m:
                mg = year_pattern_generic.match(item.name)
                if not mg:
                    continue
                base = mg.group("base").lower()
                if not (base in cid_norm or cid_norm in base):
                    continue
                year = int(mg.group("year"))
            else:
                year = int(m.group(1))
            if year > best_year:
                best_year = year
                best_dir = item

        if best_dir is not None:
            return best_dir
        return exact

    @staticmethod
    def _perfil_has_core_data(perfil: dict[str, Any]) -> bool:
        if not isinstance(perfil, dict) or not perfil:
            return False
        cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
        encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}
        return bool(
            str(cliente.get("nombre_legal") or "").strip()
            or str(cliente.get("nombre_corto") or "").strip()
            or encargo.get("anio_activo")
            or str(cliente.get("sector") or "").strip()
        )

    def list_clientes(self) -> list[str]:
        if supabase_store.is_configured():
            remote = supabase_store.list_clientes()
            if remote:
                return sorted(remote)
        if not self.data_clientes.exists():
            return []
        return sorted([p.name for p in self.data_clientes.iterdir() if p.is_dir()])

    def read_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return {}

    def read_perfil(self, cliente_id: str) -> dict[str, Any]:
        local = normalize_perfil_doc_v1(self.read_yaml(self._resolve_cliente_dir(cliente_id) / "perfil.yaml"))
        if supabase_store.is_configured():
            remote = supabase_store.fetch_single_json(
                "cliente_perfiles",
                {"cliente_id": cliente_id},
                "perfil_json",
            )
            if isinstance(remote, dict) and remote:
                remote_norm = normalize_perfil_doc_v1(remote)
                if self._perfil_has_core_data(remote_norm):
                    return remote_norm
        return local

    def write_perfil(self, cliente_id: str, data: dict[str, Any]) -> None:
        normalized = normalize_perfil_doc_v1(data)
        cdir = self._resolve_cliente_dir(cliente_id, for_write=True)
        cdir.mkdir(parents=True, exist_ok=True)
        p = cdir / "perfil.yaml"
        p.write_text(yaml.safe_dump(normalized, allow_unicode=True, sort_keys=False), encoding="utf-8")
        if supabase_store.is_configured():
            perfil_cliente = normalized.get("cliente", {}) if isinstance(normalized.get("cliente"), dict) else {}
            supabase_store.upsert_row(
                "clientes",
                {
                    "cliente_id": cliente_id,
                    "nombre": str(perfil_cliente.get("nombre_legal") or cliente_id),
                    "sector": str(perfil_cliente.get("sector") or ""),
                    "schema_version": VALID_SCHEMA_VERSION,
                },
                on_conflict="cliente_id",
            )
            supabase_store.upsert_row(
                "cliente_perfiles",
                {
                    "cliente_id": cliente_id,
                    "perfil_json": normalized,
                    "schema_version": VALID_SCHEMA_VERSION,
                },
                on_conflict="cliente_id",
            )

    def read_hallazgos(self, cliente_id: str) -> str:
        if supabase_store.is_configured():
            remote = supabase_store.fetch_single_json(
                "cliente_hallazgos",
                {"cliente_id": cliente_id},
                "hallazgos_json",
            )
            if isinstance(remote, dict):
                text = str(remote.get("markdown") or "").strip()
                if text:
                    return text
        p = self._resolve_cliente_dir(cliente_id) / "hallazgos.md"
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8")

    def append_hallazgo(self, cliente_id: str, content: str) -> None:
        cdir = self._resolve_cliente_dir(cliente_id, for_write=True)
        cdir.mkdir(parents=True, exist_ok=True)
        p = cdir / "hallazgos.md"
        previous = p.read_text(encoding="utf-8") if p.exists() else ""
        new_text = (previous + "\n\n" + content).strip() + "\n"
        p.write_text(new_text, encoding="utf-8")
        if supabase_store.is_configured():
            supabase_store.upsert_row(
                "cliente_hallazgos",
                {
                    "cliente_id": cliente_id,
                    "hallazgos_json": {"markdown": new_text},
                    "schema_version": VALID_SCHEMA_VERSION,
                },
                on_conflict="cliente_id",
            )

    def read_catalog_file(self, path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def list_area_files(self, cliente_id: str) -> list[Path]:
        areas_dir = self._resolve_cliente_dir(cliente_id) / "areas"
        if not areas_dir.exists():
            return []
        return sorted(areas_dir.glob("*.yaml"))

    def list_area_codes(self, cliente_id: str) -> list[str]:
        codes: list[str] = []
        if supabase_store.is_configured():
            rows = supabase_store.fetch_rows(
                "cliente_areas",
                filters={"cliente_id": cliente_id},
                select="area_code",
            )
            for row in rows:
                code = str(row.get("area_code") or "").strip()
                if code:
                    codes.append(code)
        if not codes:
            for path in self.list_area_files(cliente_id):
                codes.append(path.stem)
        return sorted(set(codes))

    def read_area_yaml(self, cliente_id: str, area_ls: str) -> dict[str, Any]:
        if supabase_store.is_configured():
            remote = supabase_store.fetch_single_json(
                "cliente_areas",
                {"cliente_id": cliente_id, "area_code": area_ls},
                "area_json",
            )
            if isinstance(remote, dict) and remote:
                return normalize_area_doc_v1(remote, area_code=area_ls)
        p = self._resolve_cliente_dir(cliente_id) / "areas" / f"{area_ls}.yaml"
        return normalize_area_doc_v1(self.read_yaml(p), area_code=area_ls)

    def write_area_yaml(self, cliente_id: str, area_code: str, data: dict[str, Any]) -> None:
        normalized = normalize_area_doc_v1(data, area_code=area_code)
        cdir = self._resolve_cliente_dir(cliente_id, for_write=True) / "areas"
        cdir.mkdir(parents=True, exist_ok=True)
        p = cdir / f"{area_code}.yaml"
        p.write_text(yaml.safe_dump(normalized, allow_unicode=True, sort_keys=False), encoding="utf-8")
        if supabase_store.is_configured():
            supabase_store.upsert_row(
                "cliente_areas",
                {
                    "cliente_id": cliente_id,
                    "area_code": area_code,
                    "area_json": normalized,
                    "schema_version": VALID_SCHEMA_VERSION,
                },
                on_conflict="cliente_id,area_code",
            )

    def read_workpapers(self, cliente_id: str) -> list[dict[str, Any]]:
        if supabase_store.is_configured():
            remote = supabase_store.fetch_single_json(
                "cliente_workpapers",
                {"cliente_id": cliente_id},
                "workpapers_json",
            )
            if isinstance(remote, dict):
                normalized_remote = normalize_workpapers_doc_v1(remote, cliente_id=cliente_id)
                tasks_remote = normalized_remote.get("tasks")
                if isinstance(tasks_remote, list):
                    return [t for t in tasks_remote if isinstance(t, dict)]
        p = self._resolve_cliente_dir(cliente_id) / "papeles_trabajo.yaml"
        data = self.read_yaml(p)
        normalized = normalize_workpapers_doc_v1(data if isinstance(data, dict) else {}, cliente_id=cliente_id)
        tasks = normalized.get("tasks")
        if not isinstance(tasks, list):
            return []
        return [t for t in tasks if isinstance(t, dict)]

    def read_workflow(self, cliente_id: str) -> dict[str, Any]:
        if supabase_store.is_configured():
            remote = supabase_store.fetch_single_json(
                "cliente_workflow",
                {"cliente_id": cliente_id},
                "workflow_json",
            )
            if isinstance(remote, dict):
                return remote
        p = self._resolve_cliente_dir(cliente_id) / "workflow.yaml"
        data = self.read_yaml(p)
        return data if isinstance(data, dict) else {}

    def write_workflow(self, cliente_id: str, state: dict[str, Any]) -> None:
        cdir = self._resolve_cliente_dir(cliente_id, for_write=True)
        cdir.mkdir(parents=True, exist_ok=True)
        p = cdir / "workflow.yaml"
        p.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
        if supabase_store.is_configured():
            supabase_store.upsert_row(
                "cliente_workflow",
                {
                    "cliente_id": cliente_id,
                    "workflow_json": state,
                    "schema_version": VALID_SCHEMA_VERSION,
                },
                on_conflict="cliente_id",
            )

    def write_workpapers(self, cliente_id: str, tasks: list[dict[str, Any]]) -> None:
        payload = normalize_workpapers_doc_v1({"tasks": tasks}, cliente_id=cliente_id)
        is_valid, _ = validate_workpapers_doc_v1(payload, cliente_id=cliente_id)
        if not is_valid:
            # Fallback defensivo: persistimos igualmente en disco con formato minimo normalizado.
            payload = normalize_workpapers_doc_v1({"tasks": tasks}, cliente_id=cliente_id)

        cdir = self._resolve_cliente_dir(cliente_id, for_write=True)
        cdir.mkdir(parents=True, exist_ok=True)
        p = cdir / "papeles_trabajo.yaml"
        p.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
        if supabase_store.is_configured():
            supabase_store.upsert_row(
                "cliente_workpapers",
                {
                    "cliente_id": cliente_id,
                    "workpapers_json": payload,
                    "schema_version": VALID_SCHEMA_VERSION,
                },
                on_conflict="cliente_id",
            )

    def memo_path(self, cliente_id: str) -> Path:
        return self._resolve_cliente_dir(cliente_id) / "memo_ejecutivo.md"

    def read_memo(self, cliente_id: str) -> str:
        if supabase_store.is_configured():
            remote = supabase_store.fetch_single_json(
                "cliente_hallazgos",
                {"cliente_id": cliente_id},
                "hallazgos_json",
            )
            if isinstance(remote, dict):
                memo = str(remote.get("memo_ejecutivo") or "").strip()
                if memo:
                    return memo
        p = self.memo_path(cliente_id)
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8").strip()

    def write_memo(self, cliente_id: str, content: str) -> None:
        cdir = self._resolve_cliente_dir(cliente_id, for_write=True)
        cdir.mkdir(parents=True, exist_ok=True)
        self.memo_path(cliente_id).write_text(content.strip() + "\n", encoding="utf-8")
        if supabase_store.is_configured():
            current = supabase_store.fetch_single_json(
                "cliente_hallazgos",
                {"cliente_id": cliente_id},
                "hallazgos_json",
            ) or {}
            if not isinstance(current, dict):
                current = {}
            current["memo_ejecutivo"] = content.strip()
            supabase_store.upsert_row(
                "cliente_hallazgos",
                {
                    "cliente_id": cliente_id,
                    "hallazgos_json": current,
                    "schema_version": VALID_SCHEMA_VERSION,
                },
                on_conflict="cliente_id",
            )

    def read_chat_history(self, cliente_id: str) -> list[dict[str, Any]]:
        p = self._resolve_cliente_dir(cliente_id) / "chat_history.json"
        if not p.exists():
            return []
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return []
        if not isinstance(data, list):
            return []
        out: list[dict[str, Any]] = []
        for row in data:
            if isinstance(row, dict):
                out.append(row)
        return out[-200:]

    def append_chat_message(self, cliente_id: str, message: dict[str, Any]) -> None:
        cdir = self._resolve_cliente_dir(cliente_id, for_write=True)
        cdir.mkdir(parents=True, exist_ok=True)
        history = self.read_chat_history(cliente_id)
        row = dict(message)
        if "timestamp" not in row:
            row["timestamp"] = datetime.now(timezone.utc).isoformat()
        history.append(row)
        p = cdir / "chat_history.json"
        p.write_text(json.dumps(history[-200:], ensure_ascii=False, indent=2), encoding="utf-8")

    def list_documentos(self, cliente_id: str) -> list[dict[str, Any]]:
        cdir = self._resolve_cliente_dir(cliente_id)
        docs_dir = cdir / "documentos"
        docs_dir.mkdir(parents=True, exist_ok=True)

        out: list[dict[str, Any]] = []

        def _kind_for_file(path: Path) -> str:
            name = path.name.lower()
            if name == "tb.xlsx":
                return "trial_balance"
            if name == "mayor.xlsx":
                return "libro_mayor"
            if path.suffix.lower() in {".pdf"}:
                return "pdf"
            if path.suffix.lower() in {".xlsx", ".xls", ".csv"}:
                return "spreadsheet"
            if path.suffix.lower() in {".md", ".txt"}:
                return "note"
            return "documento"

        for path in [cdir / "tb.xlsx", cdir / "mayor.xlsx"]:
            if not path.exists():
                continue
            stat = path.stat()
            out.append(
                {
                    "id": path.name,
                    "name": path.name,
                    "kind": _kind_for_file(path),
                    "uploaded_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    "path": str(path),
                }
            )

        for path in sorted(docs_dir.glob("*")):
            if not path.is_file():
                continue
            stat = path.stat()
            out.append(
                {
                    "id": path.name,
                    "name": path.name,
                    "kind": _kind_for_file(path),
                    "uploaded_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    "path": str(path),
                }
            )

        out.sort(key=lambda x: x["uploaded_at"], reverse=True)
        return out

    def create_cliente(self, *, cliente_id: str, nombre: str, sector: str | None = None) -> dict[str, Any]:
        cid = slugify_cliente_id(cliente_id) if cliente_id else slugify_cliente_id(nombre)
        if not cid:
            raise ValueError("cliente_id invalido")

        cdir = self.cliente_dir(cid)
        if cdir.exists():
            raise FileExistsError(f"El cliente '{cid}' ya existe")

        cdir.mkdir(parents=True, exist_ok=False)
        perfil = {
            "cliente": {
                "nombre_legal": nombre.strip(),
                "nombre_corto": nombre.strip(),
                "sector": (sector or "").strip() or "Holding",
                "pais": "Ecuador",
            },
            "encargo": {
                "anio_activo": datetime.now(timezone.utc).year,
                "marco_referencial": "NIIF para PYMES",
                "norma_auditoria": "NIAs",
                "fase_actual": "planificacion",
            },
            "materialidad": {
                "estado_materialidad": "preliminar",
                "preliminar": {
                    "materialidad_global": 0.0,
                    "materialidad_desempeno": 0.0,
                    "error_trivial": 0.0,
                },
                "final": {
                    "materialidad_planeacion": None,
                    "materialidad_ejecucion": None,
                    "umbral_trivialidad": None,
                },
            },
            "riesgo_global": {"nivel": "medio"},
            "cuestionario_auditoria": {
                "nomina": False,
                "inventarios": False,
                "ingresos_complejos": False,
                "partes_relacionadas": False,
                "multi_moneda": False,
            },
        }
        self.write_perfil(cid, perfil)
        return {"cliente_id": cid, "nombre": nombre.strip(), "sector": perfil["cliente"]["sector"]}

    def delete_cliente(self, cliente_id: str) -> bool:
        target = self.cliente_dir(cliente_id).resolve()
        base = self.data_clientes.resolve()
        if not str(target).startswith(str(base)):
            return False
        if not target.exists():
            if not supabase_store.is_configured():
                return False
        else:
            shutil.rmtree(target)
        if supabase_store.is_configured():
            supabase_store.delete_where("cliente_perfiles", {"cliente_id": cliente_id})
            supabase_store.delete_where("cliente_areas", {"cliente_id": cliente_id})
            supabase_store.delete_where("cliente_workflow", {"cliente_id": cliente_id})
            supabase_store.delete_where("cliente_workpapers", {"cliente_id": cliente_id})
            supabase_store.delete_where("cliente_hallazgos", {"cliente_id": cliente_id})
            supabase_store.delete_where("clientes", {"cliente_id": cliente_id})
        return True

    def _read_tb(self, cliente_id: str) -> list[dict[str, Any]]:
        tb_path = self._resolve_cliente_dir(cliente_id) / "tb.xlsx"
        if not tb_path.exists() or tb_path.stat().st_size == 0:
            return []

        try:
            import pandas as pd

            df = pd.read_excel(tb_path, engine="openpyxl")
        except Exception:
            return []

        if df.empty:
            return []

        return df.fillna(0).to_dict(orient="records")

    @staticmethod
    def _normalize_ls(value: Any) -> str:
        raw = str(value).strip()
        if not raw:
            return ""
        if raw.endswith(".0"):
            raw = raw[:-2]
        return raw

    def _saldo_columns(self, rows: list[dict[str, Any]]) -> tuple[str | None, str | None, str, str]:
        if not rows:
            return None, None, "Actual", "Anterior"

        keys = list(rows[0].keys())
        saldo_cols = [k for k in keys if isinstance(k, str) and k.lower().startswith("saldo")]

        def _col_abs_sum(col: str) -> float:
            total = 0.0
            for row in rows:
                try:
                    total += abs(float(row.get(col, 0.0) or 0.0))
                except Exception:
                    continue
            return total

        year_pairs: list[tuple[int, str]] = []
        for col in saldo_cols:
            match = re.search(r"(20\d{2})", col)
            if match:
                year_pairs.append((int(match.group(1)), col))

        if year_pairs:
            year_pairs.sort(key=lambda x: x[0], reverse=True)
            current_year, current_col = year_pairs[0]
            current_nonzero = _col_abs_sum(current_col) > 0.0

            if current_nonzero:
                if len(year_pairs) > 1:
                    previous_year, previous_col = year_pairs[1]
                else:
                    previous_year, previous_col = current_year - 1, None
                return current_col, previous_col, str(current_year), str(previous_year)

            preliminar_col = next((c for c in saldo_cols if "preliminar" in c.lower()), None)
            if preliminar_col and _col_abs_sum(preliminar_col) > 0.0:
                if len(year_pairs) > 1:
                    previous_year, previous_col = year_pairs[1]
                else:
                    previous_year, previous_col = current_year - 1, None
                return preliminar_col, previous_col, "Preliminar", str(previous_year)

            if len(year_pairs) > 1:
                previous_year, previous_col = year_pairs[1]
                return previous_col, None, str(previous_year), str(previous_year - 1)

        if len(saldo_cols) >= 2:
            return saldo_cols[-1], saldo_cols[-2], "Actual", "Anterior"
        if len(saldo_cols) == 1:
            return saldo_cols[0], None, "Actual", "Anterior"
        return None, None, "Actual", "Anterior"

    def _find_aseveraciones(self, area_ls: str) -> list[dict[str, Any]]:
        path = self.catalogos / "afirmaciones_por_area.yaml"
        all_data = self.read_yaml(path)
        if not all_data:
            return []

        area = all_data.get(area_ls)
        if not isinstance(area, dict):
            # Fallback por prefijo (ej: 130.1 toma 130)
            prefix = area_ls.split(".")[0]
            area = all_data.get(prefix, {})

        afirmaciones = area.get("afirmaciones") if isinstance(area, dict) else []
        if not isinstance(afirmaciones, list):
            return []

        out: list[dict[str, Any]] = []
        for item in afirmaciones:
            if not isinstance(item, dict):
                continue
            out.append(
                {
                    "nombre": str(item.get("nombre", "")).strip(),
                    "descripcion": str(item.get("descripcion", "")).strip(),
                    "riesgo_tipico": str(item.get("riesgo_tipico", "medio")).strip().lower(),
                    "procedimiento_clave": str(item.get("procedimiento_clave", "")).strip(),
                }
            )
        return out

    def get_area_detail(self, cliente_id: str, area_code: str) -> dict[str, Any]:
        """Retorno estable para frontend (independiente del origen de datos)."""
        area_data = self.read_area_yaml(cliente_id, area_code)
        perfil = self.read_perfil(cliente_id)
        tb_rows = self._read_tb(cliente_id)
        current_col, previous_col, current_year, previous_year = self._saldo_columns(tb_rows)

        checks = area_data.get("revision_checks")
        checks_map = checks if isinstance(checks, dict) else {}

        cuentas: list[dict[str, Any]] = []
        for row in tb_rows:
            ls = self._normalize_ls(row.get("L/S", ""))
            if not ls:
                continue
            if ls == area_code or ls.startswith(f"{area_code}."):
                codigo = str(row.get("Numero de Cuenta", "")).strip()
                saldo_actual = float(row.get(current_col, 0.0) or 0.0) if current_col else 0.0
                saldo_anterior = float(row.get(previous_col, 0.0) or 0.0) if previous_col else 0.0
                cuentas.append(
                    {
                        "codigo": codigo,
                        "nombre": str(row.get("Nombre Cuenta", "")).strip(),
                        "saldo_actual": round(saldo_actual, 2),
                        "saldo_anterior": round(saldo_anterior, 2),
                        "nivel": 1 if codigo.count(".") <= 2 else 2,
                        "checked": bool(checks_map.get(codigo, False)),
                    }
                )

        responsable = (
            str(perfil.get("encargo", {}).get("encargado_asignado") or "").strip()
            or str(perfil.get("encargo", {}).get("socio_asignado") or "").strip()
            or "Sin asignar"
        )
        estatus = str(area_data.get("estado_area") or "pendiente")
        nombre_area = get_area_name(area_code, str(area_data.get("nombre") or f"Área {area_code}"))

        return {
            "encabezado": {
                "area_code": area_code,
                "nombre": nombre_area,
                "responsable": responsable,
                "estatus": estatus,
                "actual_year": current_year,
                "anterior_year": previous_year,
            },
            "cuentas": cuentas,
            "aseveraciones": self._find_aseveraciones(area_code),
        }

    def set_area_account_check(self, cliente_id: str, area_code: str, cuenta_codigo: str, checked: bool) -> dict[str, Any]:
        area_data = self.read_area_yaml(cliente_id, area_code)
        checks = area_data.get("revision_checks")
        checks_map = checks if isinstance(checks, dict) else {}
        checks_map[str(cuenta_codigo)] = bool(checked)
        area_data["revision_checks"] = checks_map
        self.write_area_yaml(cliente_id, area_code, area_data)
        return {"cuenta_codigo": str(cuenta_codigo), "checked": bool(checked)}

    def read_area_workspace(self, cliente_id: str, area_ls: str) -> dict[str, Any]:
        area_data = self.read_area_yaml(cliente_id, area_ls)
        tb_rows = self._read_tb(cliente_id)
        current_col, previous_col, current_year, previous_year = self._saldo_columns(tb_rows)

        filtered_rows: list[dict[str, Any]] = []
        for row in tb_rows:
            ls = self._normalize_ls(row.get("L/S", ""))
            if not ls:
                continue
            if ls == area_ls or ls.startswith(f"{area_ls}."):
                current_amount = float(row.get(current_col, 0.0) or 0.0) if current_col else 0.0
                previous_amount = float(row.get(previous_col, 0.0) or 0.0) if previous_col else 0.0
                filtered_rows.append(
                    {
                        "cuenta": str(row.get("Numero de Cuenta", "")).strip(),
                        "nombre": str(row.get("Nombre Cuenta", "")).strip(),
                        "actual": current_amount,
                        "anterior": previous_amount,
                        "variacion_monto": current_amount - previous_amount,
                        "variacion_pct": ((current_amount - previous_amount) / abs(previous_amount) * 100.0) if previous_amount else 0.0,
                        "nivel": 1 if "." not in str(row.get("Numero de Cuenta", "")) else 2,
                    }
                )

        actual_total = sum(x["actual"] for x in filtered_rows)
        previous_total = sum(x["anterior"] for x in filtered_rows)
        variacion_monto = actual_total - previous_total
        variacion_pct = (variacion_monto / abs(previous_total) * 100.0) if previous_total else 0.0

        hallazgos = area_data.get("hallazgos_abiertos")
        pendientes = area_data.get("pendientes_clave")
        hallazgos_count = len(hallazgos) if isinstance(hallazgos, list) else 0
        pendientes_count = len(pendientes) if isinstance(pendientes, list) else 0

        risk_level = "bajo"
        if hallazgos_count > 0 or pendientes_count > 2:
            risk_level = "alto"
        elif pendientes_count > 0:
            risk_level = "medio"

        riesgos: list[dict[str, Any]] = []
        if isinstance(hallazgos, list):
            for h in hallazgos:
                if isinstance(h, dict):
                    riesgos.append(
                        {
                            "nivel": "alto",
                            "titulo": str(h.get("id") or "Hallazgo"),
                            "descripcion": str(h.get("descripcion") or "").strip(),
                        }
                    )

        if not riesgos:
            riesgos.append(
                {
                    "nivel": risk_level,
                    "titulo": "Riesgo de variación material",
                    "descripcion": "Analizar coherencia de movimientos del periodo y soportes de cierre.",
                }
            )

        return {
            "cliente_id": cliente_id,
            "area_ls": area_ls,
            "area_name": str(area_data.get("nombre") or f"Área {area_ls}"),
            "saldos": {
                "actual_year": current_year,
                "previous_year": previous_year,
                "actual_total": round(actual_total, 2),
                "previous_total": round(previous_total, 2),
            },
            "variaciones": {
                "monto": round(variacion_monto, 2),
                "porcentaje": round(variacion_pct, 2),
            },
            "riesgos": riesgos,
            "aseveraciones": self._find_aseveraciones(area_ls),
            "lead_schedule": filtered_rows,
        }


repo = FileRepository()


def list_clientes() -> list[str]:
    return repo.list_clientes()


def read_perfil(cliente_id: str) -> dict[str, Any]:
    return repo.read_perfil(cliente_id)


def write_perfil(cliente_id: str, data: dict[str, Any]) -> None:
    repo.write_perfil(cliente_id, data)
    # Mantiene sincronizado el cache de perfil usado por servicios de dominio.
    try:
        from domain.services.leer_perfil import set_perfil_cache

        set_perfil_cache(cliente_id, data)
    except Exception:
        pass


def read_hallazgos(cliente_id: str) -> str:
    return repo.read_hallazgos(cliente_id)


def append_hallazgo(cliente_id: str, content: str) -> None:
    repo.append_hallazgo(cliente_id, content)


def read_catalog_file(path: Path) -> str:
    return repo.read_catalog_file(path)


def read_workpapers(cliente_id: str) -> list[dict[str, Any]]:
    return repo.read_workpapers(cliente_id)


def write_workpapers(cliente_id: str, tasks: list[dict[str, Any]]) -> None:
    repo.write_workpapers(cliente_id, tasks)


def read_workflow(cliente_id: str) -> dict[str, Any]:
    return repo.read_workflow(cliente_id)


def write_workflow(cliente_id: str, state: dict[str, Any]) -> None:
    repo.write_workflow(cliente_id, state)


def read_memo(cliente_id: str) -> str:
    return repo.read_memo(cliente_id)


def write_memo(cliente_id: str, content: str) -> None:
    repo.write_memo(cliente_id, content)


def read_chat_history(cliente_id: str) -> list[dict[str, Any]]:
    return repo.read_chat_history(cliente_id)


def append_chat_message(cliente_id: str, message: dict[str, Any]) -> None:
    repo.append_chat_message(cliente_id, message)


def list_documentos(cliente_id: str) -> list[dict[str, Any]]:
    return repo.list_documentos(cliente_id)


def read_area_yaml(cliente_id: str, area_code: str) -> dict[str, Any]:
    return repo.read_area_yaml(cliente_id, area_code)


def list_area_codes(cliente_id: str) -> list[str]:
    return repo.list_area_codes(cliente_id)


def create_cliente(*, cliente_id: str, nombre: str, sector: str | None = None) -> dict[str, Any]:
    created = repo.create_cliente(cliente_id=cliente_id, nombre=nombre, sector=sector)
    try:
        from domain.services.leer_perfil import set_perfil_cache

        set_perfil_cache(created.get("cliente_id", ""), read_perfil(created.get("cliente_id", "")))
    except Exception:
        pass
    return created


def slugify_cliente_id(raw: str) -> str:
    text = str(raw or "").strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:50]


def deep_merge_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge_dict(out[key], value)
        else:
            out[key] = value
    return out


def delete_cliente(cliente_id: str) -> bool:
    deleted = repo.delete_cliente(cliente_id)
    if deleted:
        try:
            from domain.services.leer_perfil import clear_perfil_cache

            clear_perfil_cache(cliente_id)
        except Exception:
            pass
    return deleted


def append_audit_log(*, user_id: str, cliente_id: str, endpoint: str, extra: dict[str, Any] | None = None) -> None:
    log_path = ROOT / "backend" / "audit.log"
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "cliente_id": cliente_id,
        "endpoint": endpoint,
        "extra": extra or {},
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
