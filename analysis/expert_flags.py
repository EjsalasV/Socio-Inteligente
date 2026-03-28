"""Motor de banderas expertas (rule-based) para ranking y workspace por area."""

from __future__ import annotations

from typing import Any


def _txt(v: Any) -> str:
    return str(v or "").strip().lower()


def _to_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def _perfil_cliente(perfil: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(perfil, dict):
        return {}
    if isinstance(perfil.get("cliente"), dict):
        return perfil.get("cliente", {})
    return perfil


def _perfil_contexto(perfil: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(perfil, dict):
        return {}
    return perfil.get("contexto_negocio", {}) if isinstance(perfil.get("contexto_negocio"), dict) else {}


def _has_related_party_signal(perfil: dict[str, Any]) -> bool:
    ctx = _perfil_contexto(perfil)
    direct = [
        _txt(ctx.get("tiene_partes_relacionadas")),
        _txt(perfil.get("tiene_partes_relacionadas")),
        _txt(perfil.get("partes_relacionadas")),
        _txt(perfil.get("banderas_generales", {}).get("partes_relacionadas") if isinstance(perfil.get("banderas_generales"), dict) else ""),
    ]
    if any(x in {"true", "si", "sí", "1", "yes"} for x in direct):
        return True

    blob = " ".join(
        [
            _txt(perfil),
            _txt(ctx),
            _txt(perfil.get("notas_generales", {})),
        ]
    )
    return "parte" in blob and "relacion" in blob


def _mk_flag(codigo_area: str, nivel: str, titulo: str, mensaje: str, impacto: str) -> dict[str, str]:
    return {
        "codigo_area": str(codigo_area),
        "nivel": nivel,
        "titulo": titulo,
        "mensaje": mensaje,
        "impacto": impacto,
    }


def detectar_expert_flags(
    codigo_area: str,
    perfil: dict[str, Any] | None = None,
    metricas_area: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Devuelve banderas expertas para un area segun reglas de negocio simples."""
    perfil = perfil or {}
    metricas = metricas_area or {}
    codigo = str(codigo_area).strip()

    cliente_info = _perfil_cliente(perfil)
    sector = _txt(cliente_info.get("sector") or perfil.get("sector"))
    tipo_entidad = _txt(cliente_info.get("tipo_entidad") or perfil.get("tipo_entidad"))

    saldo = abs(_to_float(metricas.get("saldo_total", 0)))
    pct_total = _to_float(metricas.get("pct_total", 0))
    var_abs = abs(_to_float(metricas.get("variacion_abs_total", metricas.get("variacion_acumulada", 0))))
    materialidad_relativa = _to_float(metricas.get("materialidad_relativa", 0))

    flags: list[dict[str, str]] = []

    # 1) ESFL + patrimonio con movimiento relevante
    es_esfl = "esfl" in sector or "esfl" in tipo_entidad
    if es_esfl and codigo == "200" and (var_abs > 0 or materialidad_relativa >= 25 or pct_total >= 10):
        flags.append(
            _mk_flag(
                codigo,
                "alto",
                "Movimiento patrimonial inusual",
                "Entidad ESFL con cambios relevantes en patrimonio que requieren soporte de sustancia economica.",
                "requiere revision de sustancia economica",
            )
        )

    # 2) cooperativa + cartera/provision debil
    es_coop = "cooper" in sector or "cooper" in tipo_entidad
    if es_coop and codigo in {"130", "131", "132"} and (pct_total >= 8 or materialidad_relativa >= 20):
        flags.append(
            _mk_flag(
                codigo,
                "alto",
                "Cartera y provision con riesgo sectorial",
                "En cooperativas, la cartera/provision exige validacion reforzada de calidad, recuperabilidad y cobertura.",
                "priorizar pruebas de deterioro y recuperacion",
            )
        )

    # 3) funeraria + deterioro/propiedad de inversion
    es_funeraria = "funer" in sector or "funer" in tipo_entidad
    if es_funeraria and codigo in {"170", "171", "145"} and (pct_total >= 6 or materialidad_relativa >= 15):
        flags.append(
            _mk_flag(
                codigo,
                "medio",
                "Deterioro / propiedad de inversion sensible",
                "En funerarias, activos de larga duracion y propiedades de inversion requieren juicio tecnico sobre deterioro y valuacion.",
                "requiere pruebas de valuacion y deterioro",
            )
        )

    # 4) impuestos activos significativos
    if codigo in {"145", "136", "1900"} and (pct_total >= 5 or materialidad_relativa >= 20 or saldo >= 50000):
        flags.append(
            _mk_flag(
                codigo,
                "medio",
                "Impuestos activos significativos",
                "El saldo tributario activo luce significativo y requiere analisis de recuperabilidad y soporte fiscal.",
                "riesgo de sobrevaloracion por recuperabilidad",
            )
        )

    # 5) indicios de partes relacionadas
    if _has_related_party_signal(perfil) and codigo in {"200", "130", "140", "170", "425", "14"}:
        flags.append(
            _mk_flag(
                codigo,
                "alto",
                "Indicadores de partes relacionadas",
                "Se observan indicios de partes relacionadas; revisar condiciones, revelaciones y sustancia economica.",
                "riesgo de revelacion y medicion",
            )
        )

    return flags
