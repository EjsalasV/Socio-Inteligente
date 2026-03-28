"""
Asistente conversacional de auditoría con contexto completo.
Usa el TB, perfil, ranking y hallazgos del cliente activo.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def _fmt_money(v: Any) -> str:
    try:
        return f"${float(v):,.2f}"
    except Exception:
        return "$0.00"


def _infer_cliente_from_sistema(sistema: str) -> str:
    """
    Tries to infer client id from the system prompt field: 'ID sistema: <cliente>'.
    """
    if not sistema:
        return ""
    m = re.search(r"ID sistema:\s*([^\n\r]+)", sistema)
    if not m:
        return ""
    return m.group(1).strip()


def _cargar_contexto_persistente(cliente: str) -> str:
    """
    Always reads perfil.yaml + hallazgos saved under client folder.
    Returns a compact context block to append to system prompt.
    """
    if not cliente:
        return ""

    base = Path(__file__).resolve().parents[1]
    cdir = base / "data" / "clientes" / cliente
    if not cdir.exists():
        return ""

    # 1) perfil.yaml (source of truth for client profile)
    perfil_raw = ""
    perfil_path = cdir / "perfil.yaml"
    if perfil_path.exists():
        try:
            perfil_obj = yaml.safe_load(
                perfil_path.read_text(encoding="utf-8", errors="replace")
            ) or {}
            # Keep text compact to control prompt size
            perfil_raw = str(perfil_obj)[:7000]
        except Exception:
            try:
                perfil_raw = perfil_path.read_text(
                    encoding="utf-8", errors="replace"
                )[:7000]
            except Exception:
                perfil_raw = ""

    # 2) any findings files in client folder tree
    hallazgo_chunks: list[str] = []
    try:
        files = [
            p for p in cdir.rglob("*")
            if p.is_file() and "hallazgo" in p.name.lower()
        ]
        files = sorted(files)[:20]  # bound number of files
        for p in files:
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
                hallazgo_chunks.append(
                    f"[{p.relative_to(cdir)}]\n{txt[:1800]}"
                )
            except Exception:
                continue
    except Exception:
        pass

    hallazgos_raw = "\n\n".join(hallazgo_chunks)
    if len(hallazgos_raw) > 10000:
        hallazgos_raw = hallazgos_raw[:10000]

    if not perfil_raw and not hallazgos_raw:
        return ""

    return (
        "\n\nCONTEXTO PERSISTENTE DEL ENCARGO (leer siempre antes de responder):\n"
        f"- Fuente perfil.yaml:\n{perfil_raw if perfil_raw else 'No disponible'}\n\n"
        f"- Hallazgos guardados en carpeta cliente:\n{hallazgos_raw if hallazgos_raw else 'Sin archivos de hallazgos detectados'}\n"
    )


def construir_contexto_sistema(
    cliente: str,
    perfil: dict[str, Any],
    resumen_tb: dict[str, Any],
    ranking_areas: pd.DataFrame | None,
    variaciones: pd.DataFrame | None,
    etapa: str = "ejecucion",
) -> str:
    """
    Builds a rich system prompt with all client context.
    """
    # Client info
    c = perfil.get("cliente", {}) if isinstance(perfil, dict) else {}
    enc = perfil.get("encargo", {}) if isinstance(perfil, dict) else {}
    rg = perfil.get("riesgo_global", {}) if isinstance(perfil, dict) else {}
    ctx = perfil.get("contexto_negocio", {}) if isinstance(perfil, dict) else {}
    op = perfil.get("operacion", {}) if isinstance(perfil, dict) else {}
    banderas = perfil.get("banderas_generales", {}) if isinstance(perfil, dict) else {}

    nombre = c.get("nombre_legal", cliente)
    sector = c.get("sector", "N/A")
    tipo = c.get("tipo_entidad", "N/A")
    moneda = c.get("moneda_funcional", "USD")
    periodo = enc.get("anio_activo", "N/A")
    marco = enc.get("marco_referencial", "N/A")
    riesgo_nivel = rg.get("nivel", "N/A")

    # Balance
    activo = abs(float(resumen_tb.get("ACTIVO", 0) or 0))
    pasivo = abs(float(resumen_tb.get("PASIVO", 0) or 0))
    patrimonio = abs(float(resumen_tb.get("PATRIMONIO", 0) or 0))
    ingresos = abs(float(resumen_tb.get("INGRESOS", 0) or 0))
    gastos = abs(float(resumen_tb.get("GASTOS", 0) or 0))

    # Top areas at risk
    areas_riesgo = ""
    if isinstance(ranking_areas, pd.DataFrame) and not ranking_areas.empty:
        mask = ranking_areas.get("con_saldo", pd.Series([True]*len(ranking_areas)))
        df_r = ranking_areas[mask.astype(bool)].head(5)
        lineas = []
        for _, row in df_r.iterrows():
            score = float(row.get("score_riesgo", 0) or 0)
            nombre_a = str(row.get("nombre", ""))
            codigo_a = str(row.get("area", ""))
            prior = str(row.get("prioridad", "")).upper()
            lineas.append(
                f"  - L/S {codigo_a} {nombre_a}: "
                f"score {score:.1f} / prioridad {prior}"
            )
        areas_riesgo = "\n".join(lineas)

    # Top variations
    vars_txt = ""
    if isinstance(variaciones, pd.DataFrame) and not variaciones.empty:
        top_v = variaciones.head(5)
        lineas_v = []
        nom_col = next(
            (c for c in ["nombre", "nombre_cuenta"]
             if c in top_v.columns), None
        )
        imp_col = next(
            (c for c in ["impacto", "variacion_absoluta"]
             if c in top_v.columns), None
        )
        if nom_col and imp_col:
            for _, row in top_v.iterrows():
                lineas_v.append(
                    f"  - {str(row[nom_col])[:40]}: "
                    f"{_fmt_money(row[imp_col])}"
                )
        vars_txt = "\n".join(lineas_v)

    # Operational flags
    flags = []
    if ctx.get("tiene_partes_relacionadas"):
        flags.append("partes relacionadas")
    if op.get("tiene_inventarios_significativos"):
        flags.append("inventarios significativos")
    if op.get("tiene_prestamos_socios"):
        flags.append("préstamos a socios")
    if banderas.get("documentacion_debil"):
        flags.append("documentación débil")
    if banderas.get("riesgo_tributario_general"):
        flags.append("riesgo tributario")
    if rg.get("riesgo_negocio_en_marcha"):
        flags.append("riesgo negocio en marcha")

    sistema = f"""Eres SocioAI, un asistente experto en auditoría financiera.
