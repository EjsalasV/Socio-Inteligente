"""
PDF report services for SocioAI.
Editorial layout based on Sovereign Intelligence palette.
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

# Sovereign palette
PRIMARY_HEX = "#041627"
PRIMARY_CONTAINER_HEX = "#1A2B3C"
SURFACE_HEX = "#F7FAFC"
SURFACE_LOW_HEX = "#F1F4F6"
TEXT_MUTED_HEX = "#64748B"
ERROR_HEX = "#BA1A1A"
WARN_HEX = "#B45309"
SUCCESS_HEX = "#047857"


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.strip().lstrip("#")
    if len(h) != 6:
        return (0.0, 0.0, 0.0)
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


def _fmt_money(v: Any) -> str:
    try:
        return f"${float(v):,.2f}"
    except Exception:
        return "$0.00"


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _materialidad_planeacion(perfil: dict[str, Any] | None, fallback: float = 0.0) -> float:
    if not isinstance(perfil, dict):
        return fallback
    mat = perfil.get("materialidad", {})
    if not isinstance(mat, dict):
        return fallback
    prelim = mat.get("preliminar", {})
    if not isinstance(prelim, dict):
        return fallback
    for key in ("materialidad_global", "materialidad", "materialidad_sugerida"):
        val = _safe_float(prelim.get(key), 0.0)
        if val > 0:
            return val
    return fallback


def _score_color(score: float):
    from reportlab.lib import colors

    if score >= 70:
        return colors.Color(*_hex_to_rgb(ERROR_HEX))
    if score >= 40:
        return colors.Color(*_hex_to_rgb(WARN_HEX))
    return colors.Color(*_hex_to_rgb(SUCCESS_HEX))


def _register_editorial_fonts() -> dict[str, str]:
    """
    Try to register Inter and Newsreader from local assets.
    Falls back safely to Helvetica family when font files are unavailable.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Defaults
    names = {
        "body": "Helvetica",
        "body_bold": "Helvetica-Bold",
        "serif": "Times-Roman",
        "serif_bold": "Times-Bold",
        "serif_italic": "Times-Italic",
    }

    project_root = Path(__file__).resolve().parents[2]
    font_dirs = [
        project_root / "app" / "assets" / "fonts",
        project_root / "assets" / "fonts",
        project_root / "fonts",
    ]

    inter_file = None
    news_file = None
    for d in font_dirs:
        if not d.exists():
            continue
        if inter_file is None:
            inter_file = next(
                (p for p in [d / "Inter-Regular.ttf", d / "Inter.ttf"] if p.exists()), None
            )
        if news_file is None:
            news_file = next(
                (p for p in [d / "Newsreader-Regular.ttf", d / "Newsreader.ttf"] if p.exists()),
                None,
            )

    try:
        if inter_file:
            pdfmetrics.registerFont(TTFont("Inter", str(inter_file)))
            names["body"] = "Inter"
        if news_file:
            pdfmetrics.registerFont(TTFont("Newsreader", str(news_file)))
            names["serif"] = "Newsreader"
            names["serif_italic"] = "Newsreader"
    except Exception:
        # Keep built-in fallback fonts.
        pass

    return names


