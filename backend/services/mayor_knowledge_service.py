from __future__ import annotations

import logging
from typing import Any

from backend.services.knowledge_service import (
    knowledge_core_enabled,
    upsert_entity,
    upsert_relation,
)

LOGGER = logging.getLogger("socio_ai.mayor.knowledge")

VALIDATION_TYPES = [
    "asientos_descuadrados",
    "duplicados",
    "movimientos_sin_referencia",
    "montos_altos",
    "movimientos_cerca_cierre",
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _period_key(summary: dict[str, Any]) -> str:
    start = str(summary.get("fecha_min") or "").strip() or "na"
    end = str(summary.get("fecha_max") or "").strip() or "na"
    return f"{start}_{end}"


def _extract_accounts(validation_block: dict[str, Any], *, limit: int = 5) -> list[str]:
    items = validation_block.get("items")
    if not isinstance(items, list):
        return []
    seen: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        account = str(item.get("numero_cuenta") or "").strip()
        if not account:
            continue
        if account in seen:
            continue
        seen.append(account)
        if len(seen) >= max(1, limit):
            break
    return seen


def _extract_dates(validation_block: dict[str, Any], *, limit: int = 10) -> list[str]:
    items = validation_block.get("items")
    if not isinstance(items, list):
        return []
    seen: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        dt = str(item.get("fecha") or "").strip()
        if not dt or dt in seen:
            continue
        seen.append(dt)
        if len(seen) >= max(1, limit):
            break
    return seen


def _title_for(validation_type: str) -> str:
    titles = {
        "asientos_descuadrados": "Mayor: asientos descuadrados",
        "duplicados": "Mayor: movimientos duplicados",
        "movimientos_sin_referencia": "Mayor: movimientos sin referencia",
        "montos_altos": "Mayor: movimientos de monto alto",
        "movimientos_cerca_cierre": "Mayor: movimientos cerca del cierre",
    }
    return titles.get(validation_type, f"Mayor: {validation_type}")


def _metrics_for(validation_type: str, validation_block: dict[str, Any]) -> dict[str, Any]:
    if validation_type == "asientos_descuadrados":
        return {
            "count_asientos": _safe_int(validation_block.get("count_asientos")),
            "count_movimientos": _safe_int(validation_block.get("count_movimientos")),
            "max_descuadre_abs": _safe_float(
                max(
                    [_safe_float(x.get("descuadre_abs")) for x in validation_block.get("items", []) if isinstance(x, dict)]
                    or [0.0]
                )
            ),
        }
    if validation_type == "duplicados":
        return {
            "grupos": _safe_int(validation_block.get("grupos")),
            "movimientos": _safe_int(validation_block.get("movimientos")),
            "max_repeticiones": _safe_int(
                max(
                    [_safe_int(x.get("repeticiones")) for x in validation_block.get("items", []) if isinstance(x, dict)]
                    or [0]
                )
            ),
        }
    if validation_type == "movimientos_sin_referencia":
        return {
            "count": _safe_int(validation_block.get("count")),
        }
    if validation_type == "montos_altos":
        return {
            "count": _safe_int(validation_block.get("count")),
            "threshold": _safe_float(validation_block.get("threshold")),
            "max_monto_abs": _safe_float(
                max(
                    [_safe_float(x.get("monto_abs")) for x in validation_block.get("items", []) if isinstance(x, dict)]
                    or [0.0]
                )
            ),
        }
    if validation_type == "movimientos_cerca_cierre":
        return {
            "count": _safe_int(validation_block.get("count")),
            "fecha_cierre": str(validation_block.get("fecha_cierre") or ""),
            "dias": _safe_int(validation_block.get("dias"), default=5),
        }
    return {}


def _content_for(validation_type: str, validation_block: dict[str, Any], summary: dict[str, Any]) -> str:
    metrics = _metrics_for(validation_type, validation_block)
    metrics_txt = ", ".join([f"{k}={v}" for k, v in metrics.items()])
    period_txt = f"{summary.get('fecha_min') or 'na'} a {summary.get('fecha_max') or 'na'}"
    return (
        f"Resultado de validacion '{validation_type}' sobre el mayor contable. "
        f"Periodo: {period_txt}. Metricas: {metrics_txt}."
    )


def _upsert_client_entity(session: Any, cliente_id: str, actor: str) -> dict[str, Any]:
    return upsert_entity(
        session,
        {
            "cliente_id": cliente_id,
            "entity_type": "client",
            "title": f"Cliente {cliente_id}",
            "content": "Entidad cliente creada para enlazar hallazgos del mayor.",
            "status": "active",
            "source_module": "mayor",
            "source_id": f"cliente:{cliente_id}",
            "metadata": {"cliente_id": cliente_id},
            "tags": ["mayor", "cliente"],
        },
        actor=actor,
    )


def _upsert_period_entity(session: Any, cliente_id: str, period_key: str, summary: dict[str, Any], actor: str) -> dict[str, Any]:
    return upsert_entity(
        session,
        {
            "cliente_id": cliente_id,
            "entity_type": "note",
            "title": f"Periodo {summary.get('fecha_min') or 'na'} a {summary.get('fecha_max') or 'na'}",
            "content": "Periodo de analisis del mayor para validaciones.",
            "status": "active",
            "source_module": "mayor",
            "source_id": f"periodo:{period_key}",
            "metadata": {
                "fecha_min": str(summary.get("fecha_min") or ""),
                "fecha_max": str(summary.get("fecha_max") or ""),
            },
            "tags": ["mayor", "periodo"],
        },
        actor=actor,
    )


def _upsert_account_entity(session: Any, cliente_id: str, account: str, actor: str) -> dict[str, Any]:
    return upsert_entity(
        session,
        {
            "cliente_id": cliente_id,
            "entity_type": "trial_balance_account",
            "title": f"Cuenta {account}",
            "content": "Cuenta afectada por hallazgos de validacion del mayor.",
            "status": "active",
            "source_module": "mayor",
            "source_id": f"cuenta:{account}",
            "metadata": {"numero_cuenta": account},
            "tags": ["mayor", "cuenta"],
        },
        actor=actor,
    )


def sync_mayor_validations_to_knowledge(
    session: Any,
    *,
    cliente_id: str,
    validations: dict[str, Any],
    summary: dict[str, Any],
    actor: str = "",
) -> dict[str, Any]:
    if not knowledge_core_enabled():
        return {"enabled": False, "created_or_updated": 0, "relations_created_or_updated": 0}

    if not isinstance(validations, dict):
        return {"enabled": True, "created_or_updated": 0, "relations_created_or_updated": 0}

    period_key = _period_key(summary)
    created_or_updated = 0
    relations_created_or_updated = 0

    client_entity = _upsert_client_entity(session, cliente_id, actor)
    period_entity = _upsert_period_entity(session, cliente_id, period_key, summary, actor)

    for validation_type in VALIDATION_TYPES:
        block = validations.get(validation_type)
        if not isinstance(block, dict):
            continue

        metrics = _metrics_for(validation_type, block)
        affected_accounts = _extract_accounts(block, limit=5)
        affected_dates = _extract_dates(block, limit=10)

        source_id = f"{cliente_id}:{period_key}:{validation_type}:summary:v1"
        finding = upsert_entity(
            session,
            {
                "cliente_id": cliente_id,
                "entity_type": "finding",
                "title": _title_for(validation_type),
                "content": _content_for(validation_type, block, summary),
                "status": "active",
                "source_module": "mayor",
                "source_id": source_id,
                "source_ref": period_key,
                "metadata": {
                    "validation_type": validation_type,
                    "periodo": {
                        "fecha_min": str(summary.get("fecha_min") or ""),
                        "fecha_max": str(summary.get("fecha_max") or ""),
                        "period_key": period_key,
                    },
                    "metrics": metrics,
                    "cuentas_afectadas": affected_accounts,
                    "fechas_afectadas": affected_dates,
                },
                "tags": ["mayor", "validacion", validation_type],
                "confidence": 0.85,
            },
            actor=actor,
        )
        created_or_updated += 1

        upsert_relation(
            session,
            {
                "cliente_id": cliente_id,
                "relation_type": "belongs_to",
                "from_entity_id": int(finding["id"]),
                "to_entity_id": int(client_entity["id"]),
                "weight": 1.0,
                "metadata": {"role": "cliente"},
                "source_module": "mayor",
                "source_id": f"{source_id}:rel:cliente",
            },
            actor=actor,
        )
        relations_created_or_updated += 1

        upsert_relation(
            session,
            {
                "cliente_id": cliente_id,
                "relation_type": "belongs_to",
                "from_entity_id": int(finding["id"]),
                "to_entity_id": int(period_entity["id"]),
                "weight": 1.0,
                "metadata": {"role": "periodo"},
                "source_module": "mayor",
                "source_id": f"{source_id}:rel:periodo",
            },
            actor=actor,
        )
        relations_created_or_updated += 1

        for account in affected_accounts:
            account_entity = _upsert_account_entity(session, cliente_id, account, actor)
            upsert_relation(
                session,
                {
                    "cliente_id": cliente_id,
                    "relation_type": "impacts",
                    "from_entity_id": int(finding["id"]),
                    "to_entity_id": int(account_entity["id"]),
                    "weight": 0.7,
                    "metadata": {"numero_cuenta": account},
                    "source_module": "mayor",
                    "source_id": f"{source_id}:rel:cuenta:{account}",
                },
                actor=actor,
            )
            relations_created_or_updated += 1

    return {
        "enabled": True,
        "created_or_updated": created_or_updated,
        "relations_created_or_updated": relations_created_or_updated,
    }


def safe_sync_mayor_validations_to_knowledge(
    session: Any,
    *,
    cliente_id: str,
    validations: dict[str, Any],
    summary: dict[str, Any],
    actor: str = "",
) -> dict[str, Any]:
    try:
        return sync_mayor_validations_to_knowledge(
            session,
            cliente_id=cliente_id,
            validations=validations,
            summary=summary,
            actor=actor,
        )
    except Exception as exc:  # pragma: no cover - non-blocking integration
        LOGGER.warning(
            "Knowledge sync skipped for mayor validations (cliente_id=%s): %s",
            cliente_id,
            exc,
        )
        return {"enabled": knowledge_core_enabled(), "created_or_updated": 0, "relations_created_or_updated": 0}
