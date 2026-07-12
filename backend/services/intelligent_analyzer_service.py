"""
Intelligent Analyzer Service - Detección automática de anomalías con IA
Analiza datos financieros y detecta hallazgos de auditoría usando Claude IA
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
from sqlalchemy.orm import Session

from backend.services.rag_chat_service import _resolved_provider
from backend.services.analysis_history_service import AnalysisHistoryService
from backend.services.grupo_criteria_service import build_analysis_criteria_block

LOGGER = logging.getLogger("socio_ai.intelligent_analyzer")


def _format_financial_data_for_analysis(data: dict[str, Any]) -> str:
    """
    Formatea datos financieros para que IA los analice (version compacta)
    """
    balance = data.get("balance_trial", {})
    if balance:
        sorted_accounts = sorted(
            balance.items(),
            key=lambda x: abs(float(x[1]) if isinstance(x[1], (int, float)) else 0),
            reverse=True,
        )[:50]
        balance_summary = dict(sorted_accounts)
    else:
        balance_summary = balance

    config = data.get("configuracion_industria", {})
    if isinstance(config, dict) and config:
        config_lines = "\n".join([f"- {k}: {v}" for k, v in config.items()])
    else:
        config_lines = "- No industry-specific answers configured"

    risk_signals = data.get("risk_signals", {})
    signal_lines: list[str] = []
    if isinstance(risk_signals, dict):
        items = risk_signals.get("areas") if isinstance(risk_signals.get("areas"), list) else []
        for signal in items[:5]:
            if not isinstance(signal, dict):
                continue
            area_name = str(signal.get("area_nombre") or signal.get("area_id") or "Area")
            nivel = str(signal.get("nivel") or "N/D")
            industry_boost = signal.get("industry_boost", 0)
            mayor_boost = signal.get("mayor_boost", 0)
            drivers = signal.get("drivers", [])
            driver_text = ", ".join([str(x) for x in drivers[:2]]) if isinstance(drivers, list) else ""
            signal_lines.append(
                f"- {area_name} [{nivel}] | industry_boost={industry_boost} | mayor_boost={mayor_boost}"
                + (f" | drivers: {driver_text}" if driver_text else "")
            )
    risk_signal_block = "\n".join(signal_lines) if signal_lines else "- No active risk signals"

    size = data.get("tamano") or data.get("tama?o") or data.get("tama??o") or "Unknown"

    # Criterio experto por grupo del balance (grupos detectados en el TB)
    criteria_block = ""
    try:
        account_names = [str(k) for k in (balance or {}).keys()]
        criteria_block = build_analysis_criteria_block(account_names)
    except Exception as exc:
        LOGGER.warning("No se pudo construir criterio de grupos: %s", exc)

    base = f"""CLIENT FINANCIAL DATA:
Sector: {data.get('sector', 'Unknown')}
Size: {size}
Entity Type: {data.get('tipo_entidad', 'Unknown')}
Framework: {data.get('marco_referencial', 'Unknown')}

INDUSTRY PARAMETERS:
{config_lines}

ACTIVE RISK SIGNALS:
{risk_signal_block}

TOP ACCOUNTS (by balance):
{json.dumps(balance_summary, ensure_ascii=False)}"""

    if criteria_block:
        base = f"{base}\n\n{criteria_block}"
    return base


def _build_analysis_prompt() -> str:
    """
    Construye prompt para analisis inteligente de datos financieros.
    Detecta patrones auditables genericos y usa senales activas como prioridad.
    """
    return """Analyze financial data for 4-6 audit findings. Use the industry parameters when they exist to calibrate expectations and material thresholds. Use ACTIVE RISK SIGNALS as priority lenses: when signals mention WIP, related parties, liquidity, collections, inventory rotation, scholarships, insurance exposure, or guarantees, bias the findings and procedures toward those themes.

If an EXPERT AUDIT CRITERIA section is present, it is your PRIMARY lens — it contains the firm's expert criterion per balance group (riesgos recurrentes, matriz riesgo→prueba→hallazgo, and CHEQUEOS CRUZADOS between groups). Rules for using it:
1. Prioritize findings that match the riesgos recurrentes of the detected groups, evidenced by the actual balances.
2. ALWAYS run the CHEQUEOS CRUZADOS (cross-group coherence checks): inventory vs. revenue (corte), gross margin vs. cost/inventory movement, payroll expense vs. provisions, tax echo of non-deductible items. If the balances show incoherence between linked groups, that IS a finding — cite the specific numbers.
3. Write each finding following the matriz plantillas when available (state the amount, the missing evidence/control, and the norm).
4. In "auditoria" use the concrete tests from the criteria (verbos operativos: pedir, recalcular, conciliar, confirmar), and in "evidencia_buscar" the specific documents the criteria mentions (actas, planillas IESS, certificados, conciliación tributaria).

