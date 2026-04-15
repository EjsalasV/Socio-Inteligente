from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_ROOT = ROOT / "data" / "conocimiento_normativo"

_CACHE: dict[str, Any] = {
    "signature": "",
    "entries": [],
}

_FOLDER_CATEGORY_MAP = {
    "nias": "NIA",
    "niif_pymes": "NIIF_PYMES",
    "niif_completas": "NIIF",
    "nic": "NIC",
}


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_token(value: str) -> str:
    raw = unicodedata.normalize("NFD", str(value or "").strip().lower())
    return "".join(ch for ch in raw if unicodedata.category(ch) != "Mn")


def _catalog_signature() -> str:
    if not KNOWLEDGE_ROOT.exists():
        return "missing"
    parts: list[str] = []
    for path in sorted(KNOWLEDGE_ROOT.rglob("*.md")):
        try:
            stat = path.stat()
            parts.append(f"{path.as_posix()}:{int(stat.st_mtime_ns)}:{int(stat.st_size)}")
        except Exception:
            parts.append(f"{path.as_posix()}:missing")
    return "|".join(parts)


def _parse_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    text = str(markdown or "")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    raw_meta = parts[1]
    body = parts[2].lstrip()
    try:
        loaded = yaml.safe_load(raw_meta) or {}
        if isinstance(loaded, dict):
            return loaded, body
    except Exception:
        pass
    return {}, body


def _code_from_filename(path: Path) -> str:
    stem = path.stem.lower()
    nia = re.search(r"nia[_\- ]?(\d{3})", stem)
    if nia:
        return f"NIA-{nia.group(1)}"
    niif_pymes = re.search(r"seccion[_\- ]?(\d+)", stem)
    if niif_pymes and "niif_pymes" in stem:
        return f"NIIF-PYMES-{niif_pymes.group(1)}"
    if niif_pymes and stem.startswith("seccion_"):
        return f"NIIF-PYMES-{niif_pymes.group(1)}"
    nic = re.search(r"nic[_\- ]?(\d+)", stem)
    if nic:
        return f"NIC-{nic.group(1)}"
    niif = re.search(r"niif[_\- ]?(\d+)", stem)
    if niif:
        return f"NIIF-{niif.group(1)}"
    return path.stem.upper().replace("_", "-")


def _normalize_norm_code(raw_code: str, path: Path) -> str:
    code = _normalize_text(raw_code).upper()
    if not code:
        return _code_from_filename(path)

    nia = re.search(r"NIA[\s\-_]*(\d{3})", code)
    if nia:
        return f"NIA-{nia.group(1)}"

    niif_pymes = re.search(r"NIIF[\s\-_]*PYMES[\s\-_]*(SECCION[\s\-_]*)?(\d+)", code)
    if niif_pymes:
        return f"NIIF-PYMES-{niif_pymes.group(2)}"

    nic = re.search(r"NIC[\s\-_]*(\d+)", code)
    if nic:
        return f"NIC-{nic.group(1)}"

    niif = re.search(r"NIIF[\s\-_]*(\d+)", code)
    if niif:
        return f"NIIF-{niif.group(1)}"

    return code.replace("_", "-").replace(" ", "-")


def _categoria_from(code: str, path: Path) -> str:
    normalized = _normalize_text(code).upper()
    if normalized.startswith("NIA-"):
        return "NIA"
    if normalized.startswith("NIIF-PYMES-"):
        return "NIIF_PYMES"
    if normalized.startswith("NIC-"):
        return "NIC"
    if normalized.startswith("NIIF-"):
        return "NIIF"

    folder = path.parent.name.lower()
    return _FOLDER_CATEGORY_MAP.get(folder, "NIA")


