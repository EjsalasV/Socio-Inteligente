from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "data" / "conocimiento_normativo" / "supercias" / "matriz_versiones_ecuador.yaml"
MATRIX_REVIEW_PATH = (
    ROOT / "data" / "conocimiento_normativo" / "supercias" / "matriz_versiones_ecuador_revision.yaml"
)


def load_version_matrix() -> dict[str, Any]:
    value = yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8")) or {}
    return value if isinstance(value, dict) else {}


def evaluate_matrix_review(
    matrix_path: Path = MATRIX_PATH,
    review_path: Path = MATRIX_REVIEW_PATH,
) -> dict[str, Any]:
    """Validate that a professional review refers to the exact matrix bytes in use."""
    if not matrix_path.exists() or not review_path.exists():
        return {"status": "missing", "approved": False, "issues": ["review_record_missing"]}

    raw_review = yaml.safe_load(review_path.read_text(encoding="utf-8")) or {}
    review = raw_review if isinstance(raw_review, dict) else {}
    actual_hash = hashlib.sha256(matrix_path.read_bytes()).hexdigest()
    declared_hash = str(review.get("matrix_sha256") or "").strip().lower()
    status = _normalized(review.get("status")).replace(" ", "_") or "pending"
    issues: list[str] = []
    if declared_hash != actual_hash:
        issues.append("matrix_hash_mismatch")
    if status == "approved":
        required = ("reviewer_name", "reviewer_role", "review_date", "scope", "conclusion", "evidence_reference")
        issues.extend(f"missing_{field}" for field in required if not str(review.get(field) or "").strip())
        review_date = str(review.get("review_date") or "").strip()
        if review_date and _period_start(review_date) is None:
            issues.append("invalid_review_date")

    approved = status == "approved" and not issues
    return {
        "status": status,
        "approved": approved,
        "issues": list(dict.fromkeys(issues)),
        "matrix_sha256": actual_hash,
        "reviewer_name": str(review.get("reviewer_name") or "").strip(),
        "review_date": str(review.get("review_date") or "").strip(),
    }


