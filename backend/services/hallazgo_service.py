from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

import openai

from backend.services.rag_chat_service import retrieve_context_chunks


def _normalize_text_list(values: list[str] | None, *, fallback: str = "N/D") -> list[str]:
    if not isinstance(values, list):
        return [fallback]
    out = [str(v).strip() for v in values if str(v).strip()]
    return out or [fallback]


def _is_internal_methodology_norm(norma: str) -> bool:
    return str(norma or "").strip().upper().startswith("METODOLOGIA_")


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
    client = _get_llm_client()
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=900,
        temperature=0.3,
    )
    content = response.choices[0].message.content if response.choices else ""
    return str(content or "").strip()


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

    return {
        "area_codigo": area_codigo,
        "area_nombre": area_nombre,
        "hallazgo": hallazgo.strip(),
        "normas_activadas": normas,
        "chunks_usados": _extract_chunks_for_response(all_chunks),
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "meta": {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
        },
    }
