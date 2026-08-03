from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.repositories.file_repository import read_perfil, repo
from backend.services.context_document_service import list_documents


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _draft_path(cliente_id: str) -> Path:
    return repo.cliente_dir(cliente_id) / "entity_profile_draft.json"


def _load_saved(cliente_id: str) -> dict[str, Any]:
    path = _draft_path(cliente_id)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _save(cliente_id: str, payload: dict[str, Any]) -> None:
    path = _draft_path(cliente_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def _fact(key: str, label: str, value: Any, source: str, *, status: str = "declared") -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "value": value,
        "source": source,
        "status": status,
    }


def _question(question_id: str, text: str, reason: str, *, critical: bool = True, round_number: int = 1) -> dict[str, Any]:
    return {"id": question_id, "text": text, "reason": reason, "critical": critical, "round": round_number}


def _answered(answers: dict[str, Any], question_ids: list[str]) -> bool:
    return all(str(answers.get(question_id) or "").strip() for question_id in question_ids)


def _is_pending_answer(value: Any) -> bool:
    normalized = str(value or "").strip().lower()
    return any(marker in normalized for marker in (
        "pendiente", "por confirmar", "aún no", "aun no", "no disponible",
        "se evaluará", "se evaluara", "no definido", "por definir",
    ))


PENDING_STATUSES = {"pending", "requested", "received", "confirmed", "not_applicable"}


def _question_area(question_id: str) -> str:
    if question_id.startswith(("revenue", "activity")):
        return "Ingresos y CxC"
    if question_id.startswith("consolidation"):
        return "Consolidación"
    if question_id.startswith("estimate") or question_id == "relevant_estimates":
        return "Estimaciones"
    if question_id.startswith("audit_approach"):
        return "Enfoque por ciclos"
    if question_id.startswith("prior_findings"):
        return "Hallazgos anteriores"
    if question_id.startswith("regulatory"):
        return "Entorno regulatorio"
    return "Conocimiento de la entidad"


def _question_impact(question: dict[str, Any]) -> str:
    question_id = str(question.get("id") or "")
    if question_id.startswith("revenue"):
        return "Mantiene provisionales las conclusiones sobre reconocimiento, exactitud y corte de ingresos."
    if question_id.startswith("audit_approach"):
        return "El enfoque y los procedimientos del ciclo permanecen provisionales."
    if question_id.startswith("estimate") or question_id == "relevant_estimates":
        return "No permite cerrar la comprensión de datos, supuestos e incertidumbre de estimación."
    if question_id.startswith("consolidation"):
        return "Mantiene pendiente la comprensión del perímetro y proceso de consolidación."
    return str(question.get("reason") or "La comprensión del cliente permanece provisional.")


def _build_pending_items(
    questions: list[dict[str, Any]], answers: dict[str, Any], saved: dict[str, Any]
) -> list[dict[str, Any]]:
    registry_raw = saved.get("pending_items")
    registry = {
        str(item.get("question_id")): dict(item)
        for item in registry_raw
        if isinstance(item, dict) and item.get("question_id")
    } if isinstance(registry_raw, list) else {}
    question_map = {str(question.get("id")): question for question in questions}
    now = _now()
    for question_id, question in question_map.items():
        answer = str(answers.get(question_id) or "").strip()
        existing = registry.get(question_id)
        if _is_pending_answer(answer):
            item = existing or {}
            item.update({
                "question_id": question_id,
                "question": question.get("text"),
                "reason": question.get("reason"),
                "area": _question_area(question_id),
                "impact": _question_impact(question),
                "answer": answer,
                "status": str(item.get("status") or "pending") if str(item.get("status") or "pending") in PENDING_STATUSES else "pending",
                "created_at": item.get("created_at") or now,
                "updated_at": item.get("updated_at") or now,
            })
            registry[question_id] = item
        elif existing:
            existing.update({"answer": answer, "question": question.get("text"), "reason": question.get("reason")})
            if existing.get("status") not in {"confirmed", "not_applicable"}:
                existing["status"] = "confirmed"
                existing["updated_at"] = now
    return sorted(registry.values(), key=lambda item: (item.get("status") in {"confirmed", "not_applicable"}, item.get("created_at", "")))


