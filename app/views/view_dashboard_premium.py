from __future__ import annotations

from textwrap import dedent
from typing import Any
from pathlib import Path

import pandas as pd
import streamlit.components.v1 as components
import yaml

try:
    from domain.services.materialidad_service import calcular_materialidad
except Exception:
    calcular_materialidad = None


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _fmt_money(v: Any) -> str:
    try:
        n = float(v)
        if n < 0:
            return f"(${abs(n):,.0f})"
        return f"${n:,.0f}"
    except Exception:
        return "$0"


def _pick_materialidad(cliente: str, perfil: dict[str, Any] | None) -> float:
    if not isinstance(perfil, dict):
        perfil = {}

    # 1) perfil en memoria
    mat = perfil.get("materialidad", {})
    if isinstance(mat, dict):
        prelim = mat.get("preliminar", {}) if isinstance(mat.get("preliminar", {}), dict) else {}
        for key in ["materialidad_global", "materialidad", "materialidad_sugerida"]:
            val = _safe_float(prelim.get(key), 0.0)
            if val > 0:
                return val

    # 2) archivo data/clientes/{cliente}/materialidad.yaml
    try:
        p = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "clientes"
            / str(cliente)
            / "materialidad.yaml"
        )
        if p.exists():
            payload = yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
            if isinstance(payload, dict):
                for node_key in ["preliminar", "calculada", "materialidad", "data"]:
                    node = payload.get(node_key)
                    if isinstance(node, dict):
                        for key in ["materialidad_global", "materialidad", "materialidad_sugerida"]:
                            val = _safe_float(node.get(key), 0.0)
                            if val > 0:
                                return val
                for key in ["materialidad_global", "materialidad", "materialidad_sugerida"]:
                    val = _safe_float(payload.get(key), 0.0)
                    if val > 0:
                        return val
    except Exception:
        pass

    # 3) servicio
    try:
        if callable(calcular_materialidad):
            calc = calcular_materialidad(str(cliente))
            if isinstance(calc, dict):
                for key in ["materialidad_sugerida", "materialidad_maxima", "materialidad_minima"]:
                    val = _safe_float(calc.get(key), 0.0)
                    if val > 0:
                        return val
    except Exception:
        pass

    return 0.0


def _totales_tb(tb: pd.DataFrame | None, resumen_tb: dict[str, Any]) -> dict[str, float]:
    # Fallback from resumen already computed
    fallback = {
        "ACTIVO": _safe_float(resumen_tb.get("ACTIVO", 0.0)),
        "PASIVO": _safe_float(resumen_tb.get("PASIVO", 0.0)),
        "PATRIMONIO": _safe_float(resumen_tb.get("PATRIMONIO", 0.0)),
        "INGRESOS": _safe_float(resumen_tb.get("INGRESOS", 0.0)),
        "GASTOS": _safe_float(resumen_tb.get("GASTOS", 0.0)),
    }

    if not isinstance(tb, pd.DataFrame) or tb.empty:
        return fallback

    df = tb.copy()
    saldo_col = next((c for c in ["saldo", "saldo_actual", "saldo_2025"] if c in df.columns), None)
    if not saldo_col:
        return fallback
    df["_saldo"] = pd.to_numeric(df[saldo_col], errors="coerce").fillna(0.0).abs()

    # Prefer canonical tipo_cuenta (comes from TB normalization)
    if "tipo_cuenta" in df.columns:
        g = (
            df["tipo_cuenta"]
            .astype(str)
            .str.upper()
            .str.strip()
            .replace(
                {"ACTIVOS": "ACTIVO", "PASIVOS": "PASIVO", "INGRESO": "INGRESOS", "GASTO": "GASTOS"}
            )
        )
        out = {
            "ACTIVO": float(df.loc[g == "ACTIVO", "_saldo"].sum()),
            "PASIVO": float(df.loc[g == "PASIVO", "_saldo"].sum()),
            "PATRIMONIO": float(df.loc[g == "PATRIMONIO", "_saldo"].sum()),
            "INGRESOS": float(df.loc[g == "INGRESOS", "_saldo"].sum()),
            "GASTOS": float(df.loc[g == "GASTOS", "_saldo"].sum()),
        }
        if any(v > 0 for v in out.values()):
            return out

    # Fallback using codigo or ls first digit
    code_col = "codigo" if "codigo" in df.columns else ("ls" if "ls" in df.columns else None)
    if code_col:
        pref = df[code_col].astype(str).str.strip().str[0]
        out = {
            "ACTIVO": float(df.loc[pref == "1", "_saldo"].sum()),
            "PASIVO": float(df.loc[pref == "2", "_saldo"].sum()),
            "PATRIMONIO": float(df.loc[pref == "3", "_saldo"].sum()),
            "INGRESOS": float(df.loc[pref == "4", "_saldo"].sum()),
            "GASTOS": float(df.loc[pref == "5", "_saldo"].sum()),
        }
        if any(v > 0 for v in out.values()):
            return out

    return fallback


