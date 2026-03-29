from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from backend.constants.mapping import get_area_name

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

    def list_clientes(self) -> list[str]:
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
        return self.read_yaml(self.cliente_dir(cliente_id) / "perfil.yaml")

    def write_perfil(self, cliente_id: str, data: dict[str, Any]) -> None:
        cdir = self.cliente_dir(cliente_id)
        cdir.mkdir(parents=True, exist_ok=True)
        p = cdir / "perfil.yaml"
        p.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def read_hallazgos(self, cliente_id: str) -> str:
        p = self.cliente_dir(cliente_id) / "hallazgos.md"
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8")

    def append_hallazgo(self, cliente_id: str, content: str) -> None:
        cdir = self.cliente_dir(cliente_id)
        cdir.mkdir(parents=True, exist_ok=True)
        p = cdir / "hallazgos.md"
        previous = p.read_text(encoding="utf-8") if p.exists() else ""
        new_text = (previous + "\n\n" + content).strip() + "\n"
        p.write_text(new_text, encoding="utf-8")

    def read_catalog_file(self, path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def list_area_files(self, cliente_id: str) -> list[Path]:
        areas_dir = self.cliente_dir(cliente_id) / "areas"
        if not areas_dir.exists():
            return []
        return sorted(areas_dir.glob("*.yaml"))

    def read_area_yaml(self, cliente_id: str, area_ls: str) -> dict[str, Any]:
        p = self.cliente_dir(cliente_id) / "areas" / f"{area_ls}.yaml"
        return self.read_yaml(p)

    def write_area_yaml(self, cliente_id: str, area_code: str, data: dict[str, Any]) -> None:
        cdir = self.cliente_dir(cliente_id) / "areas"
        cdir.mkdir(parents=True, exist_ok=True)
        p = cdir / f"{area_code}.yaml"
        p.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def delete_cliente(self, cliente_id: str) -> bool:
        target = self.cliente_dir(cliente_id).resolve()
        base = self.data_clientes.resolve()
        if not str(target).startswith(str(base)):
            return False
        if not target.exists():
            return False
        shutil.rmtree(target)
        return True

    def _read_tb(self, cliente_id: str) -> list[dict[str, Any]]:
        tb_path = self.cliente_dir(cliente_id) / "tb.xlsx"
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


def read_hallazgos(cliente_id: str) -> str:
    return repo.read_hallazgos(cliente_id)


def append_hallazgo(cliente_id: str, content: str) -> None:
    repo.append_hallazgo(cliente_id, content)


def read_catalog_file(path: Path) -> str:
    return repo.read_catalog_file(path)


def delete_cliente(cliente_id: str) -> bool:
    return repo.delete_cliente(cliente_id)


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