def build_profile_draft(cliente_id: str) -> dict[str, Any]:
    perfil = read_perfil(cliente_id)
    cliente = perfil.get("cliente") if isinstance(perfil.get("cliente"), dict) else {}
    encargo = perfil.get("encargo") if isinstance(perfil.get("encargo"), dict) else {}
    documents = list_documents(cliente_id)
    saved = _load_saved(cliente_id)
    answers = saved.get("answers") if isinstance(saved.get("answers"), dict) else {}

    prior_financials = next(
        (item for item in documents if item.get("document_type") == "prior_financial_statements"),
        None,
    )
    prior_control = next(
        (item for item in documents if item.get("document_type") == "prior_internal_control"),
        None,
    )
    client_dir = repo.cliente_dir(cliente_id)
    has_tb = any((client_dir / name).exists() for name in ("tb.xlsx", "tb.csv"))
    has_mayor = any((client_dir / name).exists() for name in ("mayor.xlsx", "mayor.csv"))

    facts: list[dict[str, Any]] = []
    for key, label, value, source in [
        ("legal_name", "Nombre legal", cliente.get("nombre_legal"), "onboarding"),
        ("sector", "Sector declarado", cliente.get("sector"), "onboarding"),
        ("country", "Pais", cliente.get("pais"), "onboarding"),
        ("current_period", "Periodo actual", encargo.get("anio_activo"), "onboarding"),
        ("accounting_framework", "Marco contable", encargo.get("marco_referencial"), "onboarding"),
        ("financial_statement_scope", "Tipo de estados financieros", encargo.get("alcance_estados"), "configuración del encargo"),
        ("visit_plan", "Esquema de visitas", encargo.get("esquema_visitas"), "configuración del encargo"),
        ("reporting_period", "Periodo del encargo", f"{encargo.get('fecha_inicio_periodo', '')} a {encargo.get('fecha_cierre_periodo', '')}".strip(" a"), "configuración del encargo"),
        ("tb_cutoff", "Corte del balance cargado", encargo.get("fecha_corte_tb"), "configuración del encargo"),
    ]:
        if value not in (None, ""):
            facts.append(_fact(key, label, value, source))

    sources = [
        {
            "type": "trial_balance",
            "label": "Balance de comprobacion preliminar actual",
            "available": has_tb,
            "status": "available" if has_tb else "missing",
            "authority": "accounting_data",
        },
        {
            "type": "general_ledger",
            "label": "Libro mayor actual",
            "available": has_mayor,
            "status": "available" if has_mayor else "optional_missing",
            "authority": "accounting_data",
        },
    ]
    for item in documents:
        sources.append(
            {
                "type": item.get("document_type"),
                "label": item.get("document_label"),
                "name": item.get("name"),
                "period": item.get("period"),
                "available": item.get("status") in {"available", "available_with_warnings"},
                "status": item.get("status"),
                "authority": item.get("authority"),
                "document_id": item.get("id"),
            }
        )

    questions: list[dict[str, Any]] = []
    if prior_financials:
        questions.extend(
            [
                _question(
                    "activity_continues",
                    "¿La actividad y el modelo de ingresos descritos en los estados financieros anteriores continúan vigentes?",
                    "El periodo anterior es un antecedente; debe confirmarse su vigencia actual.",
                ),
                _question(
                    "framework_continues",
                    "¿La entidad continúa aplicando el mismo marco contable del periodo anterior?",
                    "Un cambio de marco modifica el conocimiento y los criterios aplicables.",
                ),
                _question(
                    "prior_opinion",
                    "¿La opinión anterior fue modificada, incluyó énfasis u otros asuntos relevantes?",
                    "La opinión anterior orienta preguntas, pero no se hereda automáticamente.",
                ),
            ]
        )
    else:
        questions.extend(
            [
                _question("main_activity", "¿Cuál es la actividad principal de la entidad?", "No se cargaron estados financieros anteriores."),
                _question("revenue_model", "¿Cómo genera principalmente sus ingresos?", "El modelo de ingresos activa riesgos y preguntas diferentes."),
                _question("accounting_framework_confirm", "¿Qué marco contable aplica la entidad?", "El marco debe ser confirmado por el auditor."),
            ]
        )

    questions.extend(
        [
            _question("significant_changes", "¿Qué cambió significativamente durante el periodo actual?", "Los cambios suelen explicar nuevas cuentas y riesgos."),
            _question("regulatory_environment", "¿La entidad está sujeta a un regulador especializado?", "La regulación modifica requerimientos y áreas de atención."),
            _question("relevant_estimates", "¿Qué estimaciones contables considera relevantes la administración?", "Las estimaciones requieren comprender datos, supuestos e incertidumbre."),
        ]
    )
    if prior_control:
        questions.append(
            _question(
                "prior_findings_status",
                "¿Cuál es el estado actual de las deficiencias comunicadas en el periodo anterior?",
                "Los hallazgos anteriores deben confirmarse como corregidos, vigentes o no aplicables.",
            )
        )

    round_one_ids = [question["id"] for question in questions]
    if _answered(answers, round_one_ids):
        if str(encargo.get("alcance_estados") or "") == "consolidated":
            questions.extend([
                _question("consolidation_components", "¿Cuáles son la controladora y los componentes incluidos en la consolidación?", "Permite comprender el perímetro y la importancia de cada componente.", critical=False, round_number=2),
                _question("consolidation_process", "¿Quién prepara la matriz y propone las eliminaciones, quién las revisa y aprueba por parte de la entidad, y existen componentes auditados por otros auditores?", "Distingue el trabajo del auditor de la responsabilidad de la administración sobre la información consolidada.", critical=False, round_number=2),
            ])
        changes = str(answers.get("significant_changes") or "").lower()
        if any(word in changes for word in ("poco", "redu", "aument", "cambio")):
            questions.append(_question("significant_changes_quantified", "Cuantifica el cambio indicado y señala si afectó clientes, contratos o cuentas significativas.", "Una descripción general no permite evaluar magnitud ni alcance.", critical=False, round_number=2))
        questions.extend([
            _question("revenue_process_detail", "¿Cómo nace, se aprueba, factura y cobra una operación de ingreso típica?", "Conecta el modelo de negocio con cuentas, controles y aseveraciones.", critical=False, round_number=2),
            _question("revenue_measurement_model", "¿Cómo se determina el importe del servicio: horas y tarifas, precio fijo, iguala mensual, hitos, éxito u otra modalidad? Indica qué evidencia deja el cálculo.", "Evita asumir que todos los servicios profesionales se facturan por horas y permite orientar corte, exactitud e ingresos diferidos.", critical=False, round_number=2),
            _question("audit_approach_by_cycle", "Para Ingresos y CxC, Compras y CxP, Nómina y Consolidación, indica el enfoque previsto: sustantivo, combinado, confianza en controles o pendiente de evaluar; explica brevemente el fundamento.", "El enfoque no debe inferirse de una carta de control interno: se decide por ciclo con base en riesgos y evidencia sobre controles.", critical=False, round_number=2),
            _question("estimates_breakdown", "Para cada estimación relevante, indica responsable, datos utilizados, supuestos y frecuencia de revisión.", "Separa estimaciones, juicios y políticas para orientar el trabajo posterior.", critical=False, round_number=2),
        ])
        if prior_control:
            questions.append(_question("prior_findings_breakdown", "Indica por cada hallazgo anterior si está corregido, parcialmente corregido, vigente, no aplicable o pendiente de verificar.", "No todos los antecedentes conservan el mismo estado en el periodo actual.", critical=False, round_number=2))

    round_two_ids = [question["id"] for question in questions if question.get("round") == 2]
    if round_two_ids and _answered(answers, round_two_ids):
        # Evaluar suficiencia por componentes, no solo por longitud.
        revenue_detail = str(answers.get("revenue_process_detail") or "").lower()
        revenue_missing: list[str] = []
        if not any(token in revenue_detail for token in ("aprueb", "autoriza", "valid", "revisa")):
            revenue_missing.append("quién aprueba o valida el servicio y la facturación")
        if not any(token in revenue_detail for token in ("cobr", "pago", "recaud", "cartera")):
            revenue_missing.append("cómo se gestiona y registra el cobro")
        if revenue_missing:
            questions.append(_question(
                "revenue_process_clarification",
                "Completa el ciclo de ingresos indicando " + " y ".join(revenue_missing) + ".",
                "La respuesta anterior describe la prestación y facturación, pero no cubre todo el flujo ni sus responsables.",
                critical=False,
                round_number=3,
            ))

        measurement = str(answers.get("revenue_measurement_model") or "").lower()
        if not any(token in measurement for token in ("hora", "tarifa", "fijo", "iguala", "mensual", "hito", "exito", "éxito", "importe", "valor")):
            questions.append(_question(
                "revenue_measurement_clarification",
                "Aclara la modalidad o modalidades de precio aplicables y qué documento permite recalcular cada importe facturado.",
                "Aún no existe base suficiente para proponer pruebas de exactitud y corte sin inventar un modelo de facturación.",
                critical=False,
                round_number=3,
            ))

        approach = str(answers.get("audit_approach_by_cycle") or "").lower()
        cycles_covered = sum(any(token in approach for token in group) for group in (("ingreso", "cxc", "cobrar"), ("compra", "cxp", "pagar"), ("nómina", "nomina"), ("consolid",)))
        if cycles_covered < 3 or not any(token in approach for token in ("sustant", "combin", "control", "pendiente")):
            questions.append(_question(
                "audit_approach_clarification",
                "Completa el enfoque por ciclo pendiente e indica si la confianza en controles está sustentada, se evaluará o no se prevé utilizar.",
                "SocioAI puede recomendar un enfoque, pero necesita distinguir la decisión del auditor de una inferencia automática.",
                critical=False,
                round_number=3,
            ))

        estimates_detail = str(answers.get("estimates_breakdown") or "").lower()
        estimates_missing: list[str] = []
        if not any(token in estimates_detail for token in ("dato", "base", "sistema", "reporte")):
            estimates_missing.append("datos o bases utilizadas")
        if not any(token in estimates_detail for token in ("supuest", "tasa", "vida útil", "vida util", "probabilidad", "hipótes", "hipotes")):
            estimates_missing.append("supuestos principales")
        if estimates_missing:
            questions.append(_question(
                "estimates_clarification",
                "Para cada estimación relevante, completa " + " y ".join(estimates_missing) + ", e identifica la evidencia disponible.",
                "Responsable, aprobación y frecuencia no bastan para comprender cómo se determina cada estimación.",
                critical=False,
                round_number=3,
            ))

        consolidation_detail = str(answers.get("consolidation_process") or "").lower()
        has_preparer = any(token in consolidation_detail for token in ("prepar", "elabor", "matriz", "auditor", "equipo"))
        has_management_review = any(token in consolidation_detail for token in ("aprueb", "acepta", "valida", "autoriza")) and any(
            token in consolidation_detail for token in ("contadora", "contador", "financ", "administr", "cliente", "gerencia")
        )
        if not has_preparer or not has_management_review:
            questions.append(_question(
                "consolidation_process_clarification",
                "Aclara quién prepara la matriz y propone las eliminaciones, y quién dentro de la entidad las revisa, acepta y aprueba.",
                "El auditor puede preparar su matriz y proponer ajustes; la administración conserva la responsabilidad de revisar, aceptar y aprobar la información consolidada.",
                critical=False,
                round_number=3,
            ))

        vague = [question_id for question_id in round_two_ids if len(str(answers.get(question_id) or "").strip()) < 25]
        if vague and not any(question.get("round") == 3 for question in questions):
            questions.append(_question("final_clarifications", "Amplía las respuestas breves de la ronda anterior e identifica documentos o responsables que permitan verificarlas.", "SocioAI aún detecta respuestas insuficientes para cerrar el conocimiento inicial.", critical=False, round_number=3))

    unanswered_critical = [q["id"] for q in questions if q["critical"] and not str(answers.get(q["id"]) or "").strip()]
    pending_items = _build_pending_items(questions, answers, saved)
    pending_confirmations = [
        str(item.get("question_id")) for item in pending_items
        if item.get("status") not in {"confirmed", "not_applicable"}
    ]
    active_round = min((q["round"] for q in questions if q["id"] in unanswered_critical), default=max((q["round"] for q in questions), default=1))
    visible_questions = [q for q in questions if q["round"] <= active_round]
    limitations: list[str] = []
    if not prior_financials:
        limitations.append("No se proporcionaron estados financieros auditados anteriores; el perfil dependerá más de respuestas declaradas.")
    if not has_tb:
        limitations.append("No se ha cargado el balance de comprobación actual; aún no pueden contrastarse antecedentes con saldos actuales.")
    if not has_mayor:
        limitations.append("El mayor es opcional y no está disponible; no se analizarán movimientos ni contrapartidas.")
    if pending_confirmations:
        limitations.append(f"Existen {len(pending_confirmations)} respuestas pendientes de confirmar; no se tratarán como hechos ni conclusiones.")

    if saved.get("status") in {"confirmed", "provisional"} and not unanswered_critical:
        profile_status = "provisional" if pending_confirmations else "confirmed"
    else:
        profile_status = "needs_answers"

    draft = {
        "cliente_id": cliente_id,
        "status": profile_status,
        "generated_at": _now(),
        "facts": facts,
        "sources": sources,
        "questions": visible_questions,
        "active_round": active_round,
        "max_rounds": 3,
        "answers": answers,
        "unanswered_critical": unanswered_critical,
        "pending_confirmations": pending_confirmations,
        "pending_items": pending_items,
        "limitations": limitations,
        "transparency_note": "Los datos declarados, documentos, inferencias y preguntas pendientes se mantienen separados. Ningún riesgo se considera confirmado por este borrador.",
    }
    if isinstance(saved.get("analysis"), dict):
        draft["analysis"] = saved["analysis"]
    _save(cliente_id, draft)
    return draft