def _fase_from_etapas(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "todo"
    etapas = {_normalize_token(str(item)) for item in value if str(item or "").strip()}
    if not etapas:
        return "todo"
    if etapas <= {"planificacion"}:
        return "planificacion"
    if etapas <= {"ejecucion"}:
        return "ejecucion"
    if etapas <= {"informe"} or etapas <= {"cierre"}:
        return "informe"
    return "todo"


def _first_heading(body: str) -> str:
    for line in str(body or "").splitlines():
        clean = line.strip()
        if clean.startswith("#"):
            return clean.lstrip("#").strip()
    return ""


def _extract_section_lines(body: str, section_hints: set[str]) -> list[str]:
    lines = str(body or "").splitlines()
    active = False
    out: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            if active and out:
                break
            continue
        if line.startswith("##"):
            header = _normalize_token(line.lstrip("#").strip())
            if any(hint in header for hint in section_hints):
                active = True
                continue
            if active:
                break
        if active:
            out.append(line)
    return out


def _extract_objective(body: str) -> str:
    objective_lines = _extract_section_lines(body, {"objetivo"})
    if objective_lines:
        text = " ".join(line.lstrip("-*0123456789. ").strip() for line in objective_lines)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            return text
    for raw in str(body or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(">"):
            continue
        return line
    return "Referencia normativa disponible para consulta por area y fase."


def _extract_requirements(body: str) -> list[str]:
    candidate_sections = [
        {"requisitos", "requerimientos"},
        {"procedimientos"},
        {"conceptos", "claves"},
    ]
    for hints in candidate_sections:
        lines = _extract_section_lines(body, hints)
        bullets = [
            line.lstrip("-*0123456789. ").strip()
            for line in lines
            if line.startswith(("-", "*")) or re.match(r"^\d+[.)]\s+", line)
        ]
        clean = [item for item in bullets if item]
        if clean:
            return clean[:5]

    fallback: list[str] = []
    for raw in str(body or "").splitlines():
        line = raw.strip()
        if line.startswith(("-", "*")) or re.match(r"^\d+[.)]\s+", line):
            item = line.lstrip("-*0123456789. ").strip()
            if item:
                fallback.append(item)
        if len(fallback) >= 5:
            break
    if fallback:
        return fallback
    return ["Revisar contenido completo de la norma y documentar evidencia aplicable al encargo."]


def _build_role_views(objetivo: str, categoria: str) -> dict[str, str]:
    marco = "NIA" if categoria == "NIA" else "NIIF/Marco contable"
    return {
        "junior": (
            f"Aplicacion practica: usa esta referencia para ejecutar pasos base y entender por que se pide la evidencia. ({marco})"
        ),
        "semi": (
            f"Conecta el objetivo con pruebas por aseveracion y valida desviaciones frente al criterio tecnico. ({marco})"
        ),
        "senior": (
            f"Usa esta norma para definir alcance, revisar calidad del soporte y cerrar brechas de ejecucion. ({marco})"
        ),
        "socio": (
            f"Impacto ejecutivo: {objetivo[:180]}{'...' if len(objetivo) > 180 else ''}"
        ),
    }


def _build_entry(path: Path, frontmatter: dict[str, Any], body: str) -> dict[str, Any]:
    raw_code = _normalize_text(frontmatter.get("norma"))
    codigo = _normalize_norm_code(raw_code, path)
    categoria = _categoria_from(codigo, path)

    titulo = _normalize_text(frontmatter.get("titulo"))
    if not titulo or "pendiente" in _normalize_token(titulo):
        heading = _first_heading(body)
        if heading:
            titulo = heading
    if not titulo:
        titulo = codigo

    objetivo = _extract_objective(body)
    requisitos = _extract_requirements(body)
    tags_meta = frontmatter.get("temas") if isinstance(frontmatter.get("temas"), list) else []
    tags = [str(item).strip() for item in tags_meta if str(item).strip()]
    if categoria not in tags:
        tags.append(categoria)

    return {
        "codigo": codigo,
        "titulo": titulo,
        "categoria": categoria,
        "cuando_aplica": _fase_from_etapas(frontmatter.get("etapas")),
        "objetivo": objetivo,
        "requisitos_clave": requisitos,
        "tags": tags,
        "vista": _build_role_views(objetivo, categoria),
        "source_path": str(path.relative_to(ROOT)).replace("\\", "/"),
    }


def _sort_key(entry: dict[str, Any]) -> tuple[int, int, str]:
    category_order = {"NIA": 0, "NIIF_PYMES": 1, "NIC": 2, "NIIF": 3}
    code = str(entry.get("codigo") or "")
    number_match = re.search(r"(\d+)$", code)
    number = int(number_match.group(1)) if number_match else 9999
    return (category_order.get(str(entry.get("categoria")), 9), number, code)


def list_normative_catalog() -> list[dict[str, Any]]:
    signature = _catalog_signature()
    if _CACHE.get("signature") == signature and isinstance(_CACHE.get("entries"), list):
        return _CACHE["entries"]

    entries_by_code: dict[str, dict[str, Any]] = {}
    if KNOWLEDGE_ROOT.exists():
        for path in sorted(KNOWLEDGE_ROOT.rglob("*.md")):
            try:
                raw = path.read_text(encoding="utf-8")
            except Exception:
                continue
            frontmatter, body = _parse_frontmatter(raw)
            entry = _build_entry(path, frontmatter, body)
            code = str(entry.get("codigo") or "").strip()
            if not code:
                continue
            # Prefer richer titles/objectives when duplicates exist.
            previous = entries_by_code.get(code)
            if previous is None:
                entries_by_code[code] = entry
                continue
            prev_title = _normalize_text(previous.get("titulo"))
            next_title = _normalize_text(entry.get("titulo"))
            if "pendiente" in _normalize_token(prev_title) and "pendiente" not in _normalize_token(next_title):
                entries_by_code[code] = entry

    entries = sorted(entries_by_code.values(), key=_sort_key)
    _CACHE["signature"] = signature
    _CACHE["entries"] = entries
    return entries

