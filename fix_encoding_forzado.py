from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET_FILES = [
    ROOT / "data" / "conocimiento_normativo" / "nias" / "nia_240.md",
    ROOT / "data" / "conocimiento_normativo" / "nias" / "nia_330.md",
    ROOT / "data" / "conocimiento_normativo" / "metodologia" / "aseveraciones.md",
    ROOT / "data" / "conocimiento_normativo" / "metodologia" / "hallazgos.md",
    ROOT / "data" / "conocimiento_normativo" / "metodologia" / "materialidad.md",
    ROOT / "data" / "conocimiento_normativo" / "metodologia" / "planificacion.md",
]


def _decode_best_effort(raw: bytes) -> tuple[str, str]:
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return raw.decode(enc), enc
        except Exception:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


def _clean_control_chars(text: str) -> str:
    # Mantener saltos de linea/tab y remover el resto de controles.
    return "".join(ch for ch in text if ch in ("\n", "\r", "\t") or ord(ch) >= 32)


def _repair_common_mojibake(text: str) -> str:
    repaired = text

    # Reemplazos directos frecuentes en este corpus.
    direct_map = {
        "Ã¡": "á",
        "Ã©": "é",
        "Ã­": "í",
        "Ã³": "ó",
        "Ãº": "ú",
        "Ã±": "ñ",
        "Ã": "Á",
        "Ã‰": "É",
        "Ã": "Í",
        "Ã“": "Ó",
        "Ãš": "Ú",
        "Ã‘": "Ñ",
        "â€“": "–",
        "â€”": "—",
        "â€œ": "\"",
        "â€": "\"",
        "â€˜": "'",
        "â€™": "'",
        "Â¿": "¿",
        "Â¡": "¡",
        "\ufeff": "",
    }
    for bad, good in direct_map.items():
        repaired = repaired.replace(bad, good)

    # Patrón observado: "Afirmaci3n", "Planificaci3n", etc.
    repaired = re.sub(r"(?i)([A-Za-zÁÉÍÓÚáéíóúÑñ])3([A-Za-zÁÉÍÓÚáéíóúÑñ])", r"\1ó\2", repaired)

    # Interrogativos frecuentes dañados en metodología.
    word_map = {
        "Que ": "Qué ",
        "Cual ": "Cuál ",
        "Por que ": "Por qué ",
        "Quien ": "Quién ",
        "Como ": "Cómo ",
        "Donde ": "Dónde ",
        "Cuanto ": "Cuánto ",
        "Titulo": "Título",
        "Ttulo": "Título",
        "Metodologica": "Metodológica",
        "Ejecucion": "Ejecución",
        "Planificacion": "Planificación",
        "Informacion": "Información",
        "Direccion": "Dirección",
        "Documentacion": "Documentación",
        "Revision": "Revisión",
    }
    for bad, good in word_map.items():
        repaired = repaired.replace(bad, good)

    # Signos de apertura en preguntas.
    repaired = re.sub(r"(?m)^([A-ZÁÉÍÓÚÑ][^?\n]{1,80}\?)", lambda m: ("¿" + m.group(1)) if not m.group(1).startswith("¿") else m.group(1), repaired)

    return repaired


def main() -> None:
    print("=== FIX ENCODING FORZADO ===")
    fixed = 0
    missing = 0
    for file_path in TARGET_FILES:
        if not file_path.exists():
            print(f"[WARN] No existe: {file_path}")
            missing += 1
            continue

        raw = file_path.read_bytes()
        decoded, used_enc = _decode_best_effort(raw)
        cleaned = _clean_control_chars(decoded)
        repaired = _repair_common_mojibake(cleaned)

        # Escritura forzada siempre, sin BOM.
        file_path.write_text(repaired, encoding="utf-8", newline="\n")
        fixed += 1
        print(f"[OK] Reescrito forzado: {file_path} (decode={used_enc})")

    print("\n=== RESUMEN ===")
    print(f"[OK] Reescritos: {fixed}")
    print(f"[WARN] Faltantes: {missing}")
    print("[NOTE] Todos guardados como UTF-8 sin BOM.")


if __name__ == "__main__":
    main()

