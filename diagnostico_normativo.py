from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
KNOWLEDGE_DIR = ROOT / "data" / "conocimiento_normativo"
TXT_REPORT = ROOT / "diagnostico_normativo_resultado.txt"
JSON_REPORT = ROOT / "diagnostico_normativo_resultado.json"

BROKEN_TOKENS = ("â€", "Ã", "ï»¿")


@dataclass(frozen=True)
class NormaEsperada:
    key: str
    titulo: str
    tipo: str
    filename: str
    subfolder: str


def _expected_nias() -> list[NormaEsperada]:
    pairs = [
        (200, "NIA 200 - Objetivos globales del auditor independiente"),
        (210, "NIA 210 - Acuerdo de los términos del encargo"),
        (220, "NIA 220 - Control de calidad del encargo"),
        (230, "NIA 230 - Documentación de auditoría"),
        (240, "NIA 240 - Responsabilidades del auditor en fraude"),
        (250, "NIA 250 - Consideración de leyes y reglamentos"),
        (260, "NIA 260 - Comunicación con los responsables del gobierno"),
        (265, "NIA 265 - Comunicación de deficiencias en control interno"),
        (300, "NIA 300 - Planificación de la auditoría"),
        (315, "NIA 315 - Identificación y valoración de riesgos"),
        (320, "NIA 320 - Importancia relativa o materialidad"),
        (330, "NIA 330 - Respuestas del auditor a los riesgos valorados"),
        (402, "NIA 402 - Consideraciones en entidades que usan servicios externos"),
        (450, "NIA 450 - Evaluación de incorrecciones identificadas"),
        (500, "NIA 500 - Evidencia de auditoría"),
        (501, "NIA 501 - Evidencia para partidas específicas"),
        (505, "NIA 505 - Confirmaciones externas"),
        (510, "NIA 510 - Encargos iniciales - saldos de apertura"),
        (520, "NIA 520 - Procedimientos analíticos"),
        (530, "NIA 530 - Muestreo de auditoría"),
        (540, "NIA 540 - Estimaciones contables"),
        (550, "NIA 550 - Partes relacionadas"),
        (560, "NIA 560 - Hechos posteriores al cierre"),
        (570, "NIA 570 - Empresa en funcionamiento (going concern)"),
        (580, "NIA 580 - Manifestaciones escritas"),
        (600, "NIA 600 - Auditorías de grupos"),
        (610, "NIA 610 - Uso del trabajo de auditores internos"),
        (620, "NIA 620 - Uso del trabajo de un experto"),
        (700, "NIA 700 - Formación de la opinión e informe"),
        (701, "NIA 701 - Cuestiones clave de auditoría"),
        (705, "NIA 705 - Opinión modificada"),
        (706, "NIA 706 - Párrafos de énfasis y otros"),
        (710, "NIA 710 - Información comparativa"),
        (720, "NIA 720 - Responsabilidades sobre otra información"),
    ]
    return [
        NormaEsperada(
            key=f"nia_{code}",
            titulo=title,
            tipo="nia",
            filename=f"nia_{code}.md",
            subfolder="nias",
        )
        for code, title in pairs
    ]


