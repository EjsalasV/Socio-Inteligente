from __future__ import annotations

import json
import re
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KNOWLEDGE_DIR = ROOT / "data" / "conocimiento_normativo"
DIAG_JSON = ROOT / "diagnostico_normativo_resultado.json"


def _safe_title_for_h1(title: str) -> str:
    # "NIA 240 - xxx" -> "NIA 240 - xxx"
    return re.sub(r"\s+", " ", title).strip()


def _frontmatter_nia(norma: str, titulo: str) -> str:
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
        "contenido_completo: false\n"
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


def _frontmatter_niif_completa(norma: str, titulo: str) -> str:
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
        "contenido_completo: false\n"
        "areas_aplicables: []\n"
        "afirmaciones_relacionadas: []\n"
        "marco: niif_completas\n"
        "temas: []\n"
        "referencias_cruzadas: []\n"
        "---\n\n"
    )


def _frontmatter_niif_pymes(norma: str, titulo: str, seccion: str) -> str:
    return (
        "---\n"
        f"norma: {norma}\n"
        f"titulo: {titulo}\n"
        "tipo: NIIF_PYMES\n"
        f"seccion: {seccion}\n"
        "version: 2015\n"
        "vigente_desde: 2017-01-01\n"
        "vigente_hasta: null\n"
        "activo: true\n"
        "ultima_actualizacion: 2024-01-01\n"
        "contenido_completo: false\n"
        "areas_aplicables: []\n"
        "afirmaciones_relacionadas: []\n"
        "marco: niif_pymes\n"
        "temas: []\n"
        "referencias_cruzadas: []\n"
        "---\n\n"
    )


def _template_body(nombre_norma: str) -> str:
    return (
        f"# {nombre_norma} — PENDIENTE DE COMPLETAR\n\n"
        "> ⚠️ Este archivo es una plantilla. Debe completarse con el contenido oficial.\n\n"
        "## Objetivo\n"
        "[Pendiente]\n\n"
        "## Requerimientos Principales\n"
        "[Pendiente]\n\n"
        "## Procedimientos Relacionados\n"
        "[Pendiente]\n\n"
        "## Alertas para Auditoría Ecuador\n"
        "[Pendiente]\n\n"
        "## Referencias Cruzadas\n"
        "[Pendiente]\n"
    )


def _norma_name_from_title(title: str) -> str:
    # Usa la parte antes del primer " - " para dejar encabezado limpio.
    if " - " in title:
        return title.split(" - ", 1)[0].strip()
    return title.strip()


def main() -> None:
    if not DIAG_JSON.exists():
        print(f"❌ No existe {DIAG_JSON}. Ejecuta primero diagnostico_normativo.py")
        return

    payload = json.loads(DIAG_JSON.read_text(encoding="utf-8"))
    missing = payload.get("missing", {})
    created = 0
    skipped = 0
    errors = 0

    use_ascii = os.name == "nt"
    ok_badge = "[OK]" if use_ascii else "✅"
    warn_badge = "[WARN]" if use_ascii else "⚠️"
    err_badge = "[ERR]" if use_ascii else "❌"

    for category in ("nias", "niif_completas", "niif_pymes"):
        items = missing.get(category, [])
        if not isinstance(items, list):
            continue
        for item in items:
            try:
                subfolder = str(item.get("subfolder") or "")
                filename = str(item.get("filename") or "")
                titulo = str(item.get("titulo") or "").strip()
                key = str(item.get("key") or "").strip().lower()
                if not subfolder or not filename:
                    errors += 1
                    print(f"{err_badge} Item faltante inválido: {item}")
                    continue

                if category == "nias":
                    m = re.search(r"nia_(\d{3})", key)
                    code = m.group(1) if m else "XXX"
                    norma = f"NIA {code}"
                    front = _frontmatter_nia(norma, titulo)
                elif category == "niif_completas":
                    m = re.search(r"(niif|nic)_(\d{1,2})", key)
                    prefix = m.group(1).upper() if m else "NIIF"
                    code = m.group(2) if m else "X"
                    norma = f"{prefix} {code}"
                    front = _frontmatter_niif_completa(norma, titulo)
                else:
                    m = re.search(r"niif_pymes_seccion_(\d{1,2})", key)
                    sec = m.group(1) if m else "XX"
                    norma = f"NIIF_PYMES_SECCION_{sec}"
                    front = _frontmatter_niif_pymes(norma, titulo, sec)

                dest_dir = KNOWLEDGE_DIR / subfolder
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / filename
                if dest.exists():
                    skipped += 1
                    print(f"{warn_badge} {dest.relative_to(KNOWLEDGE_DIR)} ya existe, se omite")
                    continue

                body = _template_body(_norma_name_from_title(titulo))
                dest.write_text(front + body, encoding="utf-8", newline="\n")
                created += 1
                print(f"{ok_badge} Plantilla creada: {dest.relative_to(KNOWLEDGE_DIR)}")
            except Exception as exc:
                errors += 1
                print(f"{err_badge} Error creando plantilla ({item}): {exc}")

    print("\n=== RESUMEN PLANTILLAS ===")
    print(f"{ok_badge} Creadas: {created}")
    print(f"{warn_badge} Omitidas (ya existían): {skipped}")
    print(f"{err_badge} Errores: {errors}")


if __name__ == "__main__":
    main()
