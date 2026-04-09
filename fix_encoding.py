from __future__ import annotations

import shutil
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KNOWLEDGE_DIR = ROOT / "data" / "conocimiento_normativo"
BROKEN_TOKENS = ("â€", "Ã", "ï»¿")


@dataclass
class RepairResult:
    file: str
    status: str
    detail: str


def _is_broken(text: str) -> bool:
    return any(token in text for token in BROKEN_TOKENS)


def _score_badness(text: str) -> int:
    score = 0
    for token in BROKEN_TOKENS:
        score += text.count(token) * 10
    score += text.count("\ufffd") * 5
    return score


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


def _try_latin1(raw: bytes) -> str:
    # Método A (pedido): leer latin-1.
    return raw.decode("latin-1")


def _try_cp1252(raw: bytes) -> str:
    # Método B (pedido): leer cp1252.
    return raw.decode("cp1252")


def _try_ftfy(text: str) -> str:
    # Método C (pedido): usar ftfy si está disponible.
    try:
        from ftfy import fix_text  # type: ignore

        return fix_text(text)
    except Exception:
        return text


def _try_transcode(text: str, src: str) -> str:
    try:
        return text.encode(src, errors="ignore").decode("utf-8", errors="ignore")
    except Exception:
        return text


def _best_candidate(raw: bytes, original_text: str) -> tuple[str, str]:
    base_score = _score_badness(original_text)
    best_text = original_text
    best_score = base_score
    best_method = "sin_cambios"

    candidates = []
    try:
        candidates.append(("latin-1", _try_latin1(raw)))
    except Exception:
        pass
    try:
        candidates.append(("cp1252", _try_cp1252(raw)))
    except Exception:
        pass
    # Reparacion tipica de mojibake UTF-8 interpretado como Latin-1/CP1252.
    candidates.append(("transcode-latin1", _try_transcode(original_text, "latin-1")))
    candidates.append(("transcode-cp1252", _try_transcode(original_text, "cp1252")))

    for method, candidate in candidates:
        cand_score = _score_badness(candidate)
        if cand_score < best_score:
            best_text = candidate
            best_score = cand_score
            best_method = method

    # Segunda pasada de transcode sobre el mejor candidato para casos "doble mojibake".
    trans2 = _try_transcode(best_text, "latin-1")
    trans2_score = _score_badness(trans2)
    if trans2_score < best_score:
        best_text = trans2
        best_score = trans2_score
        best_method = f"{best_method}+transcode2"

    ftfy_candidate = _try_ftfy(best_text)
    ftfy_score = _score_badness(ftfy_candidate)
    if ftfy_score < best_score:
        best_text = ftfy_candidate
        best_score = ftfy_score
        if best_method == "sin_cambios":
            best_method = "ftfy"
        else:
            best_method = f"{best_method}+ftfy"

    return best_text, best_method


def main() -> None:
    if not KNOWLEDGE_DIR.exists():
        print(f"❌ No existe la ruta: {KNOWLEDGE_DIR}")
        return

    results: list[RepairResult] = []
    md_files = sorted(KNOWLEDGE_DIR.rglob("*.md"))

    use_ascii = os.name == "nt"
    ok_badge = "[OK]" if use_ascii else "✅"
    warn_badge = "[WARN]" if use_ascii else "⚠️"
    err_badge = "[ERR]" if use_ascii else "❌"
    note_badge = "[NOTE]" if use_ascii else "📋"

    for path in md_files:
        if "_backup" in str(path):
            continue
        rel = str(path.relative_to(KNOWLEDGE_DIR)).replace("\\", "/")
        raw = path.read_bytes()
        original_text = raw.decode("utf-8", errors="replace")

        if not _is_broken(original_text):
            results.append(RepairResult(rel, "skip", "sin patron roto"))
            continue

        candidate_text, method = _best_candidate(raw, original_text)
        if _score_badness(candidate_text) >= _score_badness(original_text):
            results.append(
                RepairResult(
                    rel,
                    "warn",
                    "sin mejora detectable",
                )
            )
            print(f"{warn_badge} {rel} -> no mejoró con métodos, se dejó intacto")
            continue

        try:
            backup = _backup_file(path)
        except Exception as exc:
            results.append(RepairResult(rel, "error", f"backup falló: {exc}"))
            print(f"{err_badge} {rel} -> no se pudo crear backup")
            continue

        try:
            path.write_text(candidate_text, encoding="utf-8", newline="\n")
            results.append(
                RepairResult(
                    rel,
                    "ok",
                    f"reparado con {method} (backup: {backup.name})",
                )
            )
            print(f"{ok_badge} {rel} -> reparado con {method}")
        except Exception as exc:
            results.append(RepairResult(rel, "error", f"fallo al escribir: {exc}"))
            print(f"{err_badge} {rel} -> error al guardar")

    ok = sum(1 for r in results if r.status == "ok")
    warn = sum(1 for r in results if r.status == "warn")
    err = sum(1 for r in results if r.status == "error")
    skip = sum(1 for r in results if r.status == "skip")

    print("\n=== RESUMEN FIX ENCODING ===")
    print(f"{ok_badge} Reparados: {ok}")
    print(f"{warn_badge} Advertencias: {warn}")
    print(f"{err_badge} Errores: {err}")
    print(f"{note_badge} Sin cambios necesarios: {skip}")


if __name__ == "__main__":
    main()
