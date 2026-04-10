from __future__ import annotations

import os
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

import openai

from backend.constants.normativa import is_internal_norma
from backend.services.normativa_monitor_service import get_pending_normative_changes
from backend.services.rag_chat_service import retrieve_context_chunks


def _normalize_text_list(values: list[str] | None, *, fallback: str = "N/D") -> list[str]:
    if not isinstance(values, list):
        return [fallback]
    out = [str(v).strip() for v in values if str(v).strip()]
    return out or [fallback]


def _is_internal_methodology_norm(norma: str) -> bool:
    return is_internal_norma(norma)


def _extract_normas(chunks: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for ch in chunks:
        norma = str(ch.get("norma") or "").strip()
        if not norma or _is_internal_methodology_norm(norma) or norma in seen:
            continue
        seen.add(norma)
        out.append(norma)
    return out


def _extract_chunks_for_response(chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for ch in chunks:
        out.append(
            {
                "norma": str(ch.get("norma") or "N/D"),
                "fuente": str(ch.get("fuente") or str(ch.get("source") or "N/D")),
                "excerpt": str(ch.get("excerpt") or ""),
            }
        )
    return out


def _build_chunks_block(title: str, chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return f"{title}\n- Sin resultados.\n"
    lines = [title]
    for idx, ch in enumerate(chunks, start=1):
        norma = str(ch.get("norma") or "N/D")
        fuente = str(ch.get("fuente") or str(ch.get("source") or "N/D"))
        excerpt = str(ch.get("excerpt") or "").replace("\n", " ").strip()
        if len(excerpt) > 320:
            excerpt = excerpt[:320] + "..."
        lines.append(f"{idx}. norma={norma} | fuente={fuente}")
        lines.append(f"   excerpt={excerpt}")
    return "\n".join(lines) + "\n"


def _get_llm_client() -> openai.OpenAI:
    api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("LLM no configurado: definir DEEPSEEK_API_KEY en .env")
    return openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


def _llm_call(prompt: str) -> str:
    max_attempts = max(1, min(int(os.getenv("LLM_MAX_ATTEMPTS", "3")), 5))
    base_backoff = max(0.2, min(float(os.getenv("LLM_BACKOFF_BASE_SECONDS", "0.8")), 5.0))
    timeout_seconds = max(8.0, min(float(os.getenv("LLM_TIMEOUT_SECONDS", "25")), 60.0))

    def _is_retryable(exc: Exception) -> bool:
        message = str(exc).lower()
        retry_tokens = [
            "timeout",
            "timed out",
            "connection",
            "temporarily unavailable",
            "rate limit",
            "502",
            "503",
            "504",
        ]
        return any(token in message for token in retry_tokens)

    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            client = _get_llm_client()
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=900,
                temperature=0.3,
                timeout=timeout_seconds,
            )
            content = response.choices[0].message.content if response.choices else ""
            text = str(content or "").strip()
            if not text:
                raise RuntimeError("LLM devolvio respuesta vacia")
            return text
        except RuntimeError:
            raise
        except Exception as exc:
            last_exc = exc
            if attempt >= (max_attempts - 1) or not _is_retryable(exc):
                break
            wait_seconds = base_backoff * (2 ** attempt)
            time.sleep(wait_seconds)
    raise RuntimeError(f"Error al generar hallazgo con DeepSeek: {last_exc}")


def _norma_key(text: str) -> str:
    return "".join(ch for ch in str(text or "").upper() if ch.isalnum())


def _pending_warning(normas: list[str]) -> str:
    if not normas:
        return ""
    norm_keys = {_norma_key(n): n for n in normas}
    pending = get_pending_normative_changes()
    seen: set[str] = set()
    lines: list[str] = []
    for row in pending:
        norma = str(row.get("norma") or "").strip()
        k = _norma_key(norma)
        if not k:
            continue
        if not any(k in nk or nk in k for nk in norm_keys):
            continue
        if norma in seen:
            continue
        seen.add(norma)
        lines.append(
            f"⚠️ Verificar vigencia: {norma} tiene cambio detectado pendiente de revision."
        )
    return "\n".join(lines)


def _build_traceability(area_codigo: str, chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    now = datetime.now(timezone.utc).isoformat()
    for ch in chunks:
        norma = str(ch.get("norma") or "").strip()
        fuente = str(ch.get("fuente") or ch.get("source") or "").strip()
        excerpt = str(ch.get("excerpt") or "").strip()
        if not norma and not fuente:
            continue
        chunk_hash = hashlib.sha1(f"{norma}|{fuente}|{excerpt}".encode("utf-8")).hexdigest()[:16]
        out.append(
            {
                "norma": norma or "N/D",
                "fuente_chunk": fuente or "N/D",
                "chunk_id": chunk_hash,
                "area_codigo": str(area_codigo or ""),
                "paper_id": "",
                "timestamp": now,
            }
        )
    return out


def _build_prompt(payload: dict[str, Any], contables: list[dict[str, Any]], nias: list[dict[str, Any]]) -> str:
    afirmaciones = _normalize_text_list(payload.get("afirmaciones_criticas"), fallback="integridad")
    monto = payload.get("monto_estimado")
    monto_txt = f"${monto}" if monto not in {None, ""} else "No estimado"

    return f"""Eres auditor externo senior en Ecuador.

Estructura un hallazgo profesional usando SOLO el contexto y normativa recuperada.
No inventes citas fuera de los chunks.

Formato obligatorio:
## Condicion
## Criterio
## Causa
## Efecto
## Recomendacion
## Normativa activada

Maximo 350 palabras.

CONTEXTO DEL CLIENTE:
- Area: {payload.get("area_nombre")} ({payload.get("area_codigo")})
- Marco: {payload.get("marco")}
- Riesgo: {payload.get("riesgo")}
- Etapa: {payload.get("etapa")}
- Afirmaciones criticas: {afirmaciones}
- Condicion detectada: {payload.get("condicion_detectada")}
- Monto estimado: {monto_txt}
- Causa preliminar: {payload.get("causa_preliminar")}
- Efecto preliminar: {payload.get("efecto_preliminar")}

NORMATIVA CONTABLE RECUPERADA:
{_build_chunks_block("CONTABLE:", contables)}
NORMATIVA AUDITORIA RECUPERADA:
{_build_chunks_block("NIA:", nias)}

Reglas:
- Normativa activada solo con normas de los chunks.
- Nunca mencionar normas internas METODOLOGIA_.
- Redaccion accionable para carta de control interno.
"""


def generate_hallazgo_estructurado(payload: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    cliente_id = str(payload.get("cliente_id") or "").strip()
    area_nombre = str(payload.get("area_nombre") or "Area").strip()
    area_codigo = str(payload.get("area_codigo") or "").strip()
    etapa = str(payload.get("etapa") or "ejecucion").strip()
    marco = str(payload.get("marco") or "ambos").strip()
    riesgo = str(payload.get("riesgo") or "medio").strip()
    afirmaciones = _normalize_text_list(payload.get("afirmaciones_criticas"), fallback="integridad")
    afirmacion_principal = afirmaciones[0]

    query_contable = f"{area_nombre} {afirmacion_principal} hallazgo criterio incumplimiento"
    query_nia = f"{area_nombre} riesgo {riesgo} hallazgo evidencia auditoria"

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(
            retrieve_context_chunks,
            cliente_id,
            query_contable,
            top_k=4,
            marco=marco,
            afirmacion=afirmacion_principal,
            etapa=etapa,
        )
        f2 = pool.submit(
            retrieve_context_chunks,
            cliente_id,
            query_nia,
            top_k=4,
            tipo="NIA",
            etapa=etapa,
        )
        contables_raw = f1.result()
        nias_raw = f2.result()

    def _simplify(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for c in chunks:
            meta = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
            out.append(
                {
                    "norma": str(meta.get("norma") or ""),
                    "fuente": str(meta.get("fuente") or str(c.get("source") or "")),
                    "excerpt": str(c.get("excerpt") or ""),
                    "source": str(c.get("source") or ""),
                    "score": float(c.get("score") or 0.0),
                }
            )
        return out

    contables = _simplify(contables_raw)
    nias = _simplify(nias_raw)
    all_chunks = contables + nias

    prompt = _build_prompt(payload, contables, nias)
    hallazgo = _llm_call(prompt)

    normas = _extract_normas(all_chunks)
    if not normas:
        hallazgo = f"{hallazgo}\n\n⚠️ Sin normativa especifica recuperada para este hallazgo"
    else:
        pending_warning = _pending_warning(normas)
        if pending_warning:
            hallazgo = f"{hallazgo}\n\n{pending_warning}"

    return {
        "area_codigo": area_codigo,
        "area_nombre": area_nombre,
        "hallazgo": hallazgo.strip(),
        "normas_activadas": normas,
        "chunks_usados": _extract_chunks_for_response(all_chunks),
        "trazabilidad": _build_traceability(area_codigo, all_chunks),
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "meta": {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
        },
    }