Tienes acceso completo al expediente del cliente activo.

═══════════════════════════════════════
CLIENTE ACTIVO: {nombre}
═══════════════════════════════════════
- ID sistema: {cliente}
- Sector: {sector} | Tipo: {tipo}
- Período: {periodo} | Marco: {marco}
- Moneda: {moneda}
- Etapa actual: {etapa}
- Riesgo global: {riesgo_nivel.upper()}

BALANCE GENERAL:
- Activos:    {_fmt_money(activo)}
- Pasivos:    {_fmt_money(pasivo)}
- Patrimonio: {_fmt_money(patrimonio)}
- Ingresos:   {_fmt_money(ingresos)}
- Gastos:     {_fmt_money(gastos)}

ÁREAS DE MAYOR RIESGO:
{areas_riesgo if areas_riesgo else "  Sin datos de ranking disponibles."}

VARIACIONES SIGNIFICATIVAS:
{vars_txt if vars_txt else "  Sin variaciones cargadas."}

BANDERAS ACTIVAS:
{(", ".join(flags)) if flags else "Sin banderas críticas detectadas."}

═══════════════════════════════════════
INSTRUCCIONES:
- Responde siempre en español, tono profesional pero directo.
- Cuando cites cifras, usa los datos reales del cliente.
- Si te preguntan por un área específica, da criterio auditor concreto.
- Si te preguntan qué revisar primero, prioriza por score de riesgo.
- Si no tienes datos suficientes, dilo claramente.
- Máximo 300 palabras por respuesta salvo que pidan más detalle.
- No inventes cifras que no estén en el contexto.
"""
    return sistema


def generar_respuesta_asistente(
    messages: list[dict[str, str]],
    sistema: str,
    cliente: str | None = None,
) -> str:
    """
    Calls DeepSeek with full conversation history.
    Returns assistant response text.
    """
    from llm.llm_client import _get_deepseek_key
    from openai import OpenAI

    key = _get_deepseek_key()
    if not key:
        return (
            "⚠️ Sin API key configurada. "
            "Agrega DEEPSEEK_API_KEY en "
            "Streamlit Cloud → Settings → Secrets."
        )

    try:
        _cliente_ctx = (cliente or "").strip() or _infer_cliente_from_sistema(sistema)
        contexto_persistente = _cargar_contexto_persistente(_cliente_ctx)
        sistema_final = f"{sistema}{contexto_persistente}" if contexto_persistente else sistema

        client = OpenAI(
            api_key=key,
            base_url="https://api.deepseek.com",
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": sistema_final},
                *messages,
            ],
            max_tokens=600,
            temperature=0.4,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        return f"Error al contactar la IA: {e}"


SUGERENCIAS_INICIALES = [
    "¿Qué área debo revisar primero en este cliente?",
    "¿Cuáles son los principales riesgos de este encargo?",
    "¿Qué documentos debo pedir para las CxC?",
    "Resume el balance del cliente en 3 puntos clave.",
    "¿Hay banderas de fraude en este cliente?",
    "¿Qué procedimientos sugiere para las inversiones?",
]
