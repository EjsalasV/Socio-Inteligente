from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CRITERIA_ROOT = ROOT / "data" / "criterio_experto"
AREA_DIR = CRITERIA_ROOT / "por_area"
SECTOR_DIR = CRITERIA_ROOT / "por_sector"
QUALITY_DIR = CRITERIA_ROOT / "revision_calidad"


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower()).strip("_")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _template_area(area_codigo: str) -> str:
    code = str(area_codigo or "").strip() or "AREA"
    return (
        f"# Criterio Experto - Area {code}\n\n"
        "## Alertas practicas\n"
        "- Completar criterio especifico para esta area.\n\n"
        "## Errores comunes\n"
        "- Pendiente de documentar.\n\n"
        "## Revision de calidad\n"
        "- Definir check de supervisión antes de emisión.\n"
    )


def _template_sector(sector: str) -> str:
    name = str(sector or "").strip() or "SECTOR"
    return (
        f"# Criterio Experto - Sector {name}\n\n"
        "## Riesgos recurrentes\n"
        "- Completar riesgos caracteristicos del sector.\n\n"
        "## Enfoque recomendado\n"
        "- Definir pruebas y alcance sugerido por experiencia.\n"
    )


def _find_area_file(area_codigo: str) -> Path | None:
    code = str(area_codigo or "").strip()
    if not code or not AREA_DIR.exists():
        return None
    candidates = sorted(AREA_DIR.glob("*.md"))
    exact_prefix = f"{code}_"
    for path in candidates:
        name = path.stem
        if name == code or name.startswith(exact_prefix):
            return path
    base = code.split(".")[0]
    for path in candidates:
        name = path.stem
        if name == base or name.startswith(f"{base}_"):
            return path
    return None


def _find_sector_file(sector: str) -> Path | None:
    key = _normalize_key(sector)
    if not key or not SECTOR_DIR.exists():
        return None
    for path in sorted(SECTOR_DIR.glob("*.md")):
        if _normalize_key(path.stem) == key:
            return path
    return None


def get_expert_criteria_by_area(area_codigo: str) -> dict[str, Any]:
    path = _find_area_file(area_codigo)
    if not path:
        return {
            "found": False,
            "scope": "area",
            "key": str(area_codigo or "").strip(),
            "source_path": "",
            "content": _template_area(area_codigo),
        }
    content = _read_text(path)
    if not content:
        content = _template_area(area_codigo)
    return {
        "found": bool(_read_text(path)),
        "scope": "area",
        "key": str(area_codigo or "").strip(),
        "source_path": str(path.relative_to(ROOT)),
        "content": content,
    }


def get_expert_criteria_by_sector(sector: str) -> dict[str, Any]:
    path = _find_sector_file(sector)
    if not path:
        return {
            "found": False,
            "scope": "sector",
            "key": str(sector or "").strip(),
            "source_path": "",
            "content": _template_sector(sector),
        }
    content = _read_text(path)
    if not content:
        content = _template_sector(sector)
    return {
        "found": bool(_read_text(path)),
        "scope": "sector",
        "key": str(sector or "").strip(),
        "source_path": str(path.relative_to(ROOT)),
        "content": content,
    }


def get_quality_review_criteria() -> dict[str, Any]:
    path = QUALITY_DIR / "general.md"
    content = _read_text(path)
    if not content:
        content = (
            "# Revision de Calidad - General\n\n"
            "- Pendiente de documentar criterios de supervision y control de calidad.\n"
        )
    return {
        "found": bool(_read_text(path)),
        "scope": "revision_calidad",
        "key": "general",
        "source_path": str(path.relative_to(ROOT)),
        "content": content,
    }


def update_expert_criteria(relative_path: str, content: str) -> dict[str, Any]:
    clean = str(relative_path or "").replace("\\", "/").strip("/")
    if not clean:
        raise ValueError("path_invalido")
    target = (CRITERIA_ROOT / clean).resolve()
    root_resolved = CRITERIA_ROOT.resolve()
    if not str(target).startswith(str(root_resolved)):
        raise ValueError("path_fuera_de_criterio_experto")
    if target.suffix.lower() not in {".md", ".yaml", ".yml"}:
        raise ValueError("extension_no_soportada")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(str(content or "").strip() + "\n", encoding="utf-8")
    return {
        "saved": True,
        "path": str(target.relative_to(ROOT)),
    }

