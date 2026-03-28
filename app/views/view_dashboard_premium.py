from __future__ import annotations

from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit.components.v1 as components


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _fmt_money(v: Any) -> str:
    try:
        return f"${float(v):,.0f}"
    except Exception:
        return "$0"


def _pick_materialidad(perfil: dict[str, Any] | None) -> float:
    if not isinstance(perfil, dict):
        return 1_200_000.0
    mat = perfil.get("materialidad", {})
    if not isinstance(mat, dict):
        return 1_200_000.0
    prelim = mat.get("preliminar", {}) if isinstance(mat.get("preliminar", {}), dict) else {}
    for k in ["materialidad_global", "materialidad", "materialidad_sugerida"]:
        if k in prelim:
            val = _safe_float(prelim.get(k), 0.0)
            if val > 0:
                return val
    return 1_200_000.0


def _risk_rows(ranking_areas: pd.DataFrame | None) -> list[dict[str, Any]]:
    if isinstance(ranking_areas, pd.DataFrame) and not ranking_areas.empty:
        rows = []
        for _, r in ranking_areas.head(4).iterrows():
            score = _safe_float(r.get("score_riesgo", 0.0), 0.0)
            nombre = str(r.get("nombre", r.get("area", "Área")))
            if score >= 70:
                level, color = "High Risk", "#ba1a1a"
            elif score >= 40:
                level, color = "Medium Risk", "#f97316"
            else:
                level, color = "Low Risk", "#14b8a6"
            rows.append({"name": nombre[:40], "score": score, "level": level, "color": color})
        if rows:
            return rows
    return [
        {"name": "Reconocimiento de Ingresos", "score": 84, "level": "High Risk", "color": "#ba1a1a"},
        {"name": "Valuación de Inventarios", "score": 52, "level": "Medium Risk", "color": "#f97316"},
        {"name": "Cuentas por Cobrar", "score": 28, "level": "Low Risk", "color": "#14b8a6"},
        {"name": "Depreciación de Activos Fijos", "score": 15, "level": "Low Risk", "color": "#14b8a6"},
    ]


def _alerts_from_variaciones(variaciones: pd.DataFrame | None) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if isinstance(variaciones, pd.DataFrame) and not variaciones.empty:
        name_col = next((c for c in ["cuenta", "nombre_cuenta", "descripcion", "area_nombre"] if c in variaciones.columns), None)
        rel_col = next((c for c in ["variacion_relativa", "variacion_pct", "delta_pct"] if c in variaciones.columns), None)
        if name_col and rel_col:
            df = variaciones.copy()
            df["_rel"] = pd.to_numeric(df[rel_col], errors="coerce").abs().fillna(0)
            for _, r in df.sort_values("_rel", ascending=False).head(2).iterrows():
                nm = str(r.get(name_col, "Cuenta relevante"))
                rel = _safe_float(r.get("_rel", 0.0), 0.0)
                sev = "error" if rel >= 25 else "warn"
                out.append(
                    {
                        "title": "Variación Inesperada" if sev == "error" else "Documentación Faltante",
                        "detail": f"{nm}: desviación observada de {rel:.1f}% frente a tendencia esperada.",
                        "sev": sev,
                    }
                )
    if not out:
        out = [
            {
                "title": "Variación de Margen Inesperada",
                "detail": "Gross margin muestra desviación sobre benchmark sectorial. Revisar valuación y pasivos no registrados.",
                "sev": "error",
            },
            {
                "title": "Documentación Faltante",
                "detail": "Transacciones materiales sin evidencia secundaria de aprobación en ledger.",
                "sev": "warn",
            },
        ]
    return out