def _build_styles():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    fonts = _register_editorial_fonts()
    styles = getSampleStyleSheet()

    def style(name: str, parent: str = "Normal", **kwargs):
        return ParagraphStyle(name, parent=styles[parent], **kwargs)

    return {
        "fonts": fonts,
        "title": style(
            "title",
            fontName=fonts["serif"],
            fontSize=24,
            textColor=colors.Color(*_hex_to_rgb(PRIMARY_HEX)),
            spaceAfter=4,
        ),
        "subtitle": style(
            "subtitle",
            fontName=fonts["body"],
            fontSize=10,
            textColor=colors.Color(*_hex_to_rgb(TEXT_MUTED_HEX)),
            spaceAfter=4,
        ),
        "section": style(
            "section",
            fontName=fonts["serif_bold"],
            fontSize=12,
            textColor=colors.Color(*_hex_to_rgb(PRIMARY_HEX)),
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": style(
            "body",
            fontName=fonts["body"],
            fontSize=9,
            leading=13,
            textColor=colors.Color(0.1, 0.12, 0.16),
            spaceAfter=2,
        ),
        "small": style(
            "small",
            fontName=fonts["body"],
            fontSize=8,
            textColor=colors.Color(*_hex_to_rgb(TEXT_MUTED_HEX)),
            spaceAfter=2,
        ),
        "kpi_value": style(
            "kpi_value",
            fontName=fonts["serif_bold"],
            fontSize=18,
            alignment=TA_CENTER,
            textColor=colors.Color(*_hex_to_rgb(PRIMARY_HEX)),
        ),
        "kpi_label": style(
            "kpi_label",
            fontName=fonts["body"],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.Color(*_hex_to_rgb(TEXT_MUTED_HEX)),
        ),
        "center": style("center", fontName=fonts["body"], fontSize=9, alignment=TA_CENTER),
        "right": style("right", fontName=fonts["body"], fontSize=9, alignment=TA_RIGHT),
        "memo": style(
            "memo",
            fontName=fonts["serif_italic"],
            fontSize=13,
            leading=18,
            textColor=colors.Color(*_hex_to_rgb(PRIMARY_HEX)),
        ),
    }


def _draw_editorial_header(
    story: list[Any],
    width: float,
    cliente: str,
    titulo: str,
    styles: dict[str, Any],
    *,
    sector: str = "N/A",
) -> None:
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle

    banner = Table(
        [
            [
                Paragraph("Sovereign Intelligence", styles["title"]),
                Paragraph(titulo, styles["subtitle"]),
            ]
        ],
        colWidths=[width * 0.55, width * 0.45],
    )
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(*_hex_to_rgb(PRIMARY_HEX))),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ]
        )
    )
    story.append(banner)

    info = Table(
        [
            [
                Paragraph(f"Cliente: <b>{cliente}</b>  |  Sector: <b>{sector}</b>", styles["body"]),
                Paragraph(datetime.now().strftime("%d/%m/%Y"), styles["right"]),
            ]
        ],
        colWidths=[width * 0.70, width * 0.30],
    )
    info.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(*_hex_to_rgb(SURFACE_LOW_HEX))),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(info)