SIGN CONVENTION (read first): infer the TB sign convention before flagging anything. If most liability, equity and revenue accounts show NEGATIVE balances, the TB uses signed convention (credits negative): negative revenue/equity/liabilities are NORMAL and are NOT findings. Under that convention, flag the OPPOSITE: expenses or assets with credit (negative) sign, or revenue/liabilities/equity with debit (positive) sign. Never report "cuenta de ingresos con saldo negativo" as a finding when the whole credit side is negative.

Also look for generic audit patterns:
- Balances whose sign contradicts the inferred convention (sign reversal, misclassification)
- Accounts with zero depreciation/amortization (asset valuation issues)
- Compensating account pairs (assets=liabilities, suggesting masking)
- Classification discrepancies (related accounts with inconsistent treatment)
- Round amounts or missing accruals (completeness issues)
- Unusual account relationships or missing complementary accounts (e.g., payroll expense without provisiones de beneficios, inventory without provisión de obsolescencia)
Respond in Spanish. Return JSON: {"hallazgos": [{"id":"H00X", "descripcion":"...", "nivel":"CRITICAL|IMPORTANT|MINOR", "norma":"NIC XX", "riesgo":"...", "auditoria":["procedure"], "evidencia_buscar":["doc"], "cuenta_afectada":"...", "monto_impactado":0, "vinculo_cruzado":"grupo A vs grupo B (si aplica)"}], "resumen":"Executive summary", "observaciones_sector":"Sector notes"}"""


def analyze_financial_data(
    cliente_id: str,
    financial_data: dict[str, Any],
    session: Optional[Session] = None,
) -> dict[str, Any]:
    """
    Analiza datos financieros usando IA local o remota y detecta anomalías
    Con RAG para evitar repetir hallazgos anteriores

    Args:
        cliente_id: ID del cliente
        financial_data: Dict con balance_trial, income_statement, etc.
        session: SQLAlchemy session para guardar/recuperar histórico (opcional)

    Returns:
        Dict con hallazgos detectados
    """
    try:
        import os
        from openai import OpenAI

        LOGGER.info(f"🔍 Iniciando análisis inteligente para cliente: {cliente_id}")

        # Intentar LM Studio SOLO si está explícitamente configurado
        lm_studio_url = os.getenv("LM_STUDIO_BASE_URL", "").strip()
        use_lm_studio = False

        if lm_studio_url:
            LOGGER.debug(f"Intentando LM Studio en: {lm_studio_url}")
            try:
                lm_client = OpenAI(api_key="not-needed", base_url=f"{lm_studio_url.rstrip('/')}/v1")
                test_models = lm_client.models.list()
                if test_models.data:
                    model = test_models.data[0].id
                    client = lm_client
                    LOGGER.info(f"✅ LM Studio disponible, modelo: {model}")
                    use_lm_studio = True
            except Exception as e:
                LOGGER.debug(f"LM Studio no disponible: {e}")

        # Usar provider remoto (DeepSeek / OpenAI)
        if not use_lm_studio:
            # Interruptor de privacidad: con AI_CLIENT_DATA_ENABLED=0 los datos
            # financieros del cliente nunca salen a proveedores externos de IA.
            # Un LLM local (LM_STUDIO_BASE_URL) sigue funcionando normalmente.
            if os.getenv("AI_CLIENT_DATA_ENABLED", "1").strip().lower() in {"0", "false", "no"}:
                LOGGER.warning("Analisis IA omitido: AI_CLIENT_DATA_ENABLED=0 (sin envio de datos a proveedores externos)")
                return {
                    "error": "AI_CLIENT_DATA_DISABLED",
                    "hallazgos": [],
                    "message": (
                        "El envio de datos del cliente a proveedores externos de IA esta deshabilitado "
                        "(AI_CLIENT_DATA_ENABLED=0). Configura un LLM local con LM_STUDIO_BASE_URL "
                        "o habilita el envio explicitamente."
                    ),
                }

            provider, api_key = _resolved_provider()
            LOGGER.info(f"🌐 Usando provider remoto: {provider}")

            if not api_key:
                LOGGER.warning(f"⚠️  No API key configured para {cliente_id}")
                return {
                    "error": "No API key configured",
                    "hallazgos": [],
                    "message": "Configura una API key real en .env. La clave actual parece ausente o de ejemplo."
                }

            if provider == "deepseek":
                model = "deepseek-chat"
                base_url = "https://api.deepseek.com"
            else:
                model = "gpt-4o-mini"
                base_url = None

            LOGGER.info(f"🤖 Modelo: {model}")
            client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)

        # Preparar datos y prompt
        formatted_data = _format_financial_data_for_analysis(financial_data)
        system_prompt = _build_analysis_prompt()

        # Agregar contexto RAG si hay sesión
        rag_context = ""
        if session:
            rag_context = AnalysisHistoryService.build_rag_context(session, cliente_id)
            if rag_context:
                LOGGER.debug("📋 RAG context agregado al prompt")

        balance_trial = financial_data.get('balance_trial', {})
        LOGGER.info(f"📊 Balance de prueba: {len(balance_trial)} cuentas, total: ${sum(float(v) if isinstance(v, (int, float)) else 0 for v in balance_trial.values()):.2f}")

        # Llamar a IA
        LOGGER.debug("📤 Enviando solicitud a API de IA...")

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": rag_context + "\n\n" + formatted_data if rag_context else formatted_data
            }
        ]

        try:
            # response_format json_object evita respuestas con texto extra;
            # max_tokens amplio porque 4-6 hallazgos detallados superan 2000.
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            LOGGER.debug(f"Error con parámetros completos, intentando con parámetros mínimos...")
            # Fallback: parámetros mínimos para LM Studio
            response = client.chat.completions.create(
                model=model,
                messages=messages,
            )
        finish_reason = str(getattr(response.choices[0], "finish_reason", "") or "")
        if finish_reason == "length":
            LOGGER.warning("Respuesta de IA truncada por max_tokens (finish_reason=length)")

        # Extraer respuesta
        response_text = response.choices[0].message.content or ""
        LOGGER.debug(f"✅ Respuesta recibida ({len(response_text)} caracteres)")

        # Parsear JSON
        try:
            # Intentar extraer JSON de la respuesta
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                hallazgos_count = len(result.get("hallazgos", []))
                LOGGER.info(f"✅ Análisis completado: {hallazgos_count} hallazgos detectados")
                LOGGER.debug(f"Hallazgos: {[h.get('descripcion', '')[:50] for h in result.get('hallazgos', [])]}")

                # Guardar en histórico si hay sesión
                if session and hallazgos_count > 0:
                    try:
                        AnalysisHistoryService.save_analysis(
                            session=session,
                            cliente_id=cliente_id,
                            hallazgos=result.get("hallazgos", []),
                            resumen=result.get("resumen", ""),
                            observaciones_sector=result.get("observaciones_sector", ""),
                        )
                        LOGGER.info(f"💾 Análisis guardado en histórico para {cliente_id}")
                    except Exception as save_err:
                        LOGGER.warning(f"⚠️  Error guardando histórico: {save_err}")
                        # No interrumpir el análisis si falla el guardado
            else:
                result = {"hallazgos": [], "error": "No se pudo parsear respuesta"}
                LOGGER.warning(f"⚠️  No JSON found in response for {cliente_id}")
        except json.JSONDecodeError as je:
            LOGGER.error(f"❌ JSON parse error para {cliente_id}: {str(je)}")
            LOGGER.debug(f"Response text: {response_text[:200]}")
            result = {
                "hallazgos": [],
                "error": "Error al parsear respuesta de IA",
                "raw_response": response_text[:500]
            }

        return {
            "cliente_id": cliente_id,
            "provider": provider,
            "model": model,
            **result
        }

    except Exception as e:
        LOGGER.error(f"❌ Análisis fallido para {cliente_id}: {e}", exc_info=True)
        error_text = str(e)
        if "401" in error_text or "authentication" in error_text.lower():
            error_text = "Credenciales IA inválidas"
            user_message = "La API key configurada para IA no es válida. Revisa DEEPSEEK_API_KEY u OPENAI_API_KEY en .env."
        else:
            user_message = "Error al analizar datos"
        return {
            "cliente_id": cliente_id,
            "error": error_text,
            "hallazgos": [],
            "message": user_message,
        }


def get_audit_procedures_for_hallazgo(
    hallazgo: dict[str, Any],
    learning_role: str = "semi",
) -> dict[str, Any]:
    """
    Genera procedimientos de auditoría específicos para un hallazgo
    Adaptado al nivel del auditor
    """
    norma = hallazgo.get("norma", "NIC/NIIF")
    descripcion = hallazgo.get("descripcion", "")

    procedures = {
        "nivel": hallazgo.get("nivel", "MENOR"),
        "norma": norma,
        "procedimientos": hallazgo.get("auditoria", []),
        "evidencia": hallazgo.get("evidencia_buscar", []),
        "cantidad_horas_estimadas": {
            "CRÍTICO": 3,
            "IMPORTANTE": 2,
            "MENOR": 1
        }.get(hallazgo.get("nivel", "MENOR"), 1),
    }

    # Adaptar profundidad según learning_role
    if learning_role == "junior":
        procedures["contexto_educativo"] = (
            f"Este hallazgo está relacionado con {norma}. "
            f"Aprenderás a: {descripcion}. "
            f"Sigue cada paso de los procedimientos en orden."
        )
    elif learning_role == "socio":
        procedures["impacto_negocio"] = (
            f"Nivel de riesgo: {hallazgo.get('nivel')}. "
            f"Monto impactado: {hallazgo.get('monto_impactado', 'No cuantificado')}. "
            f"Recomendación: Revisar inmediatamente."
        )

    return procedures