def _normalized(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
    return "".join(char for char in text if not unicodedata.combining(char))


def _framework(value: Any) -> str:
    text = _normalized(value).replace("_", " ")
    if "pyme" in text or "sme" in text:
        return "ifrs_smes"
    if "nia" in text or "isa" in text:
        return "isa"
    if "niif" in text or "ifrs" in text:
        return "full_ifrs"
    return ""


def _period_start(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    if re.fullmatch(r"\d{4}", text):
        text = f"{text}-01-01"
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _evidence_set(values: Iterable[str]) -> set[str]:
    return {_normalized(value).replace(" ", "_") for value in values if str(value or "").strip()}


def _base_result(framework: str, period: date) -> dict[str, Any]:
    return {
        "status": "applicable",
        "framework": framework,
        "period_start": period.isoformat(),
        "edition": "",
        "effective_from": "",
        "early_adoption": False,
        "citation_allowed": False,
        "human_review_required": True,
        "questions": [],
        "missing_evidence": [],
        "basis": [],
    }


def resolve_normative_version(
    *,
    framework: str,
    period_start: str | int,
    standard: str = "",
    regulator: str = "",
    early_adoption: bool = False,
    evidence: Iterable[str] = (),
) -> dict[str, Any]:
    normalized_framework = _framework(framework)
    period = _period_start(period_start)
    normalized_regulator = _normalized(regulator).replace(" ", "_")
    if not normalized_framework or period is None:
        questions = []
        if not normalized_framework:
            questions.append("Confirmar marco contable o norma de auditoria.")
        if period is None:
            questions.append("Confirmar fecha de inicio del periodo.")
        return {
            "status": "blocked_missing_context",
            "framework": normalized_framework,
            "period_start": str(period_start or ""),
            "edition": "",
            "citation_allowed": False,
            "human_review_required": True,
            "questions": questions,
            "missing_evidence": [],
            "basis": [],
        }
    if normalized_regulator not in {"scvs_general", "scvs_general_inferred"}:
        return {
            **_base_result(normalized_framework, period),
            "status": "outside_scope",
            "questions": ["Confirmar regulador; la matriz actual cubre solo SCVS societario general."],
        }

    result = _base_result(normalized_framework, period)
    result["basis"] = ["SCVS adoption by reference", "issuer effective date"]
    supplied_evidence = _evidence_set(evidence)
    matrix_rules = load_version_matrix().get("rules", {})

    if normalized_framework == "ifrs_smes":
        sme_editions = matrix_rules.get("ifrs_smes", {}).get("editions", [])
        second_rule = next((row for row in sme_editions if row.get("edition") == "second_edition_2015"), {})
        third_rule = next((row for row in sme_editions if row.get("edition") == "third_edition_2025"), {})
        second_effective = _period_start(second_rule.get("effective_from")) or date(2017, 1, 1)
        third_effective = _period_start(third_rule.get("effective_from")) or date(2027, 1, 1)
        if period < second_effective:
            return {
                **result,
                "status": "historical_review_required",
                "questions": ["El periodo antecede la segunda edicion 2015; realizar revision historica separada."],
            }
        if period >= third_effective:
            result.update(
                edition="NIIF para las PYMES tercera edicion 2025",
                effective_from=third_effective.isoformat(),
            )
            return result
        if early_adoption:
            required = {"entity_election", "policy_disclosure"}
            missing = sorted(required - supplied_evidence)
            if missing:
                result.update(
                    status="blocked_early_adoption_evidence",
                    edition="NIIF para las PYMES tercera edicion 2025",
                    effective_from=third_effective.isoformat(),
                    early_adoption=True,
                    missing_evidence=missing,
                    questions=["Documentar eleccion de adopcion anticipada y revelacion en politicas/notas."],
                )
                return result
            result.update(
                status="conditional_early_adoption",
                edition="NIIF para las PYMES tercera edicion 2025",
                effective_from=third_effective.isoformat(),
                early_adoption=True,
            )
            return result
        result.update(
            edition="NIIF para las PYMES segunda edicion 2015",
            effective_from=second_effective.isoformat(),
        )
        return result

    if normalized_framework == "full_ifrs":
        result.update(
            edition="NIIF emitidas por IASB y vigentes para el inicio del periodo",
            effective_from=period.isoformat(),
        )
        if early_adoption:
            required = {"entity_election", "policy_disclosure", "issuer_allows_early_adoption"}
            missing = sorted(required - supplied_evidence)
            result.update(early_adoption=True, missing_evidence=missing)
            if missing:
                result.update(
                    status="blocked_early_adoption_evidence",
                    questions=["Confirmar que la modificacion permite adopcion anticipada y documentar la eleccion."],
                )
            else:
                result["status"] = "conditional_early_adoption"
        return result

    standard_key = _normalized(standard).replace(" ", "_")
    result["effective_from"] = period.isoformat()
    isa_rules = matrix_rules.get("isa", {}).get("pilot_standards", {})
    if "240" in standard_key:
        nia_240_effective = _period_start(isa_rules.get("NIA_240", {}).get("revised_effective_from")) or date(2026, 12, 15)
        if period >= nia_240_effective:
            result.update(edition="NIA 240 Revisada 2025", effective_from=nia_240_effective.isoformat())
            return result
        if early_adoption:
            required = {"engagement_adoption_decision", "jurisdiction_assessment"}
            missing = sorted(required - supplied_evidence)
            result.update(
                edition="NIA 240 Revisada 2025",
                effective_from=nia_240_effective.isoformat(),
                early_adoption=True,
                missing_evidence=missing,
            )
            if missing:
                result.update(
                    status="blocked_early_adoption_evidence",
                    questions=["Documentar decision del encargo y evaluacion jurisdiccional para adopcion anticipada."],
                )
            else:
                result["status"] = "conditional_early_adoption"
            return result
        result["edition"] = "NIA 240 anterior a la revision de 2025"
        return result
    if "315" in standard_key:
        nia_315_effective = _period_start(isa_rules.get("NIA_315", {}).get("effective_from")) or date(2021, 12, 15)
        result.update(edition="NIA 315 Revisada 2019", effective_from=nia_315_effective.isoformat())
        return result
    if "330" in standard_key:
        result["edition"] = "NIA 330 clarificada vigente; propuesta 2026 no aplicable"
        return result
    if "500" in standard_key:
        result["edition"] = "NIA 500 clarificada vigente; propuesta 2026 no aplicable"
        return result
    result["edition"] = "NIA emitidas por IAASB y vigentes para el inicio del periodo"
    return result


def build_profile_version_context(profile: dict[str, Any]) -> str:
    cliente = profile.get("cliente") if isinstance(profile.get("cliente"), dict) else {}
    encargo = profile.get("encargo") if isinstance(profile.get("encargo"), dict) else {}
    questionnaire = profile.get("cuestionario_auditoria") if isinstance(profile.get("cuestionario_auditoria"), dict) else {}
    country = _normalized(cliente.get("pais"))
    explicit_regulator = str(encargo.get("regulador") or "").strip()
    if explicit_regulator:
        regulator = explicit_regulator
    elif country == "ecuador" and questionnaire.get("regulado") is False:
        regulator = "scvs_general_inferred"
    else:
        regulator = ""
    period = encargo.get("fecha_inicio_periodo") or encargo.get("anio_activo") or ""
    accounting = resolve_normative_version(
        framework=str(encargo.get("marco_referencial") or encargo.get("normativa_cliente") or ""),
        period_start=period,
        regulator=regulator,
    )
    audit = resolve_normative_version(
        framework=str(encargo.get("norma_auditoria") or "NIAs"),
        period_start=period,
        regulator=regulator,
    )
    matrix_review = evaluate_matrix_review()
    lines = [
        "[MATRIZ DE VERSIONES ECUADOR - METODOLOGIA, NO CITA]",
        f"Regulador: {regulator or 'no confirmado'}",
        f"Marco contable: {accounting.get('status')} | {accounting.get('edition') or 'sin resolver'}",
        f"Auditoria: {audit.get('status')} | {audit.get('edition') or 'sin resolver'}",
        f"Revision profesional de matriz: {matrix_review.get('status')} | aprobada: {'si' if matrix_review.get('approved') else 'no'}",
    ]
    questions = [*accounting.get("questions", []), *audit.get("questions", [])]
    if questions:
        lines.append("Preguntas obligatorias: " + " ".join(dict.fromkeys(str(item) for item in questions)))
    lines.append("La matriz no habilita citas y toda adopcion anticipada requiere evidencia documentada.")
    return "\n".join(lines)


def should_include_version_context(query: str) -> bool:
    text = _normalized(query)
    return bool(
        re.search(
            r"\b(nia|niif|ifrs|isa|norma|normativa|version|edicion|ingresos|cxc|cuentas por cobrar|auditoria)\b",
            text,
        )
    )