def generate_executive_summary_pdf(
    cliente: str,
    dashboard_data: dict[str, Any] | None = None,
    *,
    riesgo_global: Any | None = None,
    materialidad: Any | None = None,
    periodo: str | None = None,
) -> bytes:
    """
    Generate a single-page editorial PDF for executive summary.
    Uses dashboard inputs focused on riesgo global and materialidad.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    dashboard_data = dashboard_data or {}
    risk = (
        str(
            riesgo_global
            if riesgo_global is not None
            else dashboard_data.get("riesgo_global", "Medio")
        )
        .strip()
        .capitalize()
    )
    mat = _safe_float(
        materialidad if materialidad is not None else dashboard_data.get("materialidad", 0.0), 0.0
    )
    period = str(periodo or dashboard_data.get("periodo", "Vigente"))
    sector = str(dashboard_data.get("sector", "N/A"))

    risk_color = (
        ERROR_HEX
        if "alto" in risk.lower()
        else WARN_HEX if "medio" in risk.lower() else SUCCESS_HEX
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"Reporte Ejecutivo de Auditoría - Socio AI - {cliente}",
    )

    styles = _build_styles()
    width = A4[0] - 4 * cm
    story: list[Any] = []

    _draw_editorial_header(
        story,
        width,
        cliente,
        "Reporte Ejecutivo de Auditoría - Socio AI",
        styles,
        sector=sector,
    )
    story.append(Spacer(1, 0.35 * cm))

    # Resumen de riesgos (bloque solicitado)
    story.append(Paragraph("Resumen de Riesgos", styles["section"]))
    kpi = Table(
        [
            [
                Paragraph(f"<b>{risk}</b>", styles["kpi_value"]),
                Paragraph(_fmt_money(mat), styles["kpi_value"]),
                Paragraph(period, styles["kpi_value"]),
            ],
            [
                Paragraph("Riesgo Global", styles["kpi_label"]),
                Paragraph("Materialidad de Planeación", styles["kpi_label"]),
                Paragraph("Periodo", styles["kpi_label"]),
            ],
        ],
        colWidths=[width / 3] * 3,
    )
    kpi.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(*_hex_to_rgb(SURFACE_HEX))),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.Color(*_hex_to_rgb("#D7DEE8"))),
                ("LINEABOVE", (0, 1), (-1, 1), 0.35, colors.Color(*_hex_to_rgb("#DDE5EF"))),
                ("TEXTCOLOR", (0, 0), (0, 0), colors.Color(*_hex_to_rgb(risk_color))),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(kpi)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Memo del Socio", styles["section"]))
    memo = Table(
        [
            [
                Paragraph(
                    "La lectura ejecutiva indica que el encargo requiere foco en áreas de mayor exposición, "
                    "asegurando evidencia suficiente y adecuada para cierre. Este resumen prioriza riesgo global "
                    "y materialidad de planeación como ejes de decisión.",
                    styles["memo"],
                )
            ]
        ],
        colWidths=[width],
    )
    memo.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(*_hex_to_rgb(SURFACE_LOW_HEX))),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.Color(*_hex_to_rgb(PRIMARY_HEX))),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ]
        )
    )
    story.append(memo)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def generar_pdf_resumen(
    cliente: str,
    perfil: dict[str, Any],
    resumen_tb: dict[str, Any],
    ranking_areas: pd.DataFrame | None,
    variaciones: pd.DataFrame | None,
    datos_clave: dict[str, Any] | None,
) -> bytes:
    """
    Legacy-compatible detailed report with editorial styling.
    Keeps current data logic and output as PDF bytes.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    datos_clave = datos_clave or {}
    encargo = perfil.get("encargo", {}) if isinstance(perfil, dict) else {}
    riesgo_g = str(
        perfil.get("riesgo_global", {}).get("nivel", "N/A") if isinstance(perfil, dict) else "N/A"
    ).upper()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm,
        title=f"SocioAI - Resumen {cliente}",
    )

    styles = _build_styles()
    width = A4[0] - 4 * cm
    story: list[Any] = []

    _draw_editorial_header(
        story,
        width,
        cliente,
        "Reporte Ejecutivo de Auditoría - Socio AI",
        styles,
        sector=str(datos_clave.get("sector") or perfil.get("cliente", {}).get("sector", "N/A")),
    )
    story.append(Spacer(1, 0.35 * cm))

    nombre_c = str(
        datos_clave.get("nombre") or perfil.get("cliente", {}).get("nombre_legal", cliente)
    )
    ruc_c = str(datos_clave.get("ruc") or perfil.get("cliente", {}).get("ruc", "N/A"))
    sector_c = str(datos_clave.get("sector") or perfil.get("cliente", {}).get("sector", "N/A"))
    periodo_c = str(datos_clave.get("periodo") or encargo.get("anio_activo", "N/A"))
    marco_c = str(encargo.get("marco_referencial", "N/A"))

    materialidad_plan = _materialidad_planeacion(perfil, 0.0)
    info = Table(
        [
            [
                Paragraph(f"<b>{nombre_c}</b>", styles["body"]),
                Paragraph(f"RUC: {ruc_c}", styles["body"]),
                Paragraph(f"Sector: {sector_c}", styles["body"]),
                Paragraph(f"Periodo: {periodo_c}", styles["body"]),
                Paragraph(f"Marco: {marco_c}", styles["body"]),
                Paragraph(
                    f"Riesgo: {riesgo_g} | Materialidad: {_fmt_money(materialidad_plan)}",
                    styles["body"],
                ),
            ]
        ],
        colWidths=[
            width * 0.22,
            width * 0.14,
            width * 0.15,
            width * 0.14,
            width * 0.16,
            width * 0.19,
        ],
    )
    info.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(*_hex_to_rgb(SURFACE_LOW_HEX))),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(info)
    story.append(Spacer(1, 0.35 * cm))

    # Resumen de riesgos
    story.append(Paragraph("Resumen de Riesgos", styles["section"]))
    riesgo_color_hex = (
        ERROR_HEX if "ALTO" in riesgo_g else WARN_HEX if "MEDIO" in riesgo_g else SUCCESS_HEX
    )
    riesgo_tbl = Table(
        [
            [
                Paragraph(
                    f"<b>Nivel de Riesgo Global:</b> <font color='{riesgo_color_hex}'>{riesgo_g}</font>",
                    styles["body"],
                ),
                Paragraph(
                    f"<b>Materialidad de Planeación:</b> {_fmt_money(materialidad_plan)}",
                    styles["right"],
                ),
            ]
        ],
        colWidths=[width * 0.58, width * 0.42],
    )
    riesgo_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(*_hex_to_rgb(SURFACE_HEX))),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.Color(*_hex_to_rgb("#D7DEE8"))),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(riesgo_tbl)
    story.append(Spacer(1, 0.35 * cm))

    # KPI section
    resumen_tb = resumen_tb or {}
    kpi_items = [
        ("Activos", _fmt_money(abs(_safe_float(resumen_tb.get("ACTIVO", 0)))), PRIMARY_HEX),
        ("Pasivos", _fmt_money(abs(_safe_float(resumen_tb.get("PASIVO", 0)))), ERROR_HEX),
        ("Patrimonio", _fmt_money(abs(_safe_float(resumen_tb.get("PATRIMONIO", 0)))), SUCCESS_HEX),
        ("Ingresos", _fmt_money(abs(_safe_float(resumen_tb.get("INGRESOS", 0)))), PRIMARY_HEX),
        ("Gastos", _fmt_money(abs(_safe_float(resumen_tb.get("GASTOS", 0)))), WARN_HEX),
    ]

    story.append(Paragraph("1. Balance General", styles["section"]))
    story.append(
        HRFlowable(
            width=width, thickness=0.7, color=colors.Color(*_hex_to_rgb("#D8E2EF")), spaceAfter=8
        )
    )

    kpi_cells: list[list[Any]] = []
    for label, value, color_hex in kpi_items:
        kpi_cells.append(
            [
                Paragraph(f"<font color='{color_hex}'><b>{value}</b></font>", styles["kpi_value"]),
                Paragraph(label, styles["kpi_label"]),
            ]
        )

    kpi_table = Table([kpi_cells], colWidths=[width / 5] * 5)
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(*_hex_to_rgb(SURFACE_HEX))),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.Color(*_hex_to_rgb("#D7DEE8"))),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.Color(*_hex_to_rgb("#E2E8F0"))),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 0.35 * cm))

    # Ranking section
    story.append(Paragraph("2. Ranking de Areas por Riesgo", styles["section"]))
    story.append(
        HRFlowable(
            width=width, thickness=0.7, color=colors.Color(*_hex_to_rgb("#D8E2EF")), spaceAfter=8
        )
    )

    if isinstance(ranking_areas, pd.DataFrame) and not ranking_areas.empty:
        df_r = ranking_areas.copy()
        if "score_riesgo" in df_r.columns:
            df_r["_score"] = pd.to_numeric(df_r["score_riesgo"], errors="coerce").fillna(0)
            df_r = df_r.sort_values("_score", ascending=False)

        rows = [
            [
                Paragraph("<b>#</b>", styles["center"]),
                Paragraph("<b>Area</b>", styles["body"]),
                Paragraph("<b>Nombre</b>", styles["body"]),
                Paragraph("<b>Score</b>", styles["center"]),
                Paragraph("<b>Saldo</b>", styles["right"]),
            ]
        ]

        for i, (_, row) in enumerate(df_r.head(12).iterrows(), start=1):
            score = _safe_float(row.get("score_riesgo", row.get("_score", 0)), 0)
            score_hex = ERROR_HEX if score >= 70 else WARN_HEX if score >= 40 else SUCCESS_HEX
            rows.append(
                [
                    Paragraph(str(i), styles["center"]),
                    Paragraph(str(row.get("area", "")), styles["body"]),
                    Paragraph(str(row.get("nombre", ""))[:35], styles["body"]),
                    Paragraph(
                        f"<b><font color='{score_hex}'>{score:.1f}</font></b>", styles["center"]
                    ),
                    Paragraph(
                        _fmt_money(abs(_safe_float(row.get("saldo_total", 0)))), styles["right"]
                    ),
                ]
            )

        t = Table(
            rows, colWidths=[width * 0.06, width * 0.12, width * 0.40, width * 0.12, width * 0.30]
        )
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.Color(*_hex_to_rgb(PRIMARY_HEX))),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.Color(*_hex_to_rgb(SURFACE_LOW_HEX))],
                    ),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.Color(*_hex_to_rgb("#D7DEE8"))),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.35, colors.Color(*_hex_to_rgb("#E6EDF6"))),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(t)
    else:
        story.append(Paragraph("Sin datos de ranking disponibles.", styles["body"]))

    # Variaciones section
    story.append(Spacer(1, 0.35 * cm))
    story.append(Paragraph("3. Variaciones Significativas", styles["section"]))
    story.append(
        HRFlowable(
            width=width, thickness=0.7, color=colors.Color(*_hex_to_rgb("#D8E2EF")), spaceAfter=8
        )
    )

    if isinstance(variaciones, pd.DataFrame) and not variaciones.empty:
        df_v = variaciones.copy()
        c_nom = next(
            (c for c in ["nombre", "nombre_cuenta", "descripcion"] if c in df_v.columns), None
        )
        c_imp = next(
            (
                c
                for c in ["impacto", "variacion_absoluta", "abs_variacion_absoluta"]
                if c in df_v.columns
            ),
            None,
        )
        if c_imp:
            df_v["_abs"] = pd.to_numeric(df_v[c_imp], errors="coerce").abs().fillna(0)
            df_v = df_v.sort_values("_abs", ascending=False)

        rows = [
            [
                Paragraph("<b>Cuenta</b>", styles["body"]),
                Paragraph("<b>Impacto</b>", styles["right"]),
            ]
        ]
        for _, row in df_v.head(8).iterrows():
            name = str(row.get(c_nom, "Cuenta"))[:62] if c_nom else "Cuenta"
            impact = _safe_float(row.get(c_imp, 0), 0) if c_imp else 0
            color = ERROR_HEX if impact > 0 else PRIMARY_HEX
            rows.append(
                [
                    Paragraph(name, styles["body"]),
                    Paragraph(
                        f"<font color='{color}'>{_fmt_money(abs(impact))}</font>", styles["right"]
                    ),
                ]
            )

        vtab = Table(rows, colWidths=[width * 0.72, width * 0.28])
        vtab.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.Color(*_hex_to_rgb(PRIMARY_HEX))),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.Color(*_hex_to_rgb(SURFACE_LOW_HEX))],
                    ),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.Color(*_hex_to_rgb("#D7DEE8"))),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.35, colors.Color(*_hex_to_rgb("#E6EDF6"))),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(vtab)
    else:
        story.append(Paragraph("Sin variaciones significativas.", styles["body"]))

    story.append(Spacer(1, 0.6 * cm))
    story.append(
        Paragraph(
            f"Generado por SocioAI - {datetime.now().strftime('%d/%m/%Y')} - Uso interno confidencial",
            styles["small"],
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
