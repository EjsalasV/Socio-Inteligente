from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.normative_quality_service import apply_quality_gate  # noqa: E402


DEFAULT_MANIFEST = ROOT / "data" / "conocimiento_normativo" / "manifest_piloto_ingresos_cxc.yaml"
DEFAULT_REPORT = ROOT / "docs" / "CORPUS_PILOTO_DIAGNOSTICO.md"
SUSPICIOUS_ENCODING_MARKERS = ("�", "Ã", "Â", "Secci3n", "auditor?a", "relaci?n", "informaci?n")


def _parse_frontmatter(markdown: str) -> dict[str, Any]:
    text = markdown.lstrip("\ufeff").strip()
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        metadata = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}
    return metadata if isinstance(metadata, dict) else {}


def _encoding_markers(text: str) -> list[str]:
    return [marker for marker in SUSPICIOUS_ENCODING_MARKERS if marker in text]


def _inspect_source(item: dict[str, Any]) -> dict[str, Any]:
    raw_path = str(item.get("path") or "").strip()
    result = {
        "id": str(item.get("id") or ""),
        "priority": int(item.get("priority") or 999),
        "purpose": str(item.get("purpose") or ""),
        "path": raw_path,
        "manifest_status": str(item.get("review_status") or "pending"),
        "exists": False,
        "citation_eligible": False,
        "quality_issues": [],
        "encoding_markers": [],
    }
    if not raw_path:
        result["quality_issues"] = ["fuente_oficial_por_identificar"]
        return result

    source_path = ROOT / raw_path
    if not source_path.exists():
        result["quality_issues"] = ["archivo_no_encontrado"]
        return result

    text = source_path.read_text(encoding="utf-8")
    metadata = _parse_frontmatter(text)
    quality = apply_quality_gate(metadata, raw_path)
    result.update(
        {
            "exists": True,
            "citation_eligible": bool(quality.get("citation_eligible")),
            "quality_issues": [str(issue) for issue in quality.get("quality_issues", [])],
            "encoding_markers": _encoding_markers(text),
            "declared_version": str(quality.get("version") or ""),
            "declared_effective_from": str(quality.get("vigente_desde") or ""),
            "declared_review_state": str(quality.get("estado_revision") or ""),
            "declared_content_type": str(quality.get("tipo_contenido") or ""),
        }
    )
    if metadata.get("contenido_completo") is True:
        result["quality_issues"].append("contenido_completo_requiere_comprobacion")
    return result


def audit_manifest(manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(manifest, dict) or not isinstance(manifest.get("sources"), list):
        raise ValueError("El manifiesto debe contener una lista 'sources'.")
    rows = [_inspect_source(item) for item in manifest["sources"] if isinstance(item, dict)]
    return manifest, sorted(rows, key=lambda row: row["priority"])


def render_report(manifest: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    existing = sum(1 for row in rows if row["exists"])
    eligible = sum(1 for row in rows if row["citation_eligible"])
    encoding_issues = sum(1 for row in rows if row["encoding_markers"])
    lines = [
        "# Diagnostico del corpus piloto",
        "",
        f"**Corte del manifiesto:** {manifest.get('updated_at', 'N/D')}",
        f"**Piloto:** {manifest.get('pilot', 'N/D')}",
        "**Estado:** DIAGNOSTICO AUTOMATICO; NO EQUIVALE A REVISION PROFESIONAL",
        "",
        "## Resumen",
        "",
        f"- Entradas requeridas: {len(rows)}",
        f"- Archivos encontrados: {existing}",
        f"- Fuentes habilitadas para citar: {eligible}",
        f"- Archivos con indicadores de codificacion: {encoding_issues}",
        f"- Fuentes por identificar: {sum(1 for row in rows if not row['path'])}",
        "",
        "## Inventario priorizado",
        "",
        "| Prioridad | Fuente | Archivo | Estado | Cita | Brechas detectadas |",
        "|---:|---|---|---|---|---|",
    ]
    for row in rows:
        issues = list(row["quality_issues"])
        if row["encoding_markers"]:
            issues.append("codificacion_sospechosa:" + ",".join(row["encoding_markers"]))
        lines.append(
            "| {priority} | {id} | {path} | {status} | {citation} | {issues} |".format(
                priority=row["priority"],
                id=row["id"],
                path=f"`{row['path']}`" if row["path"] else "Por identificar",
                status=row["manifest_status"],
                citation="Si" if row["citation_eligible"] else "No",
                issues="; ".join(issues) if issues else "Sin brechas automaticas",
            )
        )
    lines.extend(
        [
            "",
            "## Orden de trabajo",
            "",
            "1. NIA 240: obtener acceso autorizado al texto oficial y cotejar localizadores por parrafo.",
            "2. Solicitar permisos a IFAC y licencia de producto a IFRS Foundation; hasta entonces excluir texto oficial e indexar solo metadatos e interpretacion profesional propia.",
            "3. Obtener y cotejar el texto consolidado del Reglamento sobre Auditoria Externa y las reformas posteriores al instructivo NIIF de 2019.",
            "4. Obtener revision profesional local documentada de la matriz ecuatoriana de versiones y sus reglas de adopcion anticipada.",
            "5. Confirmar el regulador de cada entidad y crear matrices separadas solo cuando el piloto necesite cubrir regimenes especiales.",
            "6. Cotejar localizadores internacionales contra copias autorizadas y documentar la aprobacion humana por fuente y version.",
            "",
            "## Regla de aprobacion",
            "",
            "Una fuente solo cambia a `verified` mediante revision humana documentada. Que el archivo exista o no presente brechas automaticas no demuestra autoridad, vigencia, integridad, licencia ni aplicabilidad.",
            "",
            "## Reproducir",
            "",
            "```powershell",
            "python scripts/audit_pilot_normative_corpus.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita el manifiesto normativo del piloto.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--strict", action="store_true", help="Falla si alguna fuente no esta habilitada para citar.")
    args = parser.parse_args()

    manifest, rows = audit_manifest(args.manifest)
    report = render_report(manifest, rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")
    print(report)
    return 1 if args.strict and any(not row["citation_eligible"] for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
