from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from backend.models.client import Client
from backend.models.cliente_configuration import ClienteConfiguration
from backend.utils.database import SessionLocal


def _txt(value: Any) -> str:
    return str(value or "").strip().lower()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if isinstance(value, str):
            cleaned = value.replace("%", "").replace(",", ".").strip()
            return float(cleaned)
        return float(value)
    except Exception:
        return default


def _is_yes(value: Any) -> bool:
    raw = _txt(value).replace("í", "i")
    return raw in {"si", "true", "1", "yes", "y", "on"}


def _build_signature_payload(cliente: Client | None, config: ClienteConfiguration | None) -> dict[str, Any]:
    respuestas = config.respuestas if config and isinstance(config.respuestas, dict) else {}
    return {
        "client_id": getattr(cliente, "client_id", ""),
        "tipo_entidad": getattr(cliente, "tipo_entidad", None),
        "tamano": getattr(cliente, "tamano", None),
        "normativa": getattr(cliente, "normativa", None),
        "sector": getattr(cliente, "sector", None),
        "cliente_updated_at": getattr(getattr(cliente, "updated_at", None), "isoformat", lambda: "")(),
        "config_updated_at": getattr(getattr(config, "updated_at", None), "isoformat", lambda: "")(),
        "respuestas": respuestas,
    }


def get_cliente_configuration_signature(cliente_id: str, session: Session | None = None) -> str:
    owns_session = session is None
    db = session or SessionLocal()
    try:
        cliente = db.query(Client).filter(Client.client_id == cliente_id).first()
        if not cliente:
            return "missing"
        config = (
            db.query(ClienteConfiguration)
            .filter(ClienteConfiguration.client_id == cliente.id)
            .order_by(ClienteConfiguration.updated_at.desc())
            .first()
        )
        payload = _build_signature_payload(cliente, config)
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    finally:
        if owns_session:
            db.close()


def _matches_area(area_id: str, area_name: str, *, codes: set[str] | None = None, prefixes: tuple[str, ...] = (), keywords: tuple[str, ...] = ()) -> bool:
    code = str(area_id or "").strip()
    name = _txt(area_name)
    if codes and code in codes:
        return True
    if prefixes and any(code.startswith(prefix) for prefix in prefixes):
        return True
    return any(keyword in name for keyword in keywords)


def _is_receivables_area(area_id: str, area_name: str) -> bool:
    return _matches_area(
        area_id,
        area_name,
        codes={"130", "131", "132", "133", "134", "135", "136", "137", "138", "139"},
        keywords=("cartera", "cuentas por cobrar", "clientes", "deudores", "prestamos", "provision"),
    )


def _is_inventory_area(area_id: str, area_name: str) -> bool:
    return _matches_area(
        area_id,
        area_name,
        prefixes=("15",),
        keywords=("inventario", "mercader", "materia prima", "producto terminado", "wip", "obsolesc"),
    )


def _is_cash_area(area_id: str, area_name: str) -> bool:
    return _matches_area(
        area_id,
        area_name,
        prefixes=("10", "11"),
        keywords=("efectivo", "equivalentes", "caja", "banco", "liquidez"),
    )


def _is_investment_area(area_id: str, area_name: str) -> bool:
    return _matches_area(
        area_id,
        area_name,
        prefixes=("14", "17"),
        keywords=("inversion", "subsidi", "asociad", "propiedad de inversion", "endowment"),
    )


def _is_equity_area(area_id: str, area_name: str) -> bool:
    return _matches_area(area_id, area_name, codes={"200"}, keywords=("patrimonio", "capital", "reserv", "resultados acumulados"))


def _is_revenue_area(area_id: str, area_name: str) -> bool:
    return _matches_area(
        area_id,
        area_name,
        prefixes=("4",),
        keywords=("ingres", "ventas", "factur", "honorarios", "matricul", "pensiones", "servicios"),
    )


def _is_cost_area(area_id: str, area_name: str) -> bool:
    return _matches_area(area_id, area_name, prefixes=("5", "6"), keywords=("costo", "produccion", "manufactura"))


def _is_ppe_area(area_id: str, area_name: str) -> bool:
    return _matches_area(
        area_id,
        area_name,
        prefixes=("16", "17"),
        keywords=("propiedad planta", "equipo", "construccion", "obra en curso", "capex"),
    )


def _is_liability_area(area_id: str, area_name: str) -> bool:
    return _matches_area(
        area_id,
        area_name,
        prefixes=("21", "22", "23", "24", "25", "26", "27", "28", "29"),
        keywords=("pasivo", "obligacion", "provision", "anticipo", "ingreso diferido", "cuentas por pagar"),
    )


def _finalize(components: dict[str, float], drivers: list[str], cap_total: float = 18.0) -> dict[str, Any]:
    normalized = {k: round(max(0.0, float(v)), 2) for k, v in components.items() if float(v) > 0}
    boost = round(min(cap_total, sum(normalized.values())), 2)
    return {
        "boost": boost,
        "drivers": drivers[:3],
        "components": normalized,
    }


