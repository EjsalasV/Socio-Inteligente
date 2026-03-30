from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from backend.repositories.file_repository import list_documentos, read_hallazgos, read_perfil, read_workflow
from backend.services.prompt_service import render_prompt, validate_minimum_output

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_ROOT = ROOT / "data" / "conocimiento_normativo"
CLIENTES_ROOT = ROOT / "data" / "clientes"


@dataclass
class RetrievedChunk:
    source: str
    excerpt: str
    score: int
    metadata: dict[str, str]


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if len(t) > 2]


def _parse_frontmatter(markdown: str) -> tuple[dict[str, str], str]:
    text = markdown.strip()
    if not text.startswith("---"):
        return {}, markdown
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, markdown
    raw_meta = parts[1]
    body = parts[2].lstrip()
    try:
        loaded = yaml.safe_load(raw_meta) or {}
        if isinstance(loaded, dict):
            meta = {str(k): str(v) for k, v in loaded.items() if v is not None}
            return meta, body
    except Exception:
        pass
    return {}, markdown


def _default_metadata(relative_source: str, file_path: Path) -> dict[str, str]:
    lower = relative_source.lower()
    if "/nias/" in lower:
        norma = "NIA"
        jurisdiccion = "Internacional"
    elif "/niif_pymes/" in lower:
        norma = "NIIF PYMES"
        jurisdiccion = "Internacional"
    elif "/niif_completas/" in lower:
        norma = "NIIF"
        jurisdiccion = "Internacional"
    elif "/tributario_ec/" in lower:
        norma = "Tributario"
        jurisdiccion = "Ecuador"
    elif "/supercias/" in lower:
        norma = "SUPERCIAS"
        jurisdiccion = "Ecuador"
    else:
        norma = "Metodologia"
        jurisdiccion = "Interna"

    updated = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).date().isoformat()
    return {
        "norma": norma,
        "version": "v1",
        "vigente_desde": "",
        "ultima_actualizacion": updated,
        "reemplaza_a": "",
        "jurisdiccion": jurisdiccion,
    }


def _normalize_metadata(relative_source: str, file_path: Path, raw_meta: dict[str, str]) -> dict[str, str]:
    meta = _default_metadata(relative_source, file_path)
    for key in ["norma", "version", "vigente_desde", "ultima_actualizacion", "reemplaza_a", "jurisdiccion"]:
        value = str(raw_meta.get(key, "")).strip() if isinstance(raw_meta, dict) else ""
        if value:
            meta[key] = value
    return meta


def _load_markdown_sources() -> list[tuple[str, str, dict[str, str]]]:
    out: list[tuple[str, str, dict[str, str]]] = []
    if not KNOWLEDGE_ROOT.exists():
        return out
    for path in KNOWLEDGE_ROOT.rglob("*.md"):
        try:
            raw_text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        raw_meta, text = _parse_frontmatter(raw_text)
        text = text.strip()
        if not text:
            continue
        rel = str(path.relative_to(ROOT))
        metadata = _normalize_metadata(rel, path, raw_meta)
        out.append((rel, text, metadata))
    return out


