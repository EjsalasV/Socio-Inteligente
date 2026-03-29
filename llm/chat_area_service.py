from __future__ import annotations

import os

import pandas as pd

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


SYSTEM_PROMPT = """
Eres un socio de auditoria con 20 anos de experiencia Big4.

Revisas el trabajo de un auditor semisenior.

Reglas:
- Vas directo al riesgo concreto del cliente
- No das respuestas genericas
- Identificas errores, omisiones y debilidades
- Cuando detectas riesgos citas NIIF o NIA con referencia tecnica
- Evaluas riesgo de incorreccion material (RIM)

Responde en formato:
1. Evaluacion del area
2. Riesgos clave
3. Recomendaciones concretas
4. Procedimientos sugeridos
"""


def _first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = set(df.columns)
    for c in candidates:
        if c in cols:
            return c
    return None


def construir_contexto(ws_base: dict) -> str:
    area = ws_base.get("area_info", {}) if isinstance(ws_base.get("area_info", {}), dict) else {}
    df = ws_base.get("area_df")
    riesgos = (
        ws_base.get("riesgos_automaticos", [])
        if isinstance(ws_base.get("riesgos_automaticos", []), list)
        else []
    )

    cuentas = "No disponible"
    if isinstance(df, pd.DataFrame) and not df.empty:
        cuenta_col = _first_col(
            df, ["cuenta", "nombre_cuenta", "nombre", "numero_cuenta", "codigo"]
        )
        saldo_col = _first_col(df, ["saldo", "saldo_actual", "saldo_2025", "saldo_preliminar"])
        if cuenta_col and saldo_col:
            cuentas = df[[cuenta_col, saldo_col]].head(10).to_string(index=False)
        else:
            cuentas = df.head(10).to_string(index=False)

    riesgos_txt = (
        "\n".join([f"- {r.get('descripcion', 'Sin descripcion')}" for r in riesgos]) or "Ninguno"
    )

    return f"""
Cliente: {ws_base.get("cliente", "No disponible")}
Sector: {ws_base.get("sector", "No disponible")}
Marco: {ws_base.get("marco_niif", "No disponible")}

Materialidad de desempeno: {ws_base.get("materialidad_desempeno", "No disponible")}

Area actual: {area.get("nombre", ws_base.get("area_name", "No disponible"))} (LS {area.get("codigo_ls", ws_base.get("codigo_ls", "No disponible"))})
Saldo actual: {area.get("saldo", ws_base.get("saldo_total", "No disponible"))}
Variacion: {area.get("variacion_pct", ws_base.get("pct_total", "No disponible"))}
Score de riesgo: {area.get("score_riesgo", ws_base.get("area_score", "No disponible"))}

Cuentas principales:
{cuentas}

Riesgos detectados:
{riesgos_txt}

Aseveraciones esperadas:
{ws_base.get("aseveraciones", ws_base.get("cobertura", {}).get("esperadas", "No disponible"))}

Hallazgos previos:
{ws_base.get("hallazgos_previos", ws_base.get("hallazgos", "Ninguno"))}
"""


def consultar_socio(pregunta: str, ws_base: dict) -> str:
    if not str(pregunta or "").strip():
        return "No se recibio una pregunta valida."

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if OpenAI is None:
        return "No se pudo cargar el cliente OpenAI en este entorno."
    if not api_key:
        return (
            "OPENAI_API_KEY no configurada. Configura la variable para habilitar el chat del socio."
        )

    try:
        client = OpenAI(api_key=api_key)
        contexto = construir_contexto(ws_base)
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": contexto},
                {"role": "user", "content": pregunta},
            ],
        )
        return response.choices[0].message.content or "Sin respuesta del modelo."
    except Exception as e:
        return f"No fue posible consultar al socio en este momento: {e}"