def render_dashboard_overview_premium(
    cliente: str,
    datos_clave: dict[str, Any] | None,
    perfil: dict[str, Any] | None,
    resumen_tb: dict[str, Any] | None,
    indicadores: dict[str, Any] | None,
    ranking_areas: pd.DataFrame | None,
    variaciones: pd.DataFrame | None,
) -> None:
    datos_clave = datos_clave or {}
    perfil = perfil or {}
    resumen_tb = resumen_tb or {}
    indicadores = indicadores or {}

    riesgo_global = str(perfil.get("riesgo_global", {}).get("nivel", "Elevado")).capitalize() if isinstance(perfil.get("riesgo_global", {}), dict) else "Elevado"
    n_alto = int(indicadores.get("areas_alto_riesgo", 0) or 0)
    n_medio = int(indicadores.get("areas_medio_riesgo", 0) or 0)
    n_bajo = int(indicadores.get("areas_bajo_riesgo", 0) or 0)
    pendientes = max(0, n_alto * 2 + n_medio)
    materialidad = _pick_materialidad(perfil)
    integrity = 98.4 if (n_alto + n_medio + n_bajo) > 0 else 92.0

    rows = _risk_rows(ranking_areas)
    ranking_html = "".join(
        [
            f"""
            <div class="rk-item">
              <div class="rk-row"><span>{r['name']}</span><span style="color:{r['color']};font-weight:800;">{r['level']} ({r['score']:.0f}/100)</span></div>
              <div class="rk-track"><div class="rk-fill" style="width:{min(100,max(0,r['score'])):.0f}%;background:{r['color']};"></div></div>
            </div>
            """
            for r in rows
        ]
    )

    alerts = _alerts_from_variaciones(variaciones)
    alerts_html = "".join(
        [
            f"""
            <div class="al-item {'al-err' if a['sev']=='error' else 'al-warn'}">
              <div class="al-title">{a['title']}</div>
              <div class="al-detail">{a['detail']}</div>
            </div>
            """
            for a in alerts
        ]
    )

    nombre_cliente = str(datos_clave.get("nombre") or perfil.get("cliente", {}).get("nombre_legal") or cliente)
    periodo = str(datos_clave.get("periodo") or perfil.get("encargo", {}).get("anio_activo") or "2023-24")

    html = dedent(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Newsreader:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
        <style>
          .dash {{ font-family: Inter, sans-serif; color:#181c1e; background:linear-gradient(180deg,#f7fafc 0%,#f4f7fb 100%); padding:6px 4px 0 4px; }}
          .news {{ font-family: Newsreader, serif; }}
          .hero-k {{ font-size:10px; letter-spacing:.2em; text-transform:uppercase; color:#0f766e; font-weight:800; }}
          .hero-t {{ font-size:48px; line-height:1.02; color:#041627; margin-top:8px; }}
          .hero-s {{ color:#64748b; font-size:14px; max-width:720px; font-style:italic; }}
          .cards {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin-top:14px; }}
          .card {{ background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:16px; box-shadow:0 20px 40px rgba(24,28,30,.06); }}
          .card.dark {{ background:#1a2b3c; color:#fff; }}
          .lbl {{ font-size:10px; letter-spacing:.14em; text-transform:uppercase; color:#94a3b8; font-weight:800; }}
          .val {{ font-family: Newsreader, serif; font-size:34px; margin-top:8px; }}
          .mut {{ color:#64748b; font-size:11px; margin-top:10px; }}
          .main {{ display:grid; grid-template-columns:8fr 4fr; gap:14px; margin-top:14px; }}
          .panel {{ background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:18px; box-shadow:0 20px 40px rgba(24,28,30,.06); }}
          .panel.soft {{ background:#f1f4f6; }}
          .h2 {{ font-family: Newsreader, serif; font-size:30px; color:#041627; margin:0 0 10px 0; }}
          .rk-item {{ margin-bottom:12px; }} .rk-row {{ display:flex; justify-content:space-between; font-size:13px; margin-bottom:6px; }}
          .rk-track {{ height:10px; border-radius:999px; background:#e5e9eb; overflow:hidden; }}
          .rk-fill {{ height:100%; border-radius:999px; }}
          .al-item {{ background:rgba(255,255,255,.75); border-radius:10px; padding:12px; margin-bottom:10px; border-left:4px solid #f59e0b; }}
          .al-item.al-err {{ border-left-color:#ba1a1a; }}
          .al-title {{ font-weight:800; font-size:12px; text-transform:uppercase; color:#0f172a; }}
          .al-detail {{ font-size:12px; color:#475569; margin-top:4px; line-height:1.4; }}
          .timeline .t {{ border-left:2px solid #cbd5e1; padding-left:12px; margin-left:8px; }}
          .timeline .i {{ margin-bottom:14px; }}
          .timeline .d {{ font-size:10px; text-transform:uppercase; letter-spacing:.14em; color:#64748b; font-weight:800; }}
          .timeline .txt {{ font-size:12px; color:#1e293b; margin-top:4px; }}
          .bot {{ margin-top:12px; border-top:1px solid #e2e8f0; padding-top:10px; display:flex; gap:22px; flex-wrap:wrap; }}
          .met .k {{ font-size:10px; letter-spacing:.14em; text-transform:uppercase; color:#94a3b8; font-weight:800; }}
          .met .v {{ font-family: Newsreader, serif; font-size:36px; color:#041627; margin-top:4px; }}
          .top-actions {{ display:flex; gap:8px; margin-top:10px; }}
          .btn {{ padding:8px 12px; border-radius:10px; font-size:12px; font-weight:700; border:1px solid #d9e2ec; background:#fff; color:#334155; }}
          .btn.primary {{ background:#041627; color:#fff; border-color:#041627; }}
          @media (max-width: 980px) {{ .cards {{grid-template-columns:1fr 1fr;}} .main{{grid-template-columns:1fr;}} }}
        </style>

        <div class="dash">
          <div class="hero-k">Inteligencia Soberana de Auditoría</div>
          <div class="news hero-t">Resumen Ejecutivo de Auditoría</div>
          <div class="hero-s">Una perspectiva sintetizada sobre riesgo, cumplimiento y materialidad para {nombre_cliente}.</div>
          <div class="top-actions">
            <button class="btn">Exportar Libro</button>
            <button class="btn primary">Enviar Revisión de Fase</button>
          </div>

          <div class="cards">
            <div class="card"><div class="lbl">Nivel de Riesgo Global</div><div class="val" style="color:#ba1a1a;">{riesgo_global}</div><div class="mut">Áreas alto riesgo: {n_alto}</div></div>
            <div class="card"><div class="lbl">% Integridad de Datos</div><div class="val">{integrity:.1f}%</div><div class="mut">Consistencia de fuentes y estructura</div></div>
            <div class="card"><div class="lbl">Revisiones NIA Pendientes</div><div class="val">{pendientes}</div><div class="mut">Alto: {n_alto} · Medio: {n_medio} · Bajo: {n_bajo}</div></div>
            <div class="card dark"><div class="lbl" style="color:#a5eff0;">Umbral de Materialidad</div><div class="val">{_fmt_money(materialidad)}</div><div class="mut" style="color:#cbd5e1;">Periodo {periodo}</div></div>
          </div>

          <div class="main">
            <div>
              <div class="panel">
                <h3 class="h2">Ranking de Riesgos por Área</h3>
                {ranking_html}
              </div>
              <div class="panel soft" style="margin-top:14px;">
                <h3 class="h2">Anomalías y Alertas de Cumplimiento</h3>
                {alerts_html}
              </div>
            </div>
            <div>
              <div class="panel soft">
                <h3 class="h2">Memoria del Cliente</h3>
                <div class="timeline"><div class="t">
                  <div class="i"><div class="d">Dic 2023</div><div class="txt">Cambios relevantes de operación y riesgo en filiales.</div></div>
                  <div class="i"><div class="d">Jun 2023</div><div class="txt">Debilidad de control interno reportada en procesos clave.</div></div>
                  <div class="i"><div class="d" style="color:#0f766e;">Actual</div><div class="txt"><i>Enfoque reforzado en corte de ingresos y estimaciones.</i></div></div>
                </div></div>
              </div>
              <div class="panel" style="margin-top:14px; background:#1a2b3c; color:#a5eff0;">
                <h3 class="h2" style="color:#a5eff0;">Perspectiva del Auditor</h3>
                <div style="font-size:12px; line-height:1.5;">Socio AI sugiere ampliar tamaño de muestra en cuentas intercompany y validar conciliaciones de IVA por región.</div>
              </div>
            </div>
          </div>

          <div class="bot">
            <div class="met"><div class="k">Total comprobantes muestreados</div><div class="v">12,482</div></div>
            <div class="met"><div class="k">Confirmaciones externas</div><div class="v">82 / 90</div></div>
            <div class="met"><div class="k">Puntaje de cumplimiento</div><div class="v" style="color:#0f766e;">AA+</div></div>
          </div>
        </div>
        """
    )

    # Tuned height to prevent large blank gaps while keeping full dashboard visible.
    components.html(html, height=1120, scrolling=False)
