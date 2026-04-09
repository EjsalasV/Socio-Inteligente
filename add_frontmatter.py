from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
KNOWLEDGE_DIR = ROOT / "data" / "conocimiento_normativo"


DEFAULT_ETAPAS = ["planificacion", "ejecucion", "cierre"]


def _backup_file(path: Path) -> Path:
    backup_dir = path.parent / "_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / path.name
    if not backup.exists():
        shutil.copy2(path, backup)
        return backup

    i = 1
    while True:
        alt = backup_dir / f"{path.stem}_{i}{path.suffix}"
        if not alt.exists():
            shutil.copy2(path, alt)
            return alt
        i += 1


def _has_frontmatter(text: str) -> bool:
    return text.startswith("---")


def _split_frontmatter(text: str) -> tuple[str, str] | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    frontmatter_block = parts[1]
    body = parts[2].lstrip("\n")
    return frontmatter_block, body


def _extract_h1(text: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith("# "):
            title = line.strip()[2:].strip()
            if title:
                return title
    return "Titulo pendiente de normalizar"


def _detect_norma(path: Path, text: str) -> tuple[str, str, str]:
    """Retorna (tipo, norma, seccion)."""
    stem = path.stem.lower()
    content = text.lower()

    m = re.search(r"\bnia[_\-\s]?(\d{3})\b", stem)
    if not m:
        m = re.search(r"\bnia\s+(\d{3})\b", content)
    if m:
        code = str(int(m.group(1)))
        return "nia", f"NIA {code}", ""

    m = re.search(r"\bniif[_\-\s]?(\d{1,2})\b", stem)
    if not m:
        m = re.search(r"\bniif\s+(\d{1,2})\b", content)
    if m:
        code = str(int(m.group(1)))
        return "niif_completa", f"NIIF {code}", ""

    m = re.search(r"\bnic[_\-\s]?(\d{1,2})\b", stem)
    if not m:
        m = re.search(r"\bnic\s+(\d{1,2})\b", content)
    if m:
        code = str(int(m.group(1)))
        return "niif_completa", f"NIC {code}", ""

    m = re.search(r"(?:niif[_\-\s]?pymes[_\-\s]?)?seccion[_\-\s]?(\d{1,2})\b", stem)
    if not m:
        m = re.search(r"\bsecci[oó]n\s+(\d{1,2})\b", content)
    if m:
        sec = str(int(m.group(1)))
        return "niif_pymes", f"NIIF_PYMES_SECCION_{sec}", sec

    folder = path.parent.name.lower()
    if folder == "nias":
        return "nia", "NIA XXX", ""
    if folder == "niif_completas":
        return "niif_completa", "NIIF X", ""
    if folder == "niif_pymes":
        return "niif_pymes", "NIIF_PYMES_SECCION_XX", "XX"
    return "desconocido", "NORMA_DESCONOCIDA", ""


def _build_frontmatter(tipo: str, norma: str, titulo: str, seccion: str) -> str:
    if tipo == "nia":
        return (
            "---\n"
            f"norma: {norma}\n"
            f"titulo: {titulo}\n"
            "tipo: NIA\n"
            "version: vigente\n"
            "vigente_desde: 2009-01-01\n"
            "vigente_hasta: null\n"
            "activo: true\n"
            "ultima_actualizacion: 2024-01-01\n"
            "areas_aplicables:\n"
            "  - todas\n"
            "afirmaciones_relacionadas: []\n"
            "etapas:\n"
            "  - planificacion\n"
            "  - ejecucion\n"
            "  - cierre\n"
            "temas: []\n"
            "marco: ambos\n"
            "severidad_minima: medio\n"
            "referencias_cruzadas: []\n"
            "---\n\n"
        )
    if tipo == "niif_completa":
        return (
            "---\n"
            f"norma: {norma}\n"
            f"titulo: {titulo}\n"
            "tipo: NIIF_COMPLETA\n"
            "version: vigente\n"
            "vigente_desde: 2023-01-01\n"
            "vigente_hasta: null\n"
            "activo: true\n"
            "ultima_actualizacion: 2024-01-01\n"
            "areas_aplicables: []\n"
            "afirmaciones_relacionadas: []\n"
            "etapas:\n"
            "  - planificacion\n"
            "  - ejecucion\n"
            "  - cierre\n"
            "marco: niif_completas\n"
            "temas: []\n"
            "referencias_cruzadas: []\n"
            "---\n\n"
        )
    if tipo == "niif_pymes":
        sec = seccion or "XX"
        return (
            "---\n"
            f"norma: NIIF_PYMES_SECCION_{sec}\n"
            f"titulo: {titulo}\n"
            "tipo: NIIF_PYMES\n"
            f"seccion: {sec}\n"
            "version: 2015\n"
            "vigente_desde: 2017-01-01\n"
            "vigente_hasta: null\n"
            "activo: true\n"
            "ultima_actualizacion: 2024-01-01\n"
            "areas_aplicables: []\n"
            "afirmaciones_relacionadas: []\n"
            "etapas:\n"
            "  - planificacion\n"
            "  - ejecucion\n"
            "  - cierre\n"
            "marco: niif_pymes\n"
            "temas: []\n"
            "referencias_cruzadas: []\n"
            "---\n\n"
        )
    return (
        "---\n"
        f"norma: {norma}\n"
        f"titulo: {titulo}\n"
        "tipo: DESCONOCIDO\n"
        "version: vigente\n"
        "activo: true\n"
        "ultima_actualizacion: 2024-01-01\n"
        "referencias_cruzadas: []\n"
        "---\n\n"
    )


def _fill_etapas_if_empty(text: str) -> tuple[bool, str]:
    split = _split_frontmatter(text)
    if split is None:
        return False, text

    frontmatter_block, body = split
    try:
        loaded = yaml.safe_load(frontmatter_block) or {}
    except Exception:
        return False, text
    if not isinstance(loaded, dict):
        return False, text

    tipo = str(loaded.get("tipo") or "").strip().upper()
    if tipo not in {"NIIF_COMPLETA", "NIIF_PYMES"}:
        return False, text

    etapas = loaded.get("etapas")
    needs_update = etapas is None or (isinstance(etapas, list) and len(etapas) == 0)
    if not needs_update:
        return False, text

    loaded["etapas"] = list(DEFAULT_ETAPAS)
    dumped = yaml.safe_dump(loaded, allow_unicode=True, sort_keys=False).strip()
    rebuilt = f"---\n{dumped}\n---\n\n{body.lstrip()}"
    return True, rebuilt


def main() -> None:
    if not KNOWLEDGE_DIR.exists():
        print(f"[ERR] No existe la ruta: {KNOWLEDGE_DIR}")
        return

    updated = 0
    updated_etapas = 0
    skipped = 0
    errors = 0

    use_ascii = os.name == "nt"
    ok_badge = "[OK]" if use_ascii else "✅"
    warn_badge = "[WARN]" if use_ascii else "⚠️"
    err_badge = "[ERR]" if use_ascii else "❌"

    for path in sorted(KNOWLEDGE_DIR.rglob("*.md")):
        if "_backup" in str(path):
            continue
        rel = str(path.relative_to(KNOWLEDGE_DIR)).replace("\\", "/")
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            if _has_frontmatter(text):
                changed, new_text = _fill_etapas_if_empty(text)
                if changed:
                    backup = _backup_file(path)
                    path.write_text(new_text, encoding="utf-8", newline="\n")
                    updated_etapas += 1
                    print(f"{ok_badge} {rel} -> etapas completadas (backup: {backup.name})")
                else:
                    skipped += 1
                continue

            tipo, norma, seccion = _detect_norma(path, text)
            titulo = _extract_h1(text)
            frontmatter = _build_frontmatter(tipo, norma, titulo, seccion)

            backup = _backup_file(path)
            path.write_text(frontmatter + text.lstrip("\ufeff"), encoding="utf-8", newline="\n")
            updated += 1
            print(f"{ok_badge} {rel} -> frontmatter agregado (backup: {backup.name})")
        except Exception as exc:
            errors += 1
            print(f"{err_badge} {rel} -> error: {exc}")

    print("\n=== RESUMEN FRONTMATTER ===")
    print(f"{ok_badge} Actualizados (sin frontmatter): {updated}")
    print(f"{ok_badge} Etapas completadas (frontmatter existente): {updated_etapas}")
    print(f"{warn_badge} Omitidos: {skipped}")
    print(f"{err_badge} Errores: {errors}")


if __name__ == "__main__":
    main()