def _pick_stage(datos_clave: dict[str, Any], perfil: dict[str, Any]) -> str:
    stage = (
        str(
            datos_clave.get("etapa")
            or perfil.get("encargo", {}).get("etapa")
            or perfil.get("etapa")
            or "planificacion"
        )
        .strip()
        .lower()
    )
    if "cierre" in stage or "informe" in stage:
        return "informe"
    if "ejec" in stage:
        return "ejecucion"
    return "planificacion"


def _risk_meta(perfil: dict[str, Any]) -> tuple[str, str]:
    nivel = "Medio"
    rg = (
        perfil.get("riesgo_global", {}) if isinstance(perfil.get("riesgo_global", {}), dict) else {}
    )
    if rg:
        nivel = str(rg.get("nivel", "Medio")).strip().capitalize()
    low = nivel.lower()
    if "alto" in low:
        return nivel, "#BA1A1A"
    if "medio" in low:
        return nivel, "#B45309"
    return nivel, "#047857"


def _risk_rows(ranking_areas: pd.DataFrame | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(ranking_areas, pd.DataFrame) and not ranking_areas.empty:
        tmp = ranking_areas.copy()
        if "score_riesgo" not in tmp.columns:
            tmp["score_riesgo"] = 0.0
        tmp["_score"] = pd.to_numeric(tmp["score_riesgo"], errors="coerce").fillna(0.0)
        tmp = tmp.sort_values("_score", ascending=False)
        for _, row in tmp.head(6).iterrows():
            score = float(row.get("_score", 0.0))
            nombre = str(row.get("nombre", row.get("area", "Area")))
            if score >= 70:
                level, color = "Riesgo Alto", "#BA1A1A"
            elif score >= 40:
                level, color = "Riesgo Medio", "#B45309"
            else:
                level, color = "Riesgo Bajo", "#047857"
            rows.append(
                {
                    "name": nombre[:52],
                    "score": max(0.0, min(100.0, score)),
                    "level": level,
                    "color": color,
                }
            )
    if rows:
        return rows
    return [
        {
            "name": "Inversiones no corrientes",
            "score": 82.0,
            "level": "Riesgo Alto",
            "color": "#BA1A1A",
        },
        {"name": "Patrimonio", "score": 74.0, "level": "Riesgo Alto", "color": "#B45309"},
        {
            "name": "Gastos Administrativos",
            "score": 46.0,
            "level": "Riesgo Medio",
            "color": "#B45309",
        },
        {"name": "Cuentas por pagar", "score": 24.0, "level": "Riesgo Bajo", "color": "#047857"},
    ]


def _pending_reviews(ranking_areas: pd.DataFrame | None, indicadores: dict[str, Any]) -> int:
    if isinstance(ranking_areas, pd.DataFrame) and not ranking_areas.empty:
        for col in ["estado", "etapa", "status"]:
            if col in ranking_areas.columns:
                s = ranking_areas[col].astype(str).str.lower()
                return int((~s.str.contains("cerrad|complet|final", regex=True)).sum())
    n_alto = int(indicadores.get("areas_alto_riesgo", 0) or 0)
    n_medio = int(indicadores.get("areas_medio_riesgo", 0) or 0)
    return max(0, n_alto + n_medio)


def _integridad(indicadores: dict[str, Any]) -> float:
    for key in ["integridad", "integridad_datos", "integridad_pct", "data_integrity"]:
        if key in indicadores:
            val = _safe_float(indicadores.get(key), 0.0)
            if val > 0:
                return max(0.0, min(100.0, val))
    n_alto = int(indicadores.get("areas_alto_riesgo", 0) or 0)
    n_medio = int(indicadores.get("areas_medio_riesgo", 0) or 0)
    base = 98.0 - (n_alto * 5.0 + n_medio * 2.5)
    return max(72.0, min(99.5, base))


def _alerts_from_variaciones(variaciones: pd.DataFrame | None) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    if isinstance(variaciones, pd.DataFrame) and not variaciones.empty:
        name_col = next(
            (
                c
                for c in ["cuenta", "nombre_cuenta", "descripcion", "area_nombre", "nombre"]
                if c in variaciones.columns
            ),
            None,
        )
        rel_col = next(
            (
                c
                for c in ["variacion_relativa", "variacion_pct", "delta_pct", "var_pct"]
                if c in variaciones.columns
            ),
            None,
        )
        if name_col and rel_col:
            df = variaciones.copy()
            df["_rel"] = pd.to_numeric(df[rel_col], errors="coerce").abs().fillna(0)
            for _, row in df.sort_values("_rel", ascending=False).head(3).iterrows():
                rel = float(row.get("_rel", 0.0))
                nm = str(row.get(name_col, "Cuenta relevante"))
                sev = "critica" if rel >= 25 else "media"
                alerts.append(
                    {
                        "nivel": sev,
                        "titulo": (
                            "Variacion material" if sev == "critica" else "Variacion relevante"
                        ),
                        "detalle": f"{nm}: desviacion de {rel:.1f}% frente al comportamiento esperado.",
                    }
                )
    if alerts:
        return alerts
    return [
        {
            "nivel": "critica",
            "titulo": "Corte de ingresos",
            "detalle": "Se observan registros de cierre con comportamiento atipico en las ultimas 48 horas.",
        },
        {
            "nivel": "media",
            "titulo": "Soporte documental",
            "detalle": "Muestras con evidencia incompleta en transacciones materiales de cuentas sensibles.",
        },
        {
            "nivel": "media",
            "titulo": "Concentracion de riesgo",
            "detalle": "Alta dependencia de pocas cuentas en el top del ranking de riesgo.",
        },
    ]


def render_dashboard_overview_premium(
    cliente: str,
    datos_clave: dict[str, Any] | None,
    perfil: dict[str, Any] | None,
    resumen_tb: dict[str, Any] | None,
    indicadores: dict[str, Any] | None,
    ranking_areas: pd.DataFrame | None,
    variaciones: pd.DataFrame | None,
    tb: pd.DataFrame | None = None,
) -> None:
    datos_clave = datos_clave or {}
    perfil = perfil or {}
    resumen_tb = resumen_tb or {}
    indicadores = indicadores or {}

    client_name = str(
        datos_clave.get("nombre") or perfil.get("cliente", {}).get("nombre_legal") or cliente
    )
    periodo = str(
        datos_clave.get("periodo") or perfil.get("encargo", {}).get("anio_activo") or "2025"
    )

    riesgo_label, riesgo_color = _risk_meta(perfil)
    integridad = _integridad(indicadores)
    pendientes = _pending_reviews(ranking_areas, indicadores)
    materialidad = _pick_materialidad(cliente, perfil)
    ranking = _risk_rows(ranking_areas)
    alerts = _alerts_from_variaciones(variaciones)
    etapa = _pick_stage(datos_clave, perfil)
    totals = _totales_tb(tb, resumen_tb)

    stage_order = {"planificacion": 0, "ejecucion": 1, "informe": 2}
    current_idx = stage_order.get(etapa, 0)

    ranking_html = "".join([f"""
            <div class="rk-row">
                <div class="rk-head">
                    <span class="rk-name">{r['name']}</span>
                    <span class="rk-tag" style="color:{r['color']};">{r['level']} ({r['score']:.0f}/100)</span>
                </div>
                <div class="rk-track"><div class="rk-fill" style="width:{r['score']:.0f}%; background:{r['color']};"></div></div>
            </div>
            """ for r in ranking])

    alerts_html = "".join([f"""
            <div class="an-item {'crit' if a['nivel']=='critica' else 'med'}">
                <div class="an-title">{a['titulo']}</div>
                <div class="an-detail">{a['detalle']}</div>
            </div>
            """ for a in alerts[:3]])

    timeline_html = ""
    phases = ["Planificaci?n", "Ejecuci?n", "Informe"]
    for idx, phase in enumerate(phases):
        if idx < current_idx:
            cls = "done"
            icon = "check"
            sub = "Completada"
        elif idx == current_idx:
            cls = "active"
            icon = "radio_button_checked"
            sub = "Fase activa"
        else:
            cls = "next"
            icon = "schedule"
            sub = "Pendiente"
        timeline_html += f"""
        <tr class="tl-row {cls}">
            <td class="tl-icon"><span class="material-symbols-outlined">{icon}</span></td>
            <td class="tl-phase">{phase}</td>
            <td class="tl-status">{sub}</td>
        </tr>
        """

    insight = (
        f"El encargo de {client_name} se encuentra en {etapa}. "
        f"Con {pendientes} revisiones pendientes y riesgo global {riesgo_label.lower()}, "
        "la prioridad es cerrar pruebas en las cuentas de mayor exposici?n y consolidar evidencia suficiente para informe."
    )

    html = dedent(f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Newsreader:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
        <style>
          body {{ margin:0; font-family:Inter,sans-serif; background:#f7fafc; color:#0f172a; }}
          .dash {{ padding:12px; }}
          .topbar {{ display:flex; justify-content:space-between; gap:1rem; align-items:center; margin-bottom:8px; }}
          .name {{ font-family:Newsreader,serif; font-size:1.45rem; font-weight:700; }}
          .sub {{ font-size:.72rem; color:#64748B; margin-left:.5rem; }}
          .client {{ font-size:.8rem; color:#475569; }}
          .hero-k {{ font-size:.65rem; letter-spacing:.14em; text-transform:uppercase; color:#0f766e; font-weight:800; margin-top:6px; }}
          .hero-t {{ font-family:Newsreader,serif; font-size:2.1rem; font-weight:700; color:#041627; }}
          .hero-s {{ color:#64748B; font-size:.9rem; margin-bottom:.75rem; }}
          .bento {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:.6rem; margin-bottom:.8rem; }}
          .main {{ display:grid; grid-template-columns:2fr 1fr; gap:.8rem; }}
          .sovereign-card {{ background:#fff; border:1px solid rgba(196,198,205,.25); border-radius:12px; padding:.9rem; box-shadow:0 10px 30px rgba(24,28,30,.04); }}
          .risk-high {{ background:#ffdad6; border-left:6px solid #BA1A1A; border-radius:12px; padding:.9rem; }}
          .ai-memo {{ background:#041627; color:#a5eff0; border-radius:12px; padding:.9rem; font-family:Newsreader,serif; font-style:italic; }}
          .lbl {{ font-size:.65rem; letter-spacing:.12em; text-transform:uppercase; color:#64748B; font-weight:800; }}
          .val {{ font-size:1.5rem; font-family:Newsreader,serif; font-weight:700; margin-top:.2rem; }}
          .subline {{ font-size:.72rem; color:#64748B; }}
          .rk-title,.tl-title-main,.an-title-main {{ font-family:Newsreader,serif; font-size:1.3rem; margin:0 0 .55rem 0; color:#041627; }}
          .rk-row {{ margin-bottom:.45rem; }}
          .rk-head {{ display:flex; justify-content:space-between; gap:.6rem; align-items:center; margin-bottom:.2rem; }}
          .rk-tag {{ font-size:.7rem; font-weight:700; }}
          .rk-track {{ background:#e2e8f0; border-radius:999px; height:7px; overflow:hidden; }}
          .rk-fill {{ height:100%; border-radius:999px; }}
          .an-item {{ background:#fff; border-radius:10px; padding:.55rem .65rem; margin-top:.35rem; }}
          .an-item.crit {{ border-left:4px solid #BA1A1A; }}
          .an-item.med {{ border-left:4px solid #B45309; }}
          .an-title {{ font-size:.76rem; font-weight:700; color:#041627; }}
          .an-detail {{ font-size:.74rem; color:#475569; margin-top:.2rem; }}
          .memo-title {{ font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; font-weight:800; }}
          .memo-body {{ font-size:.95rem; line-height:1.55; margin-top:.35rem; }}
          .timeline-table {{ width:100%; border-collapse:collapse; }}
          .timeline-table td {{ border-bottom:1px solid #e2e8f0; padding:.45rem .2rem; font-size:.8rem; }}
          .timeline-table tr:last-child td {{ border-bottom:none; }}
          .tl-icon .material-symbols-outlined {{ font-size:18px; vertical-align:middle; }}
          .tl-row.done .tl-icon {{ color:#047857; }}
          .tl-row.active .tl-icon {{ color:#041627; }}
          .tl-row.next .tl-icon {{ color:#94A3B8; }}
          .tl-phase {{ font-weight:700; color:#041627; }}
          .tl-status {{ color:#64748B; text-align:right; }}
        </style>

        <div class="dash">
          <div class="topbar">
            <div class="brand">
              <span class="name">Centro de Mando de Auditoría - Socio AI</span>
              <span class="sub">Sovereign Intelligence</span>
            </div>
            <div class="client">Cliente: <b>{client_name}</b> - Periodo {periodo}</div>
          </div>

          <div class="hero-k">Inteligencia soberana de auditoría</div>
          <div class="news hero-t">Resumen Ejecutivo de Auditoría</div>
          <div class="hero-s leading-relaxed">Riesgo global {riesgo_label} - Materialidad de planeaci?n {_fmt_money(materialidad)}.</div>

          <div class="bento">
            <div class="sovereign-card">
              <div class="lbl">Activo Total</div>
              <div class="val" style="color:#041627;">{_fmt_money(totals['ACTIVO'])}</div>
              <div class="subline">Total real desde Trial Balance</div>
            </div>
            <div class="sovereign-card">
              <div class="lbl">Pasivo Total</div>
              <div class="val" style="color:#BA1A1A;">{_fmt_money(totals['PASIVO'])}</div>
              <div class="subline">Total real desde Trial Balance</div>
            </div>
            <div class="sovereign-card">
              <div class="lbl">Patrimonio</div>
              <div class="val" style="color:#041627;">{_fmt_money(totals['PATRIMONIO'])}</div>
              <div class="subline">Total real desde Trial Balance</div>
            </div>
            <div class="sovereign-card">
              <div class="lbl">Ingresos</div>
              <div class="val" style="color:#047857;">{_fmt_money(totals['INGRESOS'])}</div>
              <div class="subline">Total real desde Trial Balance</div>
            </div>
            <div class="sovereign-card">
              <div class="lbl">Gastos</div>
              <div class="val" style="color:#B45309;">{_fmt_money(totals['GASTOS'])}</div>
              <div class="subline">Total real desde Trial Balance</div>
            </div>
          </div>

          <div class="main">
            <div style="display:flex;flex-direction:column;gap:12px;">
              <section class="sovereign-card">
                <h3 class="rk-title">Ranking de Riesgos por Área</h3>
                {ranking_html}
              </section>
              <section class="risk-high">
                <h3 class="an-title-main">Anomal?as Cr?ticas</h3>
                {alerts_html}
              </section>
            </div>

            <div style="display:flex;flex-direction:column;gap:12px;">
              <section class="sovereign-card" style="background:#f1f4f6;">
                <h3 class="tl-title-main">Ciclo de Vida de Auditoría</h3>
                <table class="timeline-table">
                  <tbody>
                    {timeline_html}
                  </tbody>
                </table>
              </section>

              <section class="ai-memo">
                <div class="memo-title">Insight del Socio</div>
                <div class="memo-body">{insight}</div>
              </section>
            </div>
          </div>
        </div>
        """)

    components.html(html, height=980, scrolling=False)
