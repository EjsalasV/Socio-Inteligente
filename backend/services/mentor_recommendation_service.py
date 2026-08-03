from __future__ import annotations

import re
import unicodedata
from typing import Any

from backend.services.area_procedures_service import get_procedures_by_area
from backend.services.normative_catalog_service import list_normative_catalog


def _tokens(*values: Any) -> set[str]:
    text = " ".join(str(value or "") for value in values).lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return {token for token in re.findall(r"[a-z0-9]{3,}", text) if token not in {"para", "como", "esta", "este", "sobre", "cuenta"}}


def _score(candidate: dict[str, Any], query_tokens: set[str]) -> int:
    haystack = _tokens(
        candidate.get("descripcion"), candidate.get("afirmacion"), candidate.get("tipo"),
        candidate.get("titulo"), candidate.get("objetivo"), " ".join(candidate.get("tags", [])) if isinstance(candidate.get("tags"), list) else "",
    )
    return len(query_tokens & haystack)


def recommend_learning_resources(
    *,
    area_code: str,
    account_name: str,
    reasoning_gap: str,
    follow_up_question: str,
    learning_role: str,
) -> dict[str, list[dict[str, Any]]]:
    query_tokens = _tokens(account_name, reasoning_gap, follow_up_question)
    area = get_procedures_by_area(area_code)
    procedures = [item for item in area.get("procedimientos", []) if isinstance(item, dict) and item.get("id")]
    ranked_procedures = sorted(procedures, key=lambda item: (_score(item, query_tokens), bool(item.get("obligatorio"))), reverse=True)[:3]
    procedure_rows = [
        {
            "id": item["id"],
            "title": item.get("descripcion") or item["id"],
            "nia_ref": item.get("nia_ref") or "NIA 500",
            "assertion": item.get("afirmacion") or "",
            "why": f"Ayuda a convertir la brecha identificada en evidencia sobre {item.get('afirmacion') or 'la cuenta'}.",
            "href": f"/procedimientos?area={area_code}&procedure={item['id']}",
            "source": "catalogo_procedimientos",
        }
        for item in ranked_procedures
    ]

    preferred_codes = {str(row.get("nia_ref") or "").upper().replace(" ", "-") for row in procedure_rows}
    catalog = list_normative_catalog()
    ranked_norms = sorted(
        [item for item in catalog if isinstance(item, dict) and item.get("codigo")],
        key=lambda item: (str(item.get("codigo")) in preferred_codes, _score(item, query_tokens)),
        reverse=True,
    )
    normative_rows: list[dict[str, Any]] = []
    for item in ranked_norms:
        code = str(item.get("codigo"))
        relevance = _score(item, query_tokens)
        if code not in preferred_codes and relevance == 0 and normative_rows:
            continue
        normative_rows.append(
            {
                "code": code,
                "title": item.get("titulo") or code,
                "category": item.get("categoria") or "NIA",
                "why": (item.get("vista") or {}).get(learning_role) if isinstance(item.get("vista"), dict) else item.get("objetivo"),
                "href": f"/biblioteca?norma={code}",
                "source": "catalogo_normativo",
            }
        )
        if len(normative_rows) >= 3:
            break
    return {"procedures": procedure_rows, "norms": normative_rows}
