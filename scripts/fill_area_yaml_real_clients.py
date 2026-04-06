from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from backend.repositories.file_repository import repo

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "data" / "catalogos" / "afirmaciones_por_area.yaml"


def _load_catalog() -> dict[str, Any]:
    try:
        data = yaml.safe_load(CATALOGO.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _afirmaciones_for_area(area_code: str, catalog: dict[str, Any]) -> list[str]:
    if area_code in catalog and isinstance(catalog[area_code], dict):
        row = catalog[area_code]
    else:
        row = None
        for k, v in catalog.items():
            if not isinstance(k, str) or not isinstance(v, dict):
                continue
            if k.startswith(f"{area_code}.") or area_code.startswith(f"{k}."):
                row = v
                break
    afirmaciones: list[str] = []
    if isinstance(row, dict):
        for item in row.get("afirmaciones") or []:
            if isinstance(item, dict):
                name = str(item.get("nombre") or "").strip().lower()
                if name:
                    afirmaciones.append(name)
    seen: set[str] = set()
    out: list[str] = []
    for a in afirmaciones:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def _materialidad_planeacion(perfil: dict[str, Any]) -> float:
    materialidad = perfil.get("materialidad") if isinstance(perfil.get("materialidad"), dict) else {}
    final = materialidad.get("final") if isinstance(materialidad.get("final"), dict) else {}
    prelim = materialidad.get("preliminar") if isinstance(materialidad.get("preliminar"), dict) else {}
    for key in ["materialidad_planeacion", "materialidad_global"]:
        try:
            val = float(final.get(key) or 0)
            if val > 0:
                return val
        except Exception:
            pass
    try:
        return float(prelim.get("materialidad_global") or 0)
    except Exception:
        return 0.0


def _normalize_marco(raw: str) -> str:
    text = str(raw or "").lower()
    if "pyme" in text:
        return "niif_pymes"
    if "completa" in text:
        return "niif_completas"
    return "ambos"


def _target_clients() -> list[str]:
    out: list[str] = []
    for cid in repo.list_clientes():
        if cid == "cliente_demo":
            continue
        if cid.endswith("_2025") or cid.endswith("_2024"):
            out.append(cid)
    return sorted(out)


def main() -> None:
    catalog = _load_catalog()
    clients = _target_clients()
    print(f"Clientes objetivo: {clients}")
    total_updated = 0
    for cliente_id in clients:
        perfil = repo.read_perfil(cliente_id)
        encargo = perfil.get("encargo") if isinstance(perfil.get("encargo"), dict) else {}
        marco = _normalize_marco(str(encargo.get("marco_referencial") or ""))
        etapa = str(encargo.get("fase_actual") or "ejecucion").strip().lower()
        mat = _materialidad_planeacion(perfil)

        for area_code in repo.list_area_codes(cliente_id):
            area = repo.read_area_yaml(cliente_id, area_code)
            area.setdefault("codigo", str(area_code))
            area.setdefault("nombre", f"Area {area_code}")
            area.setdefault("estado_area", "pendiente")

            afirm = area.get("afirmaciones_criticas")
            if not isinstance(afirm, list) or not afirm:
                afirm = _afirmaciones_for_area(str(area_code), catalog)
            area["afirmaciones_criticas"] = [str(x).strip().lower() for x in afirm if str(x).strip()][:4]

            if not str(area.get("riesgo") or "").strip():
                hallazgos_abiertos = area.get("hallazgos_abiertos") if isinstance(area.get("hallazgos_abiertos"), list) else []
                pendientes = area.get("pendientes_clave") if isinstance(area.get("pendientes_clave"), list) else []
                area["riesgo"] = "alto" if hallazgos_abiertos or pendientes else "medio"

            area.setdefault("materialidad_area", mat)
            area.setdefault("marco", marco)
            area.setdefault("etapa", etapa)
            area.setdefault("patrones_historicos", [])

            hallazgos_previos = area.get("hallazgos_previos")
            if not isinstance(hallazgos_previos, list) or not hallazgos_previos:
                hallazgos_previos = []
                for h in area.get("hallazgos_abiertos") or []:
                    if isinstance(h, dict):
                        txt = str(h.get("descripcion") or "").strip()
                        if txt:
                            hallazgos_previos.append(txt)
            area["hallazgos_previos"] = hallazgos_previos[:5]

            repo.write_area_yaml(cliente_id, str(area_code), area)
            total_updated += 1
            print(f"Actualizada area {area_code} en {cliente_id}")

    print(f"Total areas actualizadas: {total_updated}")


if __name__ == "__main__":
    main()