def update_profile_answers(cliente_id: str, answers: dict[str, Any]) -> dict[str, Any]:
    current = build_profile_draft(cliente_id)
    allowed = {str(question.get("id")) for question in current.get("questions", [])}
    merged = dict(current.get("answers") or {})
    for key, value in answers.items():
        if key in allowed:
            merged[key] = value
    current["answers"] = merged
    current["status"] = "needs_answers"
    _save(cliente_id, current)
    return build_profile_draft(cliente_id)


def confirm_profile_draft(cliente_id: str, confirmed_by: str) -> dict[str, Any]:
    current = build_profile_draft(cliente_id)
    if current.get("unanswered_critical"):
        raise ValueError("Responde las preguntas críticas antes de confirmar el perfil.")
    current["status"] = "provisional" if current.get("pending_confirmations") else "confirmed"
    current["confirmed_by"] = confirmed_by
    current["confirmed_at"] = _now()
    _save(cliente_id, current)
    return current


def update_pending_item(
    cliente_id: str,
    question_id: str,
    *,
    status: str,
    answer: str,
) -> dict[str, Any]:
    normalized_status = str(status or "").strip().lower()
    if normalized_status not in PENDING_STATUSES:
        raise ValueError("Estado de pendiente no válido.")
    current = build_profile_draft(cliente_id)
    question_ids = {str(question.get("id")) for question in current.get("questions", [])}
    if question_id not in question_ids:
        raise ValueError("La pregunta pendiente no existe en el perfil actual.")
    answer_text = str(answer or "").strip()
    if normalized_status == "confirmed" and (not answer_text or _is_pending_answer(answer_text)):
        raise ValueError("Para confirmar el pendiente debes registrar una respuesta concreta.")
    current_answers = dict(current.get("answers") or {})
    if answer_text:
        current_answers[question_id] = answer_text
    current["answers"] = current_answers
    items = current.get("pending_items") if isinstance(current.get("pending_items"), list) else []
    for item in items:
        if isinstance(item, dict) and str(item.get("question_id")) == question_id:
            item["status"] = normalized_status
            item["answer"] = answer_text
            item["updated_at"] = _now()
            break
    current["pending_items"] = items
    _save(cliente_id, current)
    return build_profile_draft(cliente_id)
