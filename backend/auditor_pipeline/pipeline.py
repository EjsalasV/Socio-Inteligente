from __future__ import annotations

from typing import Any

from backend.services.normative_quality_service import validate_normative_output
from backend.services.rag_chat_service import build_citations_used_in_answer, retrieve_context_chunks

from .llm_client import call_llm
from .post_check import run_post_check
from .prompt_builder import (
    build_user_prompt,
    format_client_context,
    format_rag_chunks,
    load_context,
    load_system_prompt,
)


def _normalize_chunks(chunks_rag: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not isinstance(chunks_rag, list):
        return []
    out: list[dict[str, Any]] = []
    for chunk in chunks_rag:
        if not isinstance(chunk, dict):
            continue
        out.append(
            {
                "source": str(chunk.get("source") or chunk.get("referencia") or ""),
                "excerpt": str(chunk.get("excerpt") or chunk.get("texto") or ""),
                "score": chunk.get("score", 0),
                "metadata": chunk.get("metadata") if isinstance(chunk.get("metadata"), dict) else {},
            }
        )
    return out


def _choose_confidence(post_checked: dict[str, Any], chunks_count: int) -> float:
    flags = post_checked.get("flags") if isinstance(post_checked.get("flags"), list) else []
    if flags:
        return 0.48 if chunks_count else 0.32
    return 0.82 if chunks_count else 0.64


def _has_blocking_normative_flag(flags: list[str]) -> bool:
    blocking_prefixes = (
        "CITA_NO_VERIFICADA",
        "CITA_INVENTADA_SIN_CHUNK",
        "CITA_SIN_IDENTIFICADOR",
    )
    return any(str(flag).startswith(blocking_prefixes) for flag in flags)


def execute_pipeline(
    *,
    cliente_id: str,
    codigo_area: str,
    modo: str,
    senales_python: dict[str, Any] | None = None,
    chunks_rag: list[dict[str, Any]] | None = None,
    consulta_adicional: str = "",
) -> dict[str, Any]:
    signals_python = senales_python or {}
    perfil, area = load_context(cliente_id, codigo_area)

    normalized_chunks = _normalize_chunks(chunks_rag)
    if not normalized_chunks:
        query_for_rag = consulta_adicional.strip() or f"{modo} area {codigo_area}"
        normalized_chunks = _normalize_chunks(
            retrieve_context_chunks(cliente_id, query_for_rag, top_k=6)
        )

    contexto_cliente = format_client_context(perfil, area, signals_python, cliente_id)
    rag_block = format_rag_chunks(normalized_chunks)
    user_prompt = build_user_prompt(
        modo=modo,
        contexto_cliente=contexto_cliente,
        chunks_rag=rag_block,
        consulta_adicional=consulta_adicional,
    )
    raw_text, llm_meta = call_llm(
        prompt_usuario=user_prompt,
        modo=modo,
        system_prompt=load_system_prompt(),
    )

    post_checked = run_post_check(
        texto_llm=raw_text,
        perfil_yaml=perfil,
        area_yaml=area,
        chunks_rag=normalized_chunks,
    )
    parsed = post_checked.get("respuesta") if isinstance(post_checked.get("respuesta"), dict) else {}
    analisis = str(parsed.get("analisis") or "").strip()
    procedimientos = parsed.get("procedimientos")
    proc_lines: list[str] = []
    if isinstance(procedimientos, list):
        for step in procedimientos[:5]:
            text = str(step).strip()
            if text:
                proc_lines.append(f"- {text}")
    if not analisis:
        analisis = str(raw_text or "").strip()
    if proc_lines:
        answer = f"{analisis}\n\nProcedimientos sugeridos:\n" + "\n".join(proc_lines)
    else:
        answer = analisis

    flags = post_checked.get("flags") if isinstance(post_checked.get("flags"), list) else []
    output_validation = validate_normative_output(
        answer,
        [chunk.get("metadata") for chunk in normalized_chunks[:6]],
    )
    flags.extend(output_validation.issues)
    output_blocked = not output_validation.allowed or _has_blocking_normative_flag(flags)
    if output_blocked:
        answer = (
            "Respuesta normativa bloqueada. El pipeline genero una atribucion o cita que no esta "
            "respaldada por una fuente verificada e identificada. El contenido inseguro no se mostrara; "
            "puedes continuar como orientacion sin cita o validar primero la fuente oficial."
        )
        citations: list[dict[str, str]] = []
    else:
        citations = build_citations_used_in_answer(answer, normalized_chunks)

    confidence = _choose_confidence(post_checked, len(normalized_chunks))

    return {
        "answer": answer.strip(),
        "context_sources": [str(c.get("source") or "") for c in normalized_chunks if str(c.get("source") or "").strip()],
        "citations": citations,
        "confidence": confidence,
        "prompt_meta": {"prompt_id": "auditor_pipeline_json", "prompt_version": "v1.1"},
        "mode_used": f"{modo}_output_blocked" if output_blocked else f"{modo}_pipeline",
        "provider": str(llm_meta.get("provider") or ""),
        "model": str(llm_meta.get("model") or ""),
        "pipeline": {
            "mode": modo,
            "area_code": codigo_area,
            "flags": [str(f) for f in flags],
            "raw": "" if output_blocked else str(raw_text or ""),
        },
    }

