from __future__ import annotations

from pathlib import Path
from typing import Any


def _txt(value: Any, default: str = "No disponible") -> str:
    text = str(value).strip() if value is not None else ""
    return text if text else default


def _to_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _fmt_flags(flags: list[dict[str, Any]]) -> str:
    if not flags:
        return "- Sin señales expertas relevantes."
    lines: list[str] = []
    for f in flags:
        nivel = _txt(f.get("nivel", "medio"), "medio").upper()
        titulo = _txt(f.get("titulo", "Señal experta"), "Señal experta")
        mensaje = _txt(f.get("mensaje", ""), "")
        impacto = _txt(f.get("impacto", ""), "")
        detail = f"[{nivel}] {titulo}"
        if mensaje:
            detail += f": {mensaje}"
        if impacto:
            detail += f" (Impacto: {impacto})"
        lines.append(f"- {detail}")
    return "\n".join(lines)


def _fmt_riesgos(riesgos: list[Any]) -> str:
    if not riesgos:
        return "- Sin riesgos automáticos detectados."
    lines: list[str] = []
    for r in riesgos:
        if isinstance(r, dict):
            nivel = _txt(r.get("nivel", "N/A"), "N/A").upper()
            titulo = _txt(r.get("titulo", "Riesgo"), "Riesgo")
            descripcion = _txt(r.get("descripcion", ""), "")
            line = f"- [{nivel}] {titulo}"
            if descripcion:
                line += f": {descripcion}"
            lines.append(line)
        else:
            lines.append(f"- {_txt(r, 'Riesgo')}")
    return "\n".join(lines)


def _fmt_simple_list(items: list[Any], empty_msg: str) -> str:
    values = [str(x).strip() for x in _to_list(items) if str(x).strip()]
    if not values:
        return f"- {empty_msg}"
    return "\n".join([f"- {v}" for v in values])


def _fmt_cobertura(cobertura: dict[str, Any]) -> str:
    if not isinstance(cobertura, dict):
        cobertura = {}
    pct = cobertura.get("cobertura_porcentaje", 0)
    conclusion = _txt(cobertura.get("conclusion", "sin_mapeo"), "sin_mapeo")
    esperadas = _fmt_simple_list(cobertura.get("esperadas", []), "Sin aseveraciones esperadas.")
    cubiertas = _fmt_simple_list(cobertura.get("cubiertas", []), "Sin aseveraciones cubiertas.")
    debiles = _fmt_simple_list(cobertura.get("debiles", []), "Sin aseveraciones débiles.")
    no_cubiertas = _fmt_simple_list(cobertura.get("no_cubiertas", []), "Sin aseveraciones no cubiertas.")

    return (
        f"- Cobertura actual: {pct:.1f}%\n"
        f"- Conclusión: {conclusion}\n"
        f"- Aseveraciones esperadas:\n{esperadas}\n"
        f"- Aseveraciones cubiertas:\n{cubiertas}\n"
        f"- Aseveraciones débiles:\n{debiles}\n"
        f"- Aseveraciones no cubiertas:\n{no_cubiertas}"
    )


def build_area_resumen_markdown(payload: dict[str, Any]) -> str:
    cliente = _txt(payload.get("cliente"))
    periodo = _txt(payload.get("periodo"))
    area = _txt(payload.get("area_nombre"))
    codigo_ls = _txt(payload.get("codigo_ls"))
    etapa = _txt(payload.get("etapa"))
    estado_area = _txt(payload.get("estado_area"), "no_iniciada")
    riesgo = _txt(payload.get("riesgo"))
    score = payload.get("score_riesgo", "No disponible")
    prioridad = _txt(payload.get("prioridad"), "media")
    mat_rel = payload.get("materialidad_relativa", 0.0)
    objetivo = _txt(payload.get("objetivo_area"))
    concl_pre = _txt(payload.get("conclusion_preliminar"), "No definida")
    decision = _txt(payload.get("decision_cierre"), "requiere_revision")
    recomendacion = _txt(payload.get("recomendacion_final"), "Revisar evidencia pendiente antes de concluir.")

    riesgos_md = _fmt_riesgos(_to_list(payload.get("riesgos_area", [])))
    pendientes_md = _fmt_simple_list(payload.get("procedimientos_pendientes", []), "Sin procedimientos pendientes.")
    hallazgos_md = _fmt_simple_list(payload.get("hallazgos_abiertos", []), "Sin hallazgos abiertos.")
    flags_md = _fmt_flags(_to_list(payload.get("senales_expertas", [])))
    cobertura_md = _fmt_cobertura(payload.get("cobertura", {}))

    return f"""# Resumen de Área de Auditoría

## Cliente
- Cliente: {cliente}
- Periodo: {periodo}

## Área y Contexto
- Área / L/S: {area} ({codigo_ls})
- Etapa: {etapa}
- Estado del área: {estado_area}
- Riesgo: {riesgo}
- Score / prioridad: {score} / {prioridad}
- Materialidad relativa: {mat_rel:.1f}%

## Señales Expertas
{flags_md}

## Objetivo del Área
- {objetivo}

## Riesgos del Área
{riesgos_md}

## Procedimientos Pendientes
{pendientes_md}

## Cobertura de Aseveraciones
{cobertura_md}

## Hallazgos Abiertos
{hallazgos_md}

## Conclusión Operativa
- Conclusión preliminar: {concl_pre}
- Decisión de cierre: {decision}
- Recomendación final: {recomendacion}
"""


def build_area_cierre_markdown(payload: dict[str, Any]) -> str:
    resumen = build_area_resumen_markdown(payload)
    cierre_texto = _txt(payload.get("texto_cierre"), "No disponible")
    return (
        resumen
        + "\n## Texto de Revisión de Cierre\n"
        + f"{cierre_texto}\n"
    )


def save_area_markdown(cliente: str, filename: str, content: str) -> Path:
    export_dir = Path("data") / "exports" / str(cliente)
    export_dir.mkdir(parents=True, exist_ok=True)
    out_path = export_dir / filename
    out_path.write_text(content, encoding="utf-8")
    return out_path