def _load_client_context(cliente_id: str) -> list[tuple[str, str, dict[str, str]]]:
    out: list[tuple[str, str, dict[str, str]]] = []
    perfil_path = CLIENTES_ROOT / cliente_id / "perfil.yaml"
    hallazgos_path = CLIENTES_ROOT / cliente_id / "hallazgos.md"
    docs_text_dir = CLIENTES_ROOT / cliente_id / "documentos_text"

    base_meta = {
        "norma": "Contexto cliente",
        "version": "v1",
        "vigente_desde": "",
        "ultima_actualizacion": "",
        "reemplaza_a": "",
        "jurisdiccion": "Interna",
    }

    if perfil_path.exists():
        try:
            data = yaml.safe_load(perfil_path.read_text(encoding="utf-8")) or {}
            rel = str(perfil_path.relative_to(ROOT))
            meta = dict(base_meta)
            meta["ultima_actualizacion"] = datetime.fromtimestamp(perfil_path.stat().st_mtime, tz=timezone.utc).date().isoformat()
            out.append((rel, yaml.safe_dump(data, allow_unicode=True, sort_keys=False), meta))
        except Exception:
            pass
    if hallazgos_path.exists():
        try:
            text = hallazgos_path.read_text(encoding="utf-8").strip()
            if text:
                rel = str(hallazgos_path.relative_to(ROOT))
                meta = dict(base_meta)
                meta["ultima_actualizacion"] = datetime.fromtimestamp(hallazgos_path.stat().st_mtime, tz=timezone.utc).date().isoformat()
                out.append((rel, text, meta))
        except Exception:
            pass
    if docs_text_dir.exists():
        for path in sorted(docs_text_dir.glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8").strip()
            except Exception:
                continue
            if not text:
                continue
            rel = str(path.relative_to(ROOT))
            meta = dict(base_meta)
            meta["norma"] = "Documentacion cliente"
            meta["ultima_actualizacion"] = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date().isoformat()
            out.append((rel, text, meta))
    return out


def _split_chunks(source: str, text: str, metadata: dict[str, str]) -> list[tuple[str, str, dict[str, str]]]:
    chunks: list[tuple[str, str, dict[str, str]]] = []
    parts = re.split(r"\n\s*\n", text)
    for part in parts:
        cleaned = part.strip()
        if len(cleaned) < 40:
            continue
        if len(cleaned) > 1100:
            cleaned = cleaned[:1100]
        chunks.append((source, cleaned, metadata))
    return chunks


def _retrieve_chunks(cliente_id: str, query: str, *, top_k: int = 5) -> list[RetrievedChunk]:
    query_tokens = set(_tokenize(query))
    if not query_tokens:
        return []

    raw_docs = _load_markdown_sources() + _load_client_context(cliente_id)
    candidates: list[RetrievedChunk] = []
    for source, text, metadata in raw_docs:
        for chunk_source, chunk, chunk_meta in _split_chunks(source, text, metadata):
            tokens = set(_tokenize(chunk))
            score = len(query_tokens.intersection(tokens))
            if score <= 0:
                continue
            candidates.append(RetrievedChunk(source=chunk_source, excerpt=chunk, score=score, metadata=chunk_meta))
    candidates.sort(key=lambda x: x.score, reverse=True)
    return candidates[:top_k]


def retrieve_context_chunks(cliente_id: str, query: str, *, top_k: int = 6) -> list[dict[str, Any]]:
    chunks = _retrieve_chunks(cliente_id, query, top_k=top_k)
    out: list[dict[str, Any]] = []
    for c in chunks:
        out.append(
            {
                "source": c.source,
                "excerpt": c.excerpt,
                "score": c.score,
                "metadata": dict(c.metadata or {}),
            }
        )
    return out


def _is_greeting(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    # Si la frase ya contiene intencion de analisis, no tratar como saludo.
    if _is_risk_question(q) or _is_data_inventory_question(q) or _is_provider_question(q):
        return False
    greetings = {
        "hola",
        "buenas",
        "buen dia",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "hello",
        "hi",
        "hey",
    }
    if q in greetings:
        return True
    cleaned = re.sub(r"[^a-zA-Z0-9\s]+", " ", q)
    tokens = [t for t in cleaned.split() if t]
    if len(tokens) <= 2 and " ".join(tokens) in greetings:
        return True
    return False


def _is_provider_question(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    hints = ["deepseek", "deepsekk", "openai", "modelo", "model", "ia eres", "que modelo", "provider"]
    return any(h in q for h in hints)


def _current_provider_label() -> str:
    provider = (os.getenv("AI_PROVIDER") or "openai").strip().lower()
    if provider == "deepseek":
        model = (os.getenv("DEEPSEEK_CHAT_MODEL") or "deepseek-chat").strip() or "deepseek-chat"
        return f"DeepSeek ({model})"
    model = (os.getenv("OPENAI_CHAT_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"
    return f"OpenAI ({model})"


def _is_data_inventory_question(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    hints = [
        "que datos tienes",
        "que informacion tienes",
        "que sabes",
        "que info tienes",
        "que informacion",
        "que datos",
        "informacion tienes",
        "datos tienes",
        "what data",
        "what info",
        "what do you know",
    ]
    if any(h in q for h in hints):
        return True
    return ("informa" in q or "dato" in q) and ("tienes" in q or "sabes" in q)


def _is_risk_question(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    risk_hints = [
        "riesgo",
        "riesgos",
        "exposicion",
        "area critica",
        "top area",
        "que riesgo tiene",
        "nivel de riesgo",
    ]
    return any(h in q for h in risk_hints)


def _is_next_steps_question(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    hints = [
        "que hacemos primero",
        "que sigue",
        "siguiente paso",
        "por donde empiezo",
        "dame un plan",
        "como arrancamos",
        "que hago primero",
    ]
    return any(h in q for h in hints)


def _risk_answer(cliente_id: str) -> dict[str, Any]:
    perfil = read_perfil(cliente_id) or {}
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    riesgo_global = perfil.get("riesgo_global", {}) if isinstance(perfil.get("riesgo_global"), dict) else {}
    nivel_global = str(riesgo_global.get("nivel") or "MEDIO").upper()

    top_lines: list[str] = []
    try:
        from analysis.ranking_areas import calcular_ranking_areas

        ranking = calcular_ranking_areas(cliente_id)
        if ranking is not None and not ranking.empty:
            vis = ranking.copy()
            if "con_saldo" in vis.columns:
                vis = vis[vis["con_saldo"] == True]  # noqa: E712
            for _, row in vis.head(3).iterrows():
                area = str(row.get("area") or "")
                nombre = str(row.get("nombre") or f"Area {area}")
                score = float(row.get("score_riesgo") or 0.0)
                prioridad = str(row.get("prioridad") or "media").upper()
                top_lines.append(f"- {area} {nombre}: {score:.1f}% ({prioridad})")
    except Exception:
        top_lines = []

    cliente_nombre = str(cliente.get("nombre_legal") or cliente_id)
    if not top_lines:
        answer = (
            f"Riesgo actual del cliente `{cliente_nombre}`: **{nivel_global}**.\n\n"
            "Aun no tengo ranking de areas con saldo suficiente para priorizar. "
            "Siguiente paso: valida que el TB este cargado y luego te devuelvo top 3 areas criticas con score."
        )
        confidence = 0.62
    else:
        answer = (
            f"Riesgo global actual de la holding `{cliente_nombre}`: **{nivel_global}**.\n\n"
            "Top areas por riesgo en este momento:\n"
            + "\n".join(top_lines)
            + "\n\nSi quieres, te digo ahora mismo que pruebas de control y sustantivas ejecutar primero."
        )
        confidence = 0.86

    return {
        "answer": answer,
        "citations": [
            {
                "source": f"data/clientes/{cliente_id}/perfil.yaml",
                "excerpt": "Riesgo global y contexto del cliente",
                "norma": "Contexto cliente",
                "version": "v1",
                "vigente_desde": "",
                "ultima_actualizacion": "",
                "jurisdiccion": "Interna",
            },
        ],
        "context_sources": [f"data/clientes/{cliente_id}/perfil.yaml"],
        "confidence": confidence,
        "provider": "deterministic",
        "model": "risk_snapshot_v1",
        "prompt_meta": {"prompt_id": "risk_snapshot", "prompt_version": "v1"},
    }


def _next_steps_answer(cliente_id: str) -> dict[str, Any]:
    perfil = read_perfil(cliente_id) or {}
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    cliente_nombre = str(cliente.get("nombre_legal") or cliente_id)

    lines: list[str] = []
    try:
        from analysis.ranking_areas import calcular_ranking_areas

        ranking = calcular_ranking_areas(cliente_id)
        if ranking is not None and not ranking.empty:
            vis = ranking.copy()
            if "con_saldo" in vis.columns:
                vis = vis[vis["con_saldo"] == True]  # noqa: E712
            for _, row in vis.head(3).iterrows():
                area = str(row.get("area") or "")
                nombre = str(row.get("nombre") or f"Area {area}")
                score = float(row.get("score_riesgo") or 0.0)
                lines.append(f"{area} {nombre} ({score:.1f}%)")
    except Exception:
        lines = []

    if not lines:
        answer = (
            f"Vamos en este orden para `{cliente_nombre}`:\n\n"
            "1) Confirmar que TB y mayor esten cargados y vigentes.\n"
            "2) Definir materialidad final del encargo.\n"
            "3) Abrir papeles de trabajo y ejecutar pruebas en areas criticas.\n\n"
            "Si quieres, te doy ese plan ya en checklist de trabajo."
        )
        confidence = 0.64
    else:
        answer = (
            f"Perfecto. Para `{cliente_nombre}`, arranquemos asi:\n\n"
            f"1) Prioriza `{lines[0]}` y ejecuta pruebas sustantivas de entrada.\n"
            f"2) Continua con `{lines[1] if len(lines) > 1 else lines[0]}` y valida soportes de cierre.\n"
            f"3) Cierra con `{lines[2] if len(lines) > 2 else lines[-1]}` y documenta conclusion tecnica.\n\n"
            "Si quieres, te lo convierto ahora en tareas concretas de Papeles de Trabajo."
        )
        confidence = 0.84

    return {
        "answer": answer,
        "citations": [
            {
                "source": f"data/clientes/{cliente_id}/perfil.yaml",
                "excerpt": "Contexto base del cliente",
                "norma": "Contexto cliente",
                "version": "v1",
                "vigente_desde": "",
                "ultima_actualizacion": "",
                "jurisdiccion": "Interna",
            },
        ],
        "context_sources": [f"data/clientes/{cliente_id}/perfil.yaml"],
        "confidence": confidence,
        "provider": "deterministic",
        "model": "next_steps_v1",
        "prompt_meta": {"prompt_id": "next_steps", "prompt_version": "v1"},
    }


def _inventory_answer(cliente_id: str) -> dict[str, Any]:
    perfil = read_perfil(cliente_id) or {}
    workflow = read_workflow(cliente_id) or {}
    hallazgos = read_hallazgos(cliente_id) or ""
    docs = list_documentos(cliente_id) or []

    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}
    materialidad = perfil.get("materialidad", {}) if isinstance(perfil.get("materialidad"), dict) else {}

    docs_names = [str(d.get("name") or "") for d in docs if isinstance(d, dict)]
    has_tb = "tb.xlsx" in docs_names
    has_mayor = "mayor.xlsx" in docs_names
    extra_docs = [n for n in docs_names if n not in {"tb.xlsx", "mayor.xlsx"}]
    hallazgos_count = len([x for x in hallazgos.splitlines() if x.strip().startswith("## ")])
    phase = str(workflow.get("current_phase") or encargo.get("fase_actual") or "planificacion").strip()

    mp = 0.0
    if isinstance(materialidad, dict):
        prelim = materialidad.get("preliminar", {}) if isinstance(materialidad.get("preliminar"), dict) else {}
        final = materialidad.get("final", {}) if isinstance(materialidad.get("final"), dict) else {}
        for key in ["materialidad_planeacion", "materialidad_global"]:
            if key in final and final.get(key):
                try:
                    mp = float(final.get(key))
                    break
                except Exception:
                    pass
            if key in prelim and prelim.get(key):
                try:
                    mp = float(prelim.get(key))
                    break
                except Exception:
                    pass

    answer = (
        f"Tengo este contexto activo del cliente `{cliente_id}`:\n\n"
        f"1) Perfil: nombre `{str(cliente.get('nombre_legal') or cliente_id)}`, sector `{str(cliente.get('sector') or 'N/D')}`, marco `{str(encargo.get('marco_referencial') or 'N/D')}`.\n"
        f"2) Datos financieros: TB {'si' if has_tb else 'no'} | Mayor {'si' if has_mayor else 'no'}.\n"
        f"3) Documentos adicionales: {len(extra_docs)} cargados.\n"
        f"4) Hallazgos registrados: {hallazgos_count}.\n"
        f"5) Fase de workflow: `{phase}`.\n"
        f"6) Materialidad de referencia: {'definida' if mp > 0 else 'no definida'}.\n\n"
        "Si quieres, te digo en 30 segundos que falta para pasar a la siguiente etapa."
    )

    return {
        "answer": answer,
        "citations": [
            {
                "source": f"data/clientes/{cliente_id}/perfil.yaml",
                "excerpt": "Perfil de cliente y encargo",
                "norma": "Contexto cliente",
                "version": "v1",
                "vigente_desde": "",
                "ultima_actualizacion": "",
                "jurisdiccion": "Interna",
            },
            {
                "source": f"data/clientes/{cliente_id}/workflow.yaml",
                "excerpt": "Estado de workflow y gates",
                "norma": "Contexto cliente",
                "version": "v1",
                "vigente_desde": "",
                "ultima_actualizacion": "",
                "jurisdiccion": "Interna",
            },
        ],
        "context_sources": [
            f"data/clientes/{cliente_id}/perfil.yaml",
            f"data/clientes/{cliente_id}/workflow.yaml",
        ],
        "confidence": 0.82,
        "provider": "inventory",
        "model": "deterministic",
        "prompt_meta": {"prompt_id": "inventory", "prompt_version": "v1"},
    }


def _client_snapshot(cliente_id: str) -> str:
    perfil = read_perfil(cliente_id) or {}
    workflow = read_workflow(cliente_id) or {}
    hallazgos = read_hallazgos(cliente_id) or ""
    docs = list_documentos(cliente_id) or []
    cliente = perfil.get("cliente", {}) if isinstance(perfil.get("cliente"), dict) else {}
    encargo = perfil.get("encargo", {}) if isinstance(perfil.get("encargo"), dict) else {}
    docs_names = [str(d.get("name") or "") for d in docs if isinstance(d, dict)]
    has_tb = "tb.xlsx" in docs_names
    has_mayor = "mayor.xlsx" in docs_names
    hallazgos_count = len([x for x in hallazgos.splitlines() if x.strip().startswith("## ")])
    return (
        f"Cliente: {str(cliente.get('nombre_legal') or cliente_id)} | "
        f"Sector: {str(cliente.get('sector') or 'N/D')} | "
        f"Marco: {str(encargo.get('marco_referencial') or 'N/D')} | "
        f"Fase: {str(workflow.get('current_phase') or encargo.get('fase_actual') or 'planificacion')} | "
        f"TB: {'si' if has_tb else 'no'} | Mayor: {'si' if has_mayor else 'no'} | "
        f"Docs extra: {len([x for x in docs_names if x not in {'tb.xlsx', 'mayor.xlsx'}])} | "
        f"Hallazgos: {hallazgos_count}"
    )


def _fallback_answer(query: str, cliente_id: str, chunks: list[RetrievedChunk], *, mode: str = "chat") -> dict[str, Any]:
    sources = [c.source for c in chunks]
    first_context = chunks[0].excerpt[:240] if chunks else "Sin contexto recuperado."
    citations: list[dict[str, str]] = []
    for c in chunks:
        meta = c.metadata or {}
        citations.append(
            {
                "source": c.source,
                "excerpt": c.excerpt[:220],
                "norma": str(meta.get("norma") or ""),
                "version": str(meta.get("version") or ""),
                "vigente_desde": str(meta.get("vigente_desde") or ""),
                "ultima_actualizacion": str(meta.get("ultima_actualizacion") or ""),
                "jurisdiccion": str(meta.get("jurisdiccion") or ""),
            }
        )
    if mode == "chat":
        if _is_greeting(query):
            answer = (
                f"Hola. Soy Socio AI y ya tengo activo el contexto del cliente `{cliente_id}`.\n\n"
                "Te puedo ayudar en tres frentes:\n"
                "1) Analisis de riesgo por area.\n"
                "2) Procedimientos segun NIA/NIIF.\n"
                "3) Redaccion de hallazgos y conclusion.\n\n"
                "Dime en que area quieres que trabajemos primero."
            )
            confidence = 0.65
        elif _is_provider_question(query):
            provider_label = _current_provider_label()
            answer = (
                f"Si. En este backend estoy configurado para usar `{provider_label}`.\n\n"
                "Importante:\n"
                "1) Python calcula numeros, materialidad y gates.\n"
                "2) La AI aplica juicio profesional y recomendaciones.\n"
                "3) Si falla el proveedor, activo fallback controlado."
            )
            confidence = 0.7
        elif _is_data_inventory_question(query):
            return _inventory_answer(cliente_id)
        elif _is_next_steps_question(query):
            return _next_steps_answer(cliente_id)
        else:
            answer = (
                f"Entiendo tu consulta sobre `{query}` para `{cliente_id}`.\n\n"
                "Te puedo responder con criterio auditor general, pero para precision de cliente "
                "necesito mas contexto documental (actas, contratos, politicas, anexos) en Client Memory."
            )
            confidence = 0.35 if chunks else 0.18
    else:
        answer = (
            f"No se pudo completar la recuperacion normativa para `{query}` en modo `{mode}`. "
            "Se recomienda validar manualmente NIA/NIIF aplicables y evidencia de soporte."
            f"\n\nContexto clave: {first_context}"
        )
        confidence = 0.30 if chunks else 0.15

    return {
        "answer": answer,
        "citations": citations,
        "context_sources": sources,
        "confidence": confidence,
        "prompt_meta": {"prompt_id": "fallback", "prompt_version": "v1"},
    }


def _llm_answer(query: str, chunks: list[RetrievedChunk], *, mode: str = "chat", cliente_id: str = "") -> dict[str, Any]:
    provider = (os.getenv("AI_PROVIDER") or "openai").strip().lower()
    from openai import OpenAI

    if provider == "deepseek":
        api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY no configurada")
        model = os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat").strip() or "deepseek-chat"
        base_url = (os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").strip()
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY no configurada")
        model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        client = OpenAI(api_key=api_key)

    joined_context = "\n\n".join(
        [
            f"[{c.source}] ({c.metadata.get('norma', 'N/A')} | vigente: {c.metadata.get('vigente_desde', 'N/D')} | "
            f"actualizacion: {c.metadata.get('ultima_actualizacion', 'N/D')}) {c.excerpt}"
            for c in chunks[:6]
        ]
    )
    snapshot = _client_snapshot(cliente_id) if cliente_id else ""
    if snapshot:
        joined_context = f"[SNAPSHOT CLIENTE]\n{snapshot}\n\n{joined_context}".strip()
    instruction, prompt_meta = render_prompt(mode, query=query, context=joined_context)

    user_content = (
        f"Consulta:\n{query}\n\n"
        "Responde de forma conversacional, concreta y accionable para un auditor."
        if mode == "chat"
        else (
            f"Consulta:\n{query}\n\n"
            "Devuelve recomendacion accionable con criterio, pasos y evidencia."
        )
    )

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": user_content},
        ],
        temperature=0.35 if mode == "chat" else 0.2,
    )

    text = getattr(response, "output_text", "") or ""
    if not text.strip():
        text = "No se obtuvo respuesta del modelo."

    ok_min_output, missing = validate_minimum_output(text, mode=mode)
    if not ok_min_output:
        text = (
            f"{text.strip()}\n\n"
            "Nota de control de calidad: la respuesta no cumplio todos los componentes minimos esperados "
            f"({', '.join(missing)})."
        )

    citations: list[dict[str, str]] = []
    for c in chunks:
        meta = c.metadata or {}
        citations.append(
            {
                "source": c.source,
                "excerpt": c.excerpt[:220],
                "norma": str(meta.get("norma") or ""),
                "version": str(meta.get("version") or ""),
                "vigente_desde": str(meta.get("vigente_desde") or ""),
                "ultima_actualizacion": str(meta.get("ultima_actualizacion") or ""),
                "jurisdiccion": str(meta.get("jurisdiccion") or ""),
            }
        )

    return {
        "answer": text.strip(),
        "citations": citations,
        "context_sources": [c.source for c in chunks],
        "confidence": 0.72 if chunks else 0.35,
        "provider": provider,
        "model": model,
        "prompt_meta": prompt_meta,
    }


def generate_chat_response(cliente_id: str, query: str) -> dict[str, Any]:
    if _is_data_inventory_question(query):
        return _inventory_answer(cliente_id)
    if _is_risk_question(query):
        return _risk_answer(cliente_id)
    if _is_next_steps_question(query):
        return _next_steps_answer(cliente_id)
    if _is_greeting(query):
        return _fallback_answer(query, cliente_id, [], mode="chat")
    chunks = _retrieve_chunks(cliente_id, query, top_k=6)
    try:
        # En chat general intentamos LLM aun sin chunks para no degradar preguntas conversacionales.
        return _llm_answer(query, chunks, mode="chat", cliente_id=cliente_id)
    except Exception:
        pass
    return _fallback_answer(query, cliente_id, chunks, mode="chat")


def generate_metodologia_response(cliente_id: str, area: str) -> dict[str, Any]:
    query = f"Metodologia de auditoria para area {area}. Indica riesgos, pruebas y norma aplicable."
    chunks = _retrieve_chunks(cliente_id, query, top_k=6)
    try:
        if chunks:
            return _llm_answer(query, chunks, mode="metodologia", cliente_id=cliente_id)
    except Exception:
        pass
    return _fallback_answer(query, cliente_id, chunks, mode="metodologia")


def generate_judgement_response(cliente_id: str, query: str, *, mode: str = "judgement_risk") -> dict[str, Any]:
    chunks = _retrieve_chunks(cliente_id, query, top_k=8)
    try:
        if chunks:
            return _llm_answer(query, chunks, mode=mode, cliente_id=cliente_id)
    except Exception:
        pass
    return _fallback_answer(query, cliente_id, chunks, mode=mode)
