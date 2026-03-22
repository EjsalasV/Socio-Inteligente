"""
PDF Report Generator for SocioAI.
Generates a clean audit summary report using ReportLab.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import pandas as pd


# ── Colors (navy palette) ─────────────────────────────────────
NAVY       = (0/255, 51/255, 102/255)
BLUE_MID   = (0/255, 102/255, 204/255)
BLUE_LIGHT = (168/255, 196/255, 224/255)
WHITE      = (1, 1, 1)
GRAY_LIGHT = (0.96, 0.96, 0.97)
GRAY_MID   = (0.44, 0.47, 0.52)
RED        = (0.87, 0.21, 0.04)
ORANGE     = (1.0,  0.55, 0.0)
GREEN      = (0.0,  0.53, 0.35)
BLACK      = (0.09, 0.17, 0.29)


def _fmt_money(v: Any) -> str:
    try:
        return f"${float(v):,.2f}"
    except Exception:
        return "$0.00"


def _fmt_num(v: Any, dec: int = 1) -> str:
    try:
        return f"{float(v):,.{dec}f}"
    except Exception:
        return "0"


def _score_color(score: float):
    if score >= 70:
        return RED
    if score >= 40:
        return ORANGE
    return GREEN


def generar_pdf_resumen(
    cliente: str,
    perfil: dict[str, Any],
    resumen_tb: dict[str, Any],
    ranking_areas: pd.DataFrame | None,
    variaciones: pd.DataFrame | None,
    datos_clave: dict[str, Any] | None,
) -> bytes:
    """
    Generates a PDF audit summary report.
    Returns the PDF as bytes for Streamlit download_button.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table,
        TableStyle, HRFlowable,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=1.5*cm,
        bottomMargin=2*cm,
        title=f"SocioAI - Resumen {cliente}",
    )

    styles = getSampleStyleSheet()
    W = A4[0] - 4*cm  # usable width

    # ── Custom styles ─────────────────────────────────────────
    def _style(name, parent="Normal", **kwargs):
        s = ParagraphStyle(name, parent=styles[parent], **kwargs)
        return s

    s_title = _style(
        "s_title", fontSize=22, textColor=colors.Color(*NAVY),
        spaceAfter=4, fontName="Helvetica-Bold",
    )
    s_sub = _style(
        "s_sub", fontSize=10, textColor=colors.Color(*GRAY_MID),
        spaceAfter=2,
    )
    s_section = _style(
        "s_section", fontSize=12, textColor=colors.Color(*NAVY),
        fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6,
    )
    s_body = _style(
        "s_body", fontSize=9, textColor=colors.Color(*BLACK),
        spaceAfter=3, leading=13,
    )
    s_small = _style(
        "s_small", fontSize=8, textColor=colors.Color(*GRAY_MID),
        spaceAfter=2,
    )
    s_kpi_val = _style(
        "s_kpi_val", fontSize=16, fontName="Helvetica-Bold",
        textColor=colors.Color(*NAVY), alignment=TA_CENTER,
    )
    s_kpi_lbl = _style(
        "s_kpi_lbl", fontSize=8, textColor=colors.Color(*GRAY_MID),
        alignment=TA_CENTER,
    )
    s_center = _style("s_center", alignment=TA_CENTER, fontSize=9)
    s_right  = _style("s_right",  alignment=TA_RIGHT,  fontSize=9)

    story = []

    # ─────────────────────────────────────────────────────────
    # HEADER BANNER
    # ─────────────────────────────────────────────────────────
    banner_data = [[
        Paragraph("SocioAI", _style(
            "banner_title", fontSize=18,
            fontName="Helvetica-Bold",
            textColor=colors.white,
        )),
        Paragraph(
            "Resumen Ejecutivo de Auditoría",
            _style("banner_sub", fontSize=10,
                   textColor=colors.Color(0.8, 0.9, 1.0)),
        ),
    ]]
    banner = Table(banner_data, colWidths=[W*0.45, W*0.55])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.Color(*NAVY)),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("LEFTPADDING",   (0,0), (0,-1), 16),
        ("RIGHTPADDING",  (-1,0),(-1,-1),16),
    ]))
    story.append(banner)
    story.append(Spacer(1, 0.4*cm))

    # ─────────────────────────────────────────────────────────
    # CLIENT INFO ROW
    # ─────────────────────────────────────────────────────────
    datos_clave = datos_clave or {}
    encargo = perfil.get("encargo", {}) if isinstance(perfil, dict) else {}

    nombre_c  = str(datos_clave.get("nombre") or
                    perfil.get("cliente", {}).get("nombre_legal", cliente))
    ruc_c     = str(datos_clave.get("ruc") or
                    perfil.get("cliente", {}).get("ruc", "N/A"))
    sector_c  = str(datos_clave.get("sector") or
                    perfil.get("cliente", {}).get("sector", "N/A"))
    periodo_c = str(datos_clave.get("periodo") or
                    encargo.get("anio_activo", "N/A"))
    marco_c   = str(encargo.get("marco_referencial", "N/A"))
    riesgo_g  = str(
        perfil.get("riesgo_global", {}).get("nivel", "N/A")
        if isinstance(perfil, dict) else "N/A"
    ).upper()
    fecha_rep = datetime.now().strftime("%d/%m/%Y")

    info_data = [
        [
            Paragraph(f"<b>{nombre_c}</b>", s_body),
            Paragraph(f"RUC: {ruc_c}", s_body),
            Paragraph(f"Sector: {sector_c}", s_body),
            Paragraph(f"Período: {periodo_c}", s_body),
            Paragraph(f"Marco: {marco_c}", s_body),
            Paragraph(f"Fecha: {fecha_rep}", s_small),
        ]
    ]
    info_table = Table(
        info_data,
        colWidths=[W*0.25, W*0.18, W*0.16, W*0.13, W*0.15, W*0.13],
    )
    info_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), colors.Color(*GRAY_LIGHT)),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))

    # ─────────────────────────────────────────────────────────
    # SECTION 1 — KPIs DEL BALANCE
    # ─────────────────────────────────────────────────────────
    story.append(Paragraph("1. Balance General", s_section))
    story.append(HRFlowable(
        width=W, thickness=1,
        color=colors.Color(*BLUE_LIGHT), spaceAfter=8,
    ))

    resumen_tb = resumen_tb or {}
    activo     = float(resumen_tb.get("ACTIVO",     0) or 0)
    pasivo     = float(resumen_tb.get("PASIVO",     0) or 0)
    patrimonio = float(resumen_tb.get("PATRIMONIO", 0) or 0)
    ingresos   = float(resumen_tb.get("INGRESOS",   0) or 0)
    gastos     = float(resumen_tb.get("GASTOS",     0) or 0)

    kpi_items = [
        ("Activos Totales",  activo,     BLUE_MID),
        ("Pasivos Totales",  pasivo,     RED),
        ("Patrimonio",       patrimonio, GREEN),
        ("Ingresos",         ingresos,   BLUE_MID),
        ("Gastos",           gastos,     ORANGE),
    ]

    kpi_row = []
    for label, val, color in kpi_items:
        cell = [
            Paragraph(_fmt_money(abs(val)), _style(
                f"kv_{label}", fontSize=13,
                fontName="Helvetica-Bold",
                textColor=colors.Color(*color),
                alignment=TA_CENTER,
            )),
            Paragraph(label, s_kpi_lbl),
        ]
        kpi_row.append(cell)

    kpi_table = Table(
        [kpi_row],
        colWidths=[W/5]*5,
    )
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), colors.Color(*GRAY_LIGHT)),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("INNERGRID",     (0,0), (-1,-1), 0.5,
         colors.Color(0.88, 0.88, 0.90)),
        ("BOX",           (0,0), (-1,-1), 0.5,
         colors.Color(*BLUE_LIGHT)),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.5*cm))

    # ─────────────────────────────────────────────────────────
    # SECTION 2 — RANKING DE ÁREAS
    # ─────────────────────────────────────────────────────────
    story.append(Paragraph("2. Ranking de Áreas por Riesgo", s_section))
    story.append(HRFlowable(
        width=W, thickness=1,
        color=colors.Color(*BLUE_LIGHT), spaceAfter=8,
    ))

    if isinstance(ranking_areas, pd.DataFrame) and not ranking_areas.empty:
        rank_header = [
            Paragraph("<b>#</b>",         s_center),
            Paragraph("<b>Área</b>",       s_body),
            Paragraph("<b>Nombre</b>",     s_body),
            Paragraph("<b>Score</b>",      s_center),
            Paragraph("<b>Prioridad</b>",  s_center),
            Paragraph("<b>Saldo</b>",      s_right),
        ]
        rank_rows = [rank_header]

        df_r = ranking_areas.copy()
        if "score_riesgo" in df_r.columns:
            df_r = df_r.sort_values("score_riesgo", ascending=False)

        # Show all areas with saldo
        mask = pd.Series([True] * len(df_r))
        if "con_saldo" in df_r.columns:
            mask = df_r["con_saldo"].astype(bool)
        df_show = df_r[mask].head(12)

        for i, (_, row) in enumerate(df_show.iterrows(), start=1):
            score = float(row.get("score_riesgo", 0) or 0)
            prior = str(row.get("prioridad", "")).upper()
            saldo = float(row.get("saldo_total", 0) or 0)
            sc = _score_color(score)

            rank_rows.append([
                Paragraph(str(i), s_center),
                Paragraph(str(row.get("area", "")), s_body),
                Paragraph(
                    str(row.get("nombre", ""))[:35], s_body
                ),
                Paragraph(
                    f"<b>{score:.1f}</b>",
                    _style(f"sc_{i}", fontSize=9,
                           fontName="Helvetica-Bold",
                           textColor=colors.Color(*sc),
                           alignment=TA_CENTER),
                ),
                Paragraph(prior, s_center),
                Paragraph(_fmt_money(abs(saldo)), s_right),
            ])

        rank_table = Table(
            rank_rows,
            colWidths=[
                W*0.05, W*0.10, W*0.38,
                W*0.12, W*0.16, W*0.19,
            ],
        )
        rank_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),
             colors.Color(*NAVY)),
            ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0), 9),
            ("ROWBACKGROUNDS",(0,1), (-1,-1),
             [colors.white, colors.Color(*GRAY_LIGHT)]),
            ("GRID",          (0,0), (-1,-1), 0.4,
             colors.Color(0.88, 0.88, 0.90)),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ]))
        story.append(rank_table)
    else:
        story.append(Paragraph("Sin datos de ranking disponibles.", s_body))

    story.append(Spacer(1, 0.5*cm))

    # ─────────────────────────────────────────────────────────
    # SECTION 3 — TOP VARIACIONES
    # ─────────────────────────────────────────────────────────
    story.append(
        Paragraph("3. Top Variaciones Significativas", s_section)
    )
    story.append(HRFlowable(
        width=W, thickness=1,
        color=colors.Color(*BLUE_LIGHT), spaceAfter=8,
    ))

    if isinstance(variaciones, pd.DataFrame) and not variaciones.empty:
        var_header = [
            Paragraph("<b>Código</b>",   s_body),
            Paragraph("<b>Nombre</b>",   s_body),
            Paragraph("<b>Saldo</b>",    s_right),
            Paragraph("<b>Impacto</b>",  s_right),
        ]
        var_rows = [var_header]

        cols_needed = {
            "codigo": ["codigo", "numero_de_cuenta", "cuenta"],
            "nombre": ["nombre", "nombre_cuenta", "descripcion"],
            "saldo":  ["saldo", "saldo_actual", "saldo_2025"],
            "impacto":["impacto", "variacion_absoluta",
                       "abs_variacion_absoluta"],
        }

        def _get_col(df, candidates):
            for c in candidates:
                if c in df.columns:
                    return c
            return None

        c_cod  = _get_col(variaciones, cols_needed["codigo"])
        c_nom  = _get_col(variaciones, cols_needed["nombre"])
        c_sal  = _get_col(variaciones, cols_needed["saldo"])
        c_imp  = _get_col(variaciones, cols_needed["impacto"])

        df_v = variaciones.copy()
        if c_imp:
            df_v["_sort"] = pd.to_numeric(
                df_v[c_imp], errors="coerce"
            ).fillna(0).abs()
            df_v = df_v.sort_values("_sort", ascending=False)

        for _, row in df_v.head(10).iterrows():
            cod = str(row[c_cod])[:15] if c_cod else "—"
            nom = str(row[c_nom])[:40] if c_nom else "—"
            sal = float(row[c_sal]) if c_sal else 0
            imp = float(row[c_imp]) if c_imp else 0

            imp_color = RED if imp > 0 else colors.Color(*NAVY)
            var_rows.append([
                Paragraph(cod, s_small),
                Paragraph(nom, s_body),
                Paragraph(_fmt_money(sal), s_right),
                Paragraph(
                    _fmt_money(abs(imp)),
                    _style(f"imp_{cod}", fontSize=9,
                           textColor=imp_color,
                           alignment=TA_RIGHT),
                ),
            ])

        var_table = Table(
            var_rows,
            colWidths=[W*0.18, W*0.46, W*0.18, W*0.18],
        )
        var_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),
             colors.Color(*NAVY)),
            ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0), 9),
            ("ROWBACKGROUNDS",(0,1), (-1,-1),
             [colors.white, colors.Color(*GRAY_LIGHT)]),
            ("GRID",          (0,0), (-1,-1), 0.4,
             colors.Color(0.88, 0.88, 0.90)),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ]))
        story.append(var_table)
    else:
        story.append(
            Paragraph("Sin variaciones significativas.", s_body)
        )

    story.append(Spacer(1, 0.5*cm))

    # ─────────────────────────────────────────────────────────
    # SECTION 4 — ESTADO DE CIERRE POR ÁREA
    # ─────────────────────────────────────────────────────────
    story.append(
        Paragraph("4. Estado de Cierre por Área", s_section)
    )
    story.append(HRFlowable(
        width=W, thickness=1,
        color=colors.Color(*BLUE_LIGHT), spaceAfter=8,
    ))

    if isinstance(ranking_areas, pd.DataFrame) and not ranking_areas.empty:
        cierre_header = [
            Paragraph("<b>Área</b>",       s_body),
            Paragraph("<b>Nombre</b>",     s_body),
            Paragraph("<b>Score</b>",      s_center),
            Paragraph("<b>Prioridad</b>",  s_center),
            Paragraph("<b>Estado</b>",     s_center),
        ]
        cierre_rows = [cierre_header]

        mask2 = pd.Series([True] * len(ranking_areas))
        if "con_saldo" in ranking_areas.columns:
            mask2 = ranking_areas["con_saldo"].astype(bool)
        df_c = ranking_areas[mask2].copy()
        if "score_riesgo" in df_c.columns:
            df_c = df_c.sort_values("score_riesgo", ascending=False)

        for _, row in df_c.head(12).iterrows():
            score  = float(row.get("score_riesgo", 0) or 0)
            prior  = str(row.get("prioridad", "media")).upper()
            sc     = _score_color(score)

            if score >= 70:
                estado_txt = "Requiere revisión"
                estado_color = RED
            elif score >= 40:
                estado_txt = "En proceso"
                estado_color = ORANGE
            else:
                estado_txt = "Controlado"
                estado_color = GREEN

            cierre_rows.append([
                Paragraph(
                    str(row.get("area", "")), s_body
                ),
                Paragraph(
                    str(row.get("nombre", ""))[:30], s_body
                ),
                Paragraph(
                    f"<b>{score:.1f}</b>",
                    _style(f"cs_{_}", fontSize=9,
                           fontName="Helvetica-Bold",
                           textColor=colors.Color(*sc),
                           alignment=TA_CENTER),
                ),
                Paragraph(prior, s_center),
                Paragraph(
                    estado_txt,
                    _style(f"ce_{_}", fontSize=9,
                           textColor=colors.Color(*estado_color),
                           alignment=TA_CENTER),
                ),
            ])

        cierre_table = Table(
            cierre_rows,
            colWidths=[
                W*0.10, W*0.42, W*0.12, W*0.16, W*0.20
            ],
        )
        cierre_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),
             colors.Color(*NAVY)),
            ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0), 9),
            ("ROWBACKGROUNDS",(0,1), (-1,-1),
             [colors.white, colors.Color(*GRAY_LIGHT)]),
            ("GRID",          (0,0), (-1,-1), 0.4,
             colors.Color(0.88, 0.88, 0.90)),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ]))
        story.append(cierre_table)
    else:
        story.append(
            Paragraph("Sin datos de estado de cierre.", s_body)
        )

    # ─────────────────────────────────────────────────────────
    # FOOTER
    # ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(
        width=W, thickness=0.5,
        color=colors.Color(*BLUE_LIGHT), spaceAfter=4,
    ))
    story.append(Paragraph(
        f"Generado por SocioAI · {fecha_rep} · "
        f"Uso interno — confidencial",
        _style("footer", fontSize=7,
               textColor=colors.Color(*GRAY_MID),
               alignment=TA_CENTER),
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
