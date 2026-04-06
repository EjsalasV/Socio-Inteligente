from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

import openai

from backend.services.rag_chat_service import retrieve_context_chunks


def get_llm_client() -> openai.OpenAI:
    api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("LLM no configurado: definir DEEPSEEK_API_KEY en .env")
    return openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


def llamar_llm(prompt: str) -> str:
    client = get_llm_client()
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.3,
    )
    content = response.choices[0].message.content if response.choices else ""
    return str(content or "").strip()


def _normalize_text_list(values: list[str] | None, *, fallback: str = "N/D") -> list[str]:
    if not isinstance(values, list):
        return [fallback]
    out = [str(v).strip() for v in values if str(v).strip()]
    return out or [fallback]


def _is_internal_methodology_norm(norma: str) -> bool:
    return str(norma or "").strip().upper().startswith("METODOLOGIA_")


def _build_chunks_block(title: str, chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return f"{title}\n- Sin resultados.\n"
    lines = [title]
    for idx, ch in enumerate(chunks, start=1):
        norma = str(ch.get("norma") or "N/D")
        fuente = str(ch.get("fuente") or str(ch.get("source") or "N/D"))
        excerpt = str(ch.get("excerpt") or "").replace("\n", " ").strip()
        if len(excerpt) > 300:
            excerpt = excerpt[:300] + "..."
        lines.append(f"{idx}. norma={norma} | fuente={fuente}")
        lines.append(f"   excerpt={excerpt}")
    return "\n".join(lines) + "\n"


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


def _extract_normas(chunks: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    normas: list[str] = []
    for ch in chunks:
        norma = str(ch.get("norma") or "").strip()
        if not norma or _is_internal_methodology_norm(norma) or norma in seen:
            continue
        seen.add(norma)
        normas.append(norma)
    return normas


def _strip_internal_norms_from_briefing(briefing: str) -> str:
    lines = str(briefing or "").splitlines()
    return "\n".join([line for line in lines if "METODOLOGIA_" not in line]).strip()


def _build_prompt(payload: dict[str, Any], contables: list[dict[str, Any]], nias: list[dict[str, Any]]) -> str:
    afirmaciones = _normalize_text_list(payload.get("afirmaciones_criticas"), fallback="integridad")
    patrones = _normalize_text_list(payload.get("patrones_historicos"), fallback="Sin patrones historicos")
    hallazgos = _normalize_text_list(payload.get("hallazgos_previos"), fallback="Sin hallazgos previos")

    chunks_contables = _build_chunks_block("CONTABLES:", contables)
    chunks_nias = _build_chunks_block("AUDITORIA_NIA:", nias)

    return f"""---SISTEMA---
Eres un auditor externo senior en Ecuador con criterio practico.
Responde SIEMPRE en este formato exacto, sin agregar secciones extra:

## Por que importa esta area
[2-3 lineas especificas al cliente, no genericas]

## Afirmaciones mas expuestas
[lista con una linea de justificacion por afirmacion]

## Procedimientos sugeridos
[maximo 5, en orden de prioridad, accionables]

## Errores comunes en este tipo de empresa
[maximo 3, especificos para el sector/marco]

## Alertas tributarias
[solo si aplica para Ecuador, maximo 2]

## Normativa activada
[solo las normas que el RAG recupero, con una linea de por que aplica]

Responde en modo practico. No des teoria.
Se especifico al cliente descrito, no generico.
Maximo 400 palabras en total.

---CONTEXTO DEL CLIENTE---
Area: {payload.get("area_nombre")} | Codigo: {payload.get("area_codigo")}
Marco: {payload.get("marco")} | Riesgo asignado: {payload.get("riesgo")}
Materialidad: ${payload.get("materialidad")}
Afirmaciones criticas: {afirmaciones}
Patrones historicos: {patrones}
Hallazgos previos: {hallazgos}

---NORMATIVA RECUPERADA POR RAG---
{chunks_contables}
{chunks_nias}

---INSTRUCCION FINAL---
Genera el briefing para esta area especifica.
Basa la seccion "Normativa activada" SOLO en los chunks anteriores,
no en memoria del modelo.
Nunca cites normas internas con prefijo "METODOLOGIA_".
"""


def _area_terms(area_nombre: str, afirmaciones: list[str]) -> str:
    name = str(area_nombre or "").lower()
    norm = (
        name.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )
    mapping: list[tuple[list[str], str]] = [
        (["inventario"], "valuacion existencia costo VNR deterioro"),
        (["ingreso", "ventas"], "ocurrencia corte reconocimiento ventas"),
        (["cobrar", "cxc"], "valuacion deterioro provision circularizacion"),
        (["efectivo", "banco", "caja"], "existencia reconciliacion conciliacion"),
        (["patrimonio"], "integridad clasificacion dividendos"),
        (["impuesto", "tribut"], "diferido temporaria conciliacion tributaria"),
        (["ppe", "propiedad", "planta", "equipo"], "valuacion depreciacion deterioro"),
    ]
    for keys, terms in mapping:
        if any(k in norm for k in keys):
            return terms
    return " ".join([a for a in afirmaciones if a]).strip()


def generate_area_briefing(payload: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    cliente_id = str(payload.get("cliente_id") or "").strip()
    area_nombre = str(payload.get("area_nombre") or "Area").strip()
    area_codigo = str(payload.get("area_codigo") or "").strip()
    etapa = str(payload.get("etapa") or "ejecucion").strip()
    marco = str(payload.get("marco") or "ambos").strip()
    riesgo = str(payload.get("riesgo") or "medio").strip()
    afirmaciones = _normalize_text_list(payload.get("afirmaciones_criticas"), fallback="integridad")
    afirmacion_principal = afirmaciones[0]

    area_specific = _area_terms(area_nombre, afirmaciones)
    query_contable = f"{area_nombre} {afirmacion_principal} procedimientos riesgos {area_specific}".strip()
    query_nia = f"{area_nombre} riesgo {riesgo} afirmaciones auditoria"

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

    briefing = llamar_llm(prompt)
    briefing = _strip_internal_norms_from_briefing(briefing)

    normas = _extract_normas(all_chunks)
    if not normas:
        briefing = f"{briefing}\n\n⚠️ Sin normativa especifica recuperada para esta area"

    return {
        "area_codigo": area_codigo,
        "area_nombre": area_nombre,
        "briefing": briefing.strip(),
        "normas_activadas": normas,
        "chunks_usados": _extract_chunks_for_response(all_chunks),
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "meta": {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
        },
    }
