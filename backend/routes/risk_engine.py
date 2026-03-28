from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends

from backend.auth import authorize_cliente_access, get_current_user
from backend.schemas import ApiResponse, RiskCriticalArea, RiskEngineResponse, RiskMatrixCell, UserContext

router = APIRouter(prefix="/risk-engine", tags=["risk-engine"])


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data
    return {}


def _normalize_level(score: float) -> str:
    if score >= 80:
        return "ALTO"
    if score >= 55:
        return "MEDIO"
    return "BAJO"


def _compute_score(area_data: dict[str, Any]) -> tuple[float, int, int]:
    hallazgos = area_data.get("hallazgos_abiertos")
    procedimientos = area_data.get("procedimientos")

    hallazgos_count = len(hallazgos) if isinstance(hallazgos, list) else 0
    pendientes_count = 0
    if isinstance(procedimientos, list):
        for proc in procedimientos:
            if not isinstance(proc, dict):
                continue
            estado = str(proc.get("estado", "")).strip().lower()
            if estado in {"pendiente", "planificado", "en_proceso"}:
                pendientes_count += 1

    score = 35.0 + (hallazgos_count * 22.0) + min(pendientes_count * 6.0, 30.0)
    score = max(8.0, min(99.0, score))
    return score, hallazgos_count, pendientes_count


def _score_to_axes(score: float) -> tuple[int, int]:
    impacto = max(1, min(5, int(round(score / 20.0))))
    frecuencia = max(1, min(5, int(round((score * 0.8) / 20.0)) + 1))
    return frecuencia, impacto


def _build_matrix_cells(areas: list[RiskCriticalArea]) -> list[list[RiskMatrixCell]]:
    grid: list[list[RiskMatrixCell]] = []
    by_pos: dict[tuple[int, int], RiskCriticalArea] = {}

    for item in areas:
        key = (item.frecuencia, item.impacto)
        current = by_pos.get(key)
        if current is None or item.score > current.score:
            by_pos[key] = item

    for row in range(5, 0, -1):
        matrix_row: list[RiskMatrixCell] = []
        for col in range(1, 6):
            found = by_pos.get((row, col))
            score = found.score if found else float((row * col) * 3)
            nivel = _normalize_level(score)
            matrix_row.append(
                RiskMatrixCell(
                    row=6 - row,
                    col=col - 1,
                    frecuencia=row,
                    impacto=col,
                    score=round(score, 2),
                    nivel=nivel,
                    area_id=found.area_id if found else None,
                    area_nombre=found.area_nombre if found else None,
                )
            )
        grid.append(matrix_row)
    return grid


@router.get("/{cliente_id}", response_model=ApiResponse)
def get_risk_engine(cliente_id: str, user: UserContext = Depends(get_current_user)) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    cliente_root = Path(__file__).resolve().parents[2] / "data" / "clientes" / cliente_id
    areas_dir = cliente_root / "areas"
    critical_areas: list[RiskCriticalArea] = []

    if areas_dir.exists():
        for area_file in sorted(areas_dir.glob("*.yaml")):
            area_data = _safe_read_yaml(area_file)
            if not area_data:
                continue

            score, hallazgos_count, _pendientes_count = _compute_score(area_data)
            area_id = str(area_data.get("codigo") or area_file.stem)
            area_name = str(area_data.get("nombre") or f"Área {area_id}")
            frecuencia, impacto = _score_to_axes(score)
            critical_areas.append(
                RiskCriticalArea(
                    area_id=area_id,
                    area_nombre=area_name,
                    score=round(score, 2),
                    nivel=_normalize_level(score),
                    frecuencia=frecuencia,
                    impacto=impacto,
                    hallazgos_abiertos=_to_int(hallazgos_count, 0),
                )
            )

    if not critical_areas:
        # Fallback para clientes sin archivos por área.
        critical_areas = [
            RiskCriticalArea(
                area_id="14",
                area_nombre="Inversiones no corrientes",
                score=72.0,
                nivel="MEDIO",
                frecuencia=4,
                impacto=4,
                hallazgos_abiertos=0,
            ),
            RiskCriticalArea(
                area_id="200",
                area_nombre="Patrimonio",
                score=65.0,
                nivel="MEDIO",
                frecuencia=4,
                impacto=3,
                hallazgos_abiertos=0,
            ),
            RiskCriticalArea(
                area_id="1000",
                area_nombre="Gastos administrativos",
                score=52.0,
                nivel="BAJO",
                frecuencia=3,
                impacto=3,
                hallazgos_abiertos=0,
            ),
        ]

    critical_areas.sort(key=lambda x: x.score, reverse=True)
    quadrants = _build_matrix_cells(critical_areas)

    payload = RiskEngineResponse(cliente_id=cliente_id, quadrants=quadrants, areas_criticas=critical_areas[:8])
    return ApiResponse(data=payload.model_dump())