def build_industry_risk_signal(snapshot: dict[str, Any] | None, area_id: str, area_name: str, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    if not snapshot:
        return {"boost": 0.0, "drivers": [], "components": {}}

    tipo = str(snapshot.get("tipo_entidad") or "").strip().upper()
    respuestas = snapshot.get("respuestas") if isinstance(snapshot.get("respuestas"), dict) else {}
    metrics = metrics or {}
    pct_total = _to_float(metrics.get("pct_total"), 0.0)
    materialidad_relativa = _to_float(metrics.get("materialidad_relativa"), 0.0)

    components: dict[str, float] = {}
    drivers: list[str] = []

    if tipo == "BANCO":
        dias_vencimiento = _to_float(respuestas.get("rango_vencimiento"), 30.0)
        provisiones = [_to_float(part, 0.0) for part in str(respuestas.get("provisiones_pct") or "").split(",") if str(part).strip()]
        provision_promedio = sum(provisiones) / len(provisiones) if provisiones else 0.0

        if _is_receivables_area(area_id, area_name):
            if dias_vencimiento <= 30:
                components["industry_overdue_policy"] = 4.0
                drivers.append(f"Politica de cartera exigente ({int(dias_vencimiento)} dias)")
            if provisiones and provision_promedio < 5:
                components["industry_provision_pressure"] = 4.0
                drivers.append(f"Cobertura de provision conservadora ({provision_promedio:.1f}% promedio)")
        if _is_cash_area(area_id, area_name) and _is_yes(respuestas.get("tiene_obligaciones_publico")):
            components["industry_liquidity_exposure"] = 3.0
            drivers.append("Obligaciones con el publico elevan la sensibilidad de liquidez")

    elif tipo == "RETAIL":
        inv_pct_esperado = _to_float(respuestas.get("inventario_pct_activos"), 50.0)
        rotacion_dias = _to_float(respuestas.get("rotacion_inventario_dias"), 60.0)

        if _is_inventory_area(area_id, area_name):
            diff = abs(pct_total - inv_pct_esperado)
            if diff >= 12:
                components["industry_inventory_mix"] = min(8.0, round(diff / 4.0, 2))
                drivers.append(f"Inventario fuera del mix esperado ({pct_total:.1f}% vs {inv_pct_esperado:.1f}%)")
            if rotacion_dias >= 75:
                components["industry_inventory_rotation"] = 4.0
                drivers.append(f"Ciclo de inventario largo esperado ({rotacion_dias:.0f} dias)")
            if _is_yes(respuestas.get("tiene_consignaciones")):
                components["industry_cutoff_consignment"] = 3.0
                drivers.append("Inventario en consignacion requiere corte reforzado")
        if _is_receivables_area(area_id, area_name) and _to_float(respuestas.get("rango_vencimiento_cxc"), 60.0) >= 60:
            components["industry_retail_collections"] = 2.0
            drivers.append("Cobranzas retail con ventana amplia de vencimiento")

    elif tipo == "SERVICIOS":
        if _is_yes(respuestas.get("usa_proyectos")) and (_is_revenue_area(area_id, area_name) or _is_receivables_area(area_id, area_name)):
            if materialidad_relativa >= 15 or pct_total >= 5:
                components["industry_project_accounting"] = 4.0
                drivers.append("Contabilidad por proyectos exige pruebas por contrato")
        if _is_yes(respuestas.get("tiene_anticipos_clientes")) and (_is_revenue_area(area_id, area_name) or _is_liability_area(area_id, area_name)):
            components["industry_customer_advances"] = 3.0
            drivers.append("Anticipos de clientes aumentan riesgo de reconocimiento")
        if _is_yes(respuestas.get("tiene_servicios_garantia")) and _is_liability_area(area_id, area_name):
            components["industry_service_warranty"] = 3.0
            drivers.append("Servicios con garantia requieren provisiones tecnicas")

    elif tipo == "MANUFACTURA":
        if _is_inventory_area(area_id, area_name) or _is_cost_area(area_id, area_name):
            if _is_yes(respuestas.get("tiene_wip")):
                components["industry_wip_exposure"] = 6.0
                drivers.append("WIP declarado: revisar acumulacion y valuacion")
            pct_wip = _to_float(respuestas.get("pct_wip_normal"), 15.0)
            if pct_wip >= 15:
                components["industry_wip_baseline"] = 2.0
                drivers.append(f"Umbral WIP relevante ({pct_wip:.0f}% normal)")
            if _txt(respuestas.get("usa_costos_estandar")) == "estandar":
                components["industry_standard_costs"] = 3.0
                drivers.append("Costo estandar requiere revision de variaciones")
        if _is_ppe_area(area_id, area_name) and _is_yes(respuestas.get("tiene_bienes_construccion")):
            components["industry_capex_pipeline"] = 4.0
            drivers.append("Bienes en construccion requieren capitalizacion y corte")

    elif tipo == "HOLDING":
        pct_relacionadas = _to_float(respuestas.get("pct_transacciones_relacionadas"), 10.0)
        target_related = _is_investment_area(area_id, area_name) or _is_equity_area(area_id, area_name) or _is_receivables_area(area_id, area_name) or _is_liability_area(area_id, area_name)
        if target_related and pct_relacionadas >= 10:
            components["industry_related_parties"] = min(8.0, round(pct_relacionadas / 5.0, 2))
            drivers.append(f"Relacionadas relevantes ({pct_relacionadas:.0f}% de transacciones)")
        if (_is_investment_area(area_id, area_name) or _is_equity_area(area_id, area_name)) and _is_yes(respuestas.get("tiene_cambios_control")):
            components["industry_control_changes"] = 5.0
            drivers.append("Cambios de control elevan riesgo de consolidacion")
        garantia_pasivos = _txt(respuestas.get("tiene_garantias_pasivos")).replace("í", "i")
        if (_is_liability_area(area_id, area_name) or _is_equity_area(area_id, area_name)) and garantia_pasivos in {"si", "parcialmente"}:
            components["industry_group_guarantees"] = 4.0
            drivers.append("Garantias de grupo exigen revision de contingencias")

    elif tipo == "SALUD":
        pct_seguros = _to_float(respuestas.get("pct_seguros_vs_pacientes"), 70.0)
        if (_is_receivables_area(area_id, area_name) or _is_revenue_area(area_id, area_name)) and pct_seguros >= 60:
            components["industry_insurer_exposure"] = 5.0
            drivers.append(f"Alta dependencia de seguros ({pct_seguros:.0f}% ingresos)")
        if _is_inventory_area(area_id, area_name) and _is_yes(respuestas.get("tiene_medicinas_vencidas")):
            components["industry_medicine_obsolescence"] = 4.0
            drivers.append("Rotacion lenta de medicinas incrementa obsolescencia")
        if _is_receivables_area(area_id, area_name) and _to_float(respuestas.get("rango_vencimiento_cxc"), 60.0) >= 90:
            components["industry_long_collections"] = 2.0
            drivers.append("Plazo largo de cobranza medica esperado")

    elif tipo == "EDUCACION":
        meses_vencimiento = _to_float(respuestas.get("rango_vencimiento_pensiones"), 3.0)
        pct_becas = _to_float(respuestas.get("pct_becas"), 20.0)

        if _is_receivables_area(area_id, area_name):
            if meses_vencimiento >= 3:
                components["industry_student_ar_window"] = 4.0
                drivers.append(f"Cartera estudiantil con ventana amplia ({meses_vencimiento:.0f} meses)")
            if pct_becas >= 20:
                components["industry_scholarship_pressure"] = min(6.0, round(pct_becas / 10.0, 2))
                drivers.append(f"Carga de becas relevante ({pct_becas:.0f}% estudiantes)")
        if (_is_investment_area(area_id, area_name) or _is_equity_area(area_id, area_name)) and _is_yes(respuestas.get("tiene_endowment")):
            components["industry_endowment"] = 4.0
            drivers.append("Fondo patrimonial requiere valuacion y restricciones")
        if (_is_revenue_area(area_id, area_name) or _is_liability_area(area_id, area_name)) and _is_yes(respuestas.get("tiene_investigacion")):
            components["industry_research_revenue"] = 3.0
            drivers.append("Ingresos de investigacion requieren diferimiento y soporte")

    return _finalize(components, drivers)


def summarize_risk_areas_for_ai(areas: list[Any], *, top_n: int = 5) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for area in (areas or [])[:top_n]:
        area_id = str(getattr(area, "area_id", "") or "")
        area_name = str(getattr(area, "area_nombre", "") or area_id)
        score = _to_float(getattr(area, "score", 0.0), 0.0)
        nivel = str(getattr(area, "nivel", "") or "BAJO")
        drivers = getattr(area, "drivers", []) or []
        if not isinstance(drivers, list):
            drivers = []
        components = getattr(area, "score_components", {}) or {}
        if not isinstance(components, dict):
            components = {}
        industry_boost = _to_float(components.get("industry_boost"), 0.0)
        mayor_boost = _to_float(components.get("mayor_boost"), 0.0)
        top_components = [
            {"key": str(key), "value": _to_float(value, 0.0)}
            for key, value in sorted(
                (
                    (k, v)
                    for k, v in components.items()
                    if k not in {"base_model", "industry_boost", "mayor_boost"} and _to_float(v, 0.0) > 0
                ),
                key=lambda item: _to_float(item[1], 0.0),
                reverse=True,
            )[:3]
        ]
        summaries.append(
            {
                "area_id": area_id,
                "area_nombre": area_name,
                "score": round(score, 2),
                "nivel": nivel,
                "industry_boost": round(industry_boost, 2),
                "mayor_boost": round(mayor_boost, 2),
                "drivers": [str(driver) for driver in drivers[:3] if str(driver).strip()],
                "top_components": top_components,
            }
        )
    return summaries