def _expected_niif_completas() -> list[NormaEsperada]:
    pairs = [
        ("niif", 1, "NIIF 1 - Adopción por primera vez"),
        ("niif", 2, "NIIF 2 - Pagos basados en acciones"),
        ("niif", 3, "NIIF 3 - Combinaciones de negocios"),
        ("niif", 5, "NIIF 5 - Activos no corrientes mantenidos para la venta"),
        ("niif", 7, "NIIF 7 - Instrumentos financieros revelaciones"),
        ("niif", 8, "NIIF 8 - Segmentos de operación"),
        ("niif", 9, "NIIF 9 - Instrumentos financieros"),
        ("niif", 10, "NIIF 10 - Estados financieros consolidados"),
        ("niif", 13, "NIIF 13 - Medición del valor razonable"),
        ("niif", 15, "NIIF 15 - Ingresos de contratos con clientes"),
        ("niif", 16, "NIIF 16 - Arrendamientos"),
        ("nic", 1, "NIC 1 - Presentación de estados financieros"),
        ("nic", 2, "NIC 2 - Inventarios"),
        ("nic", 7, "NIC 7 - Estado de flujos de efectivo"),
        ("nic", 8, "NIC 8 - Políticas contables, cambios en estimaciones"),
        ("nic", 10, "NIC 10 - Hechos ocurridos después del periodo"),
        ("nic", 12, "NIC 12 - Impuesto a las ganancias"),
        ("nic", 16, "NIC 16 - Propiedades, planta y equipo"),
        ("nic", 19, "NIC 19 - Beneficios a los empleados"),
        ("nic", 21, "NIC 21 - Efectos de las variaciones en tasas de cambio"),
        ("nic", 23, "NIC 23 - Costos por préstamos"),
        ("nic", 24, "NIC 24 - Información a revelar sobre partes relacionadas"),
        ("nic", 32, "NIC 32 - Instrumentos financieros presentación"),
        ("nic", 36, "NIC 36 - Deterioro del valor de los activos"),
        ("nic", 37, "NIC 37 - Provisiones, pasivos y activos contingentes"),
        ("nic", 38, "NIC 38 - Activos intangibles"),
        ("nic", 40, "NIC 40 - Propiedades de inversión"),
    ]
    out: list[NormaEsperada] = []
    for prefix, code, title in pairs:
        out.append(
            NormaEsperada(
                key=f"{prefix}_{code}",
                titulo=title,
                tipo="niif_completa",
                filename=f"{prefix}_{code}.md",
                subfolder="niif_completas",
            )
        )
    return out


def _expected_niif_pymes() -> list[NormaEsperada]:
    pairs = [
        (1, "Seccion 1 - Pequeñas y medianas entidades"),
        (2, "Seccion 2 - Conceptos y principios generales"),
        (3, "Seccion 3 - Presentación de estados financieros"),
        (4, "Seccion 4 - Estado de situación financiera"),
        (5, "Seccion 5 - Estado de resultado integral"),
        (6, "Seccion 6 - Estado de cambios en el patrimonio"),
        (7, "Seccion 7 - Estado de flujos de efectivo"),
        (8, "Seccion 8 - Notas a los estados financieros"),
        (10, "Seccion 10 - Políticas contables, estimaciones y errores"),
        (11, "Seccion 11 - Instrumentos financieros básicos"),
        (12, "Seccion 12 - Otros instrumentos financieros"),
        (13, "Seccion 13 - Inventarios"),
        (17, "Seccion 17 - Propiedades planta y equipo"),
        (18, "Seccion 18 - Activos intangibles"),
        (20, "Seccion 20 - Arrendamientos"),
        (21, "Seccion 21 - Provisiones y contingencias"),
        (22, "Seccion 22 - Pasivos y patrimonio"),
        (23, "Seccion 23 - Ingresos de actividades ordinarias"),
        (25, "Seccion 25 - Costos por préstamos"),
        (27, "Seccion 27 - Deterioro del valor de los activos"),
        (28, "Seccion 28 - Beneficios a los empleados"),
        (29, "Seccion 29 - Impuesto a las ganancias"),
        (32, "Seccion 32 - Hechos ocurridos después del periodo"),
        (33, "Seccion 33 - Información a revelar sobre partes relacionadas"),
        (35, "Seccion 35 - Transición a NIIF para PYMES"),
    ]
    return [
        NormaEsperada(
            key=f"niif_pymes_seccion_{code}",
            titulo=title,
            tipo="niif_pymes",
            filename=f"niif_pymes_seccion_{code}.md",
            subfolder="niif_pymes",
        )
        for code, title in pairs
    ]


def build_master() -> dict[str, list[NormaEsperada]]:
    return {
        "nias": _expected_nias(),
        "niif_completas": _expected_niif_completas(),
        "niif_pymes": _expected_niif_pymes(),
    }


def read_text_best_effort(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def has_frontmatter(text: str) -> bool:
    return text.startswith("---")


def has_broken_encoding(text: str) -> bool:
    return any(token in text for token in BROKEN_TOKENS)


def _extract_norma_key(path: Path, text: str) -> str | None:
    stem = path.stem.lower()

    m = re.search(r"\bnia[_\-\s]?(\d{3})\b", stem)
    if m:
        return f"nia_{int(m.group(1))}"

    m = re.search(r"\bniif[_\-\s]?(\d{1,2})\b", stem)
    if m:
        return f"niif_{int(m.group(1))}"

    m = re.search(r"\bnic[_\-\s]?(\d{1,2})\b", stem)
    if m:
        return f"nic_{int(m.group(1))}"

    m = re.search(r"(?:niif[_\-\s]?pymes[_\-\s]?)?seccion[_\-\s]?(\d{1,2})\b", stem)
    if m:
        return f"niif_pymes_seccion_{int(m.group(1))}"

    text_norm = text.lower()
    m = re.search(r"\bnia\s+(\d{3})\b", text_norm)
    if m:
        return f"nia_{int(m.group(1))}"

    m = re.search(r"\bniif\s+(\d{1,2})\b", text_norm)
    if m:
        return f"niif_{int(m.group(1))}"

    m = re.search(r"\bnic\s+(\d{1,2})\b", text_norm)
    if m:
        return f"nic_{int(m.group(1))}"

    m = re.search(r"\bsecci[oó]n\s+(\d{1,2})\b", text_norm)
    if m and "pymes" in text_norm:
        return f"niif_pymes_seccion_{int(m.group(1))}"

    return None


def _group_files(files: Iterable[Path]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for file in sorted(files):
        rel = file.relative_to(KNOWLEDGE_DIR)
        sub = rel.parts[0] if rel.parts else "."
        grouped.setdefault(sub, []).append(str(rel).replace("\\", "/"))
    return grouped


def main() -> None:
    if not KNOWLEDGE_DIR.exists():
        print(f"❌ No existe la ruta: {KNOWLEDGE_DIR}")
        return

    master = build_master()
    all_expected = {n.key: n for values in master.values() for n in values}

    md_files = sorted(
        p for p in KNOWLEDGE_DIR.rglob("*.md") if "_backup" not in str(p)
    )
    grouped = _group_files(md_files)

    present_keys: set[str] = set()
    broken_files: list[str] = []
    no_frontmatter_files: list[str] = []
    unmapped_files: list[str] = []

    for file in md_files:
        rel = str(file.relative_to(KNOWLEDGE_DIR)).replace("\\", "/")
        text = read_text_best_effort(file)
        if has_broken_encoding(text):
            broken_files.append(rel)
        if not has_frontmatter(text):
            no_frontmatter_files.append(rel)
        key = _extract_norma_key(file, text)
        if key and key in all_expected:
            present_keys.add(key)
        else:
            unmapped_files.append(rel)

    missing: dict[str, list[NormaEsperada]] = {}
    for category, expected in master.items():
        missing[category] = [item for item in expected if item.key not in present_keys]

    lines: list[str] = []
    lines.append("DIAGNOSTICO NORMATIVO - SOCIO AI")
    lines.append("=" * 72)
    lines.append(f"Ruta analizada: {KNOWLEDGE_DIR}")
    lines.append(f"Total archivos .md: {len(md_files)}")
    lines.append("")

    lines.append("ARCHIVOS ENCONTRADOS POR SUBCARPETA")
    lines.append("-" * 72)
    for sub, files in grouped.items():
        lines.append(f"[{sub}] ({len(files)} archivos)")
        for f in files:
            lines.append(f"  - {f}")
        lines.append("")

    lines.append("FALTANTES POR CATEGORIA")
    lines.append("-" * 72)
    for category in ("nias", "niif_completas", "niif_pymes"):
        items = missing[category]
        lines.append(f"{category.upper()} ({len(items)} faltantes)")
        for item in items:
            lines.append(f"  📋 {item.titulo} -> esperado: {item.subfolder}/{item.filename}")
        if not items:
            lines.append("  ✅ Sin faltantes")
        lines.append("")

    lines.append("ARCHIVOS CON POSIBLE ENCODING ROTO")
    lines.append("-" * 72)
    if broken_files:
        for f in broken_files:
            lines.append(f"  ⚠️ {f}")
    else:
        lines.append("  ✅ No se detectaron patrones rotos")
    lines.append("")

    lines.append("ARCHIVOS SIN FRONTMATTER YAML")
    lines.append("-" * 72)
    if no_frontmatter_files:
        for f in no_frontmatter_files:
            lines.append(f"  ⚠️ {f}")
    else:
        lines.append("  ✅ Todos tienen frontmatter")
    lines.append("")

    lines.append("ARCHIVOS NO MAPEADOS A LISTA MAESTRA")
    lines.append("-" * 72)
    if unmapped_files:
        for f in unmapped_files:
            lines.append(f"  ⚠️ {f}")
    else:
        lines.append("  ✅ Todos mapeados")
    lines.append("")

    n_nias = len(master["nias"]) - len(missing["nias"])
    n_niif = len(master["niif_completas"]) - len(missing["niif_completas"])
    n_pymes = len(master["niif_pymes"]) - len(missing["niif_pymes"])
    lines.append("RESUMEN DE COBERTURA")
    lines.append("-" * 72)
    lines.append(f"NIAs: {n_nias} de {len(master['nias'])}")
    lines.append(f"NIIF completas: {n_niif} de {len(master['niif_completas'])}")
    lines.append(f"NIIF PYMES: {n_pymes} de {len(master['niif_pymes'])}")
    lines.append("")

    TXT_REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    json_payload = {
        "knowledge_dir": str(KNOWLEDGE_DIR),
        "totals": {
            "files_md": len(md_files),
            "nias_presentes": n_nias,
            "nias_total": len(master["nias"]),
            "niif_completas_presentes": n_niif,
            "niif_completas_total": len(master["niif_completas"]),
            "niif_pymes_presentes": n_pymes,
            "niif_pymes_total": len(master["niif_pymes"]),
        },
        "missing": {
            category: [
                {
                    "key": item.key,
                    "titulo": item.titulo,
                    "tipo": item.tipo,
                    "filename": item.filename,
                    "subfolder": item.subfolder,
                }
                for item in items
            ]
            for category, items in missing.items()
        },
        "broken_encoding_files": broken_files,
        "no_frontmatter_files": no_frontmatter_files,
        "unmapped_files": unmapped_files,
        "grouped_files": grouped,
    }
    JSON_REPORT.write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )

    use_ascii = os.name == "nt"
    ok = "[OK]" if use_ascii else "✅"
    warn = "[WARN]" if use_ascii else "⚠️"
    note = "[NOTE]" if use_ascii else "📋"

    print(f"{ok} Diagnóstico generado: {TXT_REPORT}")
    print(f"{ok} Diagnóstico JSON generado: {JSON_REPORT}")
    print(f"{note} NIAs: {n_nias}/{len(master['nias'])}")
    print(f"{note} NIIF completas: {n_niif}/{len(master['niif_completas'])}")
    print(f"{note} NIIF PYMES: {n_pymes}/{len(master['niif_pymes'])}")
    print(f"{warn} Encoding roto detectado en {len(broken_files)} archivos")
    print(f"{warn} Sin frontmatter: {len(no_frontmatter_files)} archivos")


if __name__ == "__main__":
    main()
