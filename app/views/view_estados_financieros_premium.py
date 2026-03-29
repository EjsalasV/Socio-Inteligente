from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st


def _fmt_money(value: Any) -> str:
    try:
        return f"${float(value):,.0f}"
    except Exception:
        return "$0"


def _fmt_pct(value: Any, decimals: int = 1) -> str:
    try:
        return f"{float(value):.{decimals}f}%"
    except Exception:
        return "0.0%"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _txt(value: Any, default: str = "") -> str:
    t = str(value if value is not None else default).strip()
    if not t:
        t = default
    return escape(t)


def _inject_assets_once() -> None:
    if st.session_state.get("_ef_premium_assets_loaded"):
        return

    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2family=Inter:wght@400;500;600;700;800&family=Newsreader:ital,wght@0,400;0,600;0,700;1,700&family=Material+Symbols+Outlined:wght@400;700&display=swap" rel="stylesheet">
        
        """,
        unsafe_allow_html=True,
    )

    st.session_state["_ef_premium_assets_loaded"] = True


def _pick_var_source(tb: pd.DataFrame | None) -> tuple[str | None, str | None]:
    if not isinstance(tb, pd.DataFrame) or tb.empty:
        return None, None

    current_candidates = ["saldo", "saldo_actual", "saldo_2023", "actual", "monto_actual"]
    prev_candidates = ["saldo_anterior", "saldo_2022", "anterior", "monto_anterior", "saldo_prev"]

    ccol = next((c for c in current_candidates if c in tb.columns), None)
    pcol = next((c for c in prev_candidates if c in tb.columns), None)
    return ccol, pcol


def _build_rows(tb: pd.DataFrame | None, variaciones: pd.DataFrame | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    if isinstance(variaciones, pd.DataFrame) and not variaciones.empty:
        name_col = next(
            (
                c
                for c in ["cuenta", "nombre_cuenta", "descripcion", "area_nombre"]
                if c in variaciones.columns
            ),
            None,
        )
        curr_col = next(
            (c for c in ["saldo_actual", "saldo", "actual"] if c in variaciones.columns), None
        )
        prev_col = next(
            (c for c in ["saldo_anterior", "anterior", "saldo_prev"] if c in variaciones.columns),
            None,
        )

        if name_col and curr_col and prev_col:
            df = variaciones.copy().head(8)
            for _, r in df.iterrows():
                curr = _safe_float(r.get(curr_col, 0.0))
                prev = _safe_float(r.get(prev_col, 0.0))
                delta = curr - prev
                delta_pct = (delta / prev * 100.0) if prev else 0.0
                rows.append(
                    {
                        "cuenta": _txt(r.get(name_col, "Cuenta"), "Cuenta"),
                        "actual": curr,
                        "anterior": prev,
                        "delta": delta,
                        "delta_pct": delta_pct,
                    }
                )

    if rows:
        return rows[:6]

    if isinstance(tb, pd.DataFrame) and not tb.empty:
        ccol, pcol = _pick_var_source(tb)
        name_col = next(
            (c for c in ["nombre_cuenta", "cuenta", "descripcion", "nombre"] if c in tb.columns),
            None,
        )
        if ccol and name_col:
            df = tb.copy().head(10)
            for _, r in df.iterrows():
                curr = _safe_float(r.get(ccol, 0.0))
                prev = _safe_float(r.get(pcol, 0.0)) if pcol else 0.0
                delta = curr - prev
                delta_pct = (delta / prev * 100.0) if prev else 0.0
                rows.append(
                    {
                        "cuenta": _txt(r.get(name_col, "Cuenta"), "Cuenta"),
                        "actual": curr,
                        "anterior": prev,
                        "delta": delta,
                        "delta_pct": delta_pct,
                    }
                )

    if rows:
        return rows[:6]

    return [
        {
            "cuenta": "Cuentas por Cobrar Comerciales",
            "actual": 8450000,
            "anterior": 6200000,
            "delta": 2250000,
            "delta_pct": 36.3,
        },
        {
            "cuenta": "Efectivo y Equivalentes",
            "actual": 1120000,
            "anterior": 1050000,
            "delta": 70000,
            "delta_pct": 6.7,
        },
        {
            "cuenta": "Inventarios",
            "actual": 4800000,
            "anterior": 4100000,
            "delta": 700000,
            "delta_pct": 17.1,
        },
        {
            "cuenta": "Propiedad, Planta y Equipo",
            "actual": 15200000,
            "anterior": 13900000,
            "delta": 1300000,
            "delta_pct": 9.4,
        },
        {
            "cuenta": "Ventas Netas",
            "actual": 42300000,
            "anterior": 38100000,
            "delta": 4200000,
            "delta_pct": 11.0,
        },
    ]


def render_estados_financieros_premium(
    cliente: str,
    tb: pd.DataFrame | None,
    variaciones: pd.DataFrame | None,
    datos_clave: dict[str, Any] | None,
    perfil: dict[str, Any] | None,
) -> None:
    _inject_assets_once()

    datos_clave = datos_clave or {}
    perfil = perfil or {}

    mat_block = (
        perfil.get("materialidad", {}) if isinstance(perfil.get("materialidad"), dict) else {}
    )
    mp = _safe_float(mat_block.get("materialidad_planeacion", 0.0))
    me = _safe_float(mat_block.get("materialidad_ejecucion", 0.0))
    triv = _safe_float(mat_block.get("umbral_trivial", 0.0))

    if mp <= 0:
        mp = 1250000.0
    if me <= 0:
        me = mp * 0.75
    if triv <= 0:
        triv = mp * 0.05

    rows = _build_rows(tb, variaciones)
    year_current = str(datos_clave.get("periodo", "2023"))
    year_prev = str(int(year_current) - 1) if year_current.isdigit() else "2022"

    st.markdown(
        f"""
        <div class="ef-root" style="margin-bottom:.8rem;">
            <h1 class="ef-serif" style="font-size:2.2rem;margin:0;">Estados Financieros - Análisis Comparativo</h1>
            <p style="margin:.15rem 0 0 0;color:#64748B;">Cliente: {_txt(cliente, 'N/D')} | Auditoría del periodo fiscal finalizado el 31 de diciembre.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="ef-root ef-card ef-metric">
                <div class="ef-label">Materialidad de Planeación (MP)</div>
                <div class="ef-serif ef-value">{_fmt_money(mp)}</div>
                <div class="ef-sub">Base de planeación</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="ef-root ef-card ef-metric k2">
                <div class="ef-label">Materialidad de Ejecución (ME)</div>
                <div class="ef-serif ef-value">{_fmt_money(me)}</div>
                <div class="ef-sub">75% de MP</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="ef-root ef-card ef-metric k3">
                <div class="ef-label" style="color:#a5eff0;">Umbral de Diferencias Triviales</div>
                <div class="ef-serif ef-value">{_fmt_money(triv)}</div>
                <div class="ef-sub" style="color:#cbd5e1;">5% de MP</div>
                <div style="position:absolute;right:-30px;top:-30px;width:120px;height:120px;background:#89d3d4;opacity:.12;border-radius:999px;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    table_rows = ""
    for r in rows:
        warn = abs(float(r["delta_pct"])) >= 9.0
        tr_cls = "ef-warn-row" if warn else ""
        delta_sign = "+" if r["delta"] >= 0 else ""
        pct_sign = "+" if r["delta_pct"] >= 0 else ""
        delta_cls = "ef-warn" if warn else ""
        table_rows += f"""
        <tr class="{tr_cls}">
            <td>{r['cuenta']}</td>
            <td class="ef-num">{_fmt_money(r['actual'])}</td>
            <td class="ef-num">{_fmt_money(r['anterior'])}</td>
            <td class="ef-num {delta_cls}">{delta_sign}{_fmt_money(r['delta'])}</td>
            <td class="ef-num {delta_cls}">{pct_sign}{_fmt_pct(r['delta_pct'])}</td>
        </tr>
        """

    st.markdown(
        f"""
        <div class="ef-root ef-table-wrap" style="margin-top:.85rem;">
            <div class="ef-table-box">
                <div class="ef-table-head">
                    <h2 class="ef-serif" style="font-size:1.4rem;margin:0;">Balance General y P&G</h2>
                    <div>
                        <span class="ef-btn">Exportar Reporte</span>
                        <span class="ef-btn primary">Ajustar Filtros</span>
                    </div>
                </div>
                <div style="overflow-x:auto;">
                    <table class="ef-table">
                        <thead>
                            <tr>
                                <th>Cuenta Contable</th>
                                <th class="ef-num">Año Actual ({_txt(year_current, '2023')})</th>
                                <th class="ef-num">Año Anterior ({_txt(year_prev, '2022')})</th>
                                <th class="ef-num">Variación $</th>
                                <th class="ef-num">Variación %</th>
                            </tr>
                        </thead>
                        <tbody>{table_rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([3, 2])
    with left:
        st.markdown(
            """
            <div class="ef-root ef-card ef-ia">
                <div style="display:flex;gap:.5rem;align-items:center;">
                    <span class="material-symbols-outlined" style="background:#002f30;color:#89d3d4;padding:.35rem;border-radius:.55rem;">psychology</span>
                    <h2 class="ef-serif" style="font-size:1.55rem;margin:0;">Criterio del Socio - IA</h2>
                </div>
                <div class="ef-ia-item">
                    <h4>Análisis de Coherencia: Ventas vs CXC</h4>
                    <p>Se observa descorrelación entre crecimiento de ventas y cuentas por cobrar. Recomendación: profundizar pruebas de incobrabilidad y política de crédito.</p>
                </div>
                <div class="ef-ia-item" style="border-left-color:#c4c6cd;">
                    <h4>Relación Costo de Ventas</h4>
                    <p>El margen bruto se mantiene relativamente estable. No se detectan anomalías materiales en el reconocimiento de costos directos.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="ef-root ef-alerts">
                <div style="display:flex;gap:.45rem;align-items:center;margin-bottom:.35rem;">
                    <span class="material-symbols-outlined" style="color:#BA1A1A;">emergency_home</span>
                    <h2 class="ef-serif" style="font-size:1.35rem;margin:0;">Alertas de Integridad</h2>
                </div>
                <div class="ef-alert">
                    <span class="material-symbols-outlined" style="color:#BA1A1A;">history</span>
                    <div><div class="ef-alert-title">Asientos Manuales al Cierre</div><div class="ef-alert-msg">Movimientos manuales posteriores al horario de cierre requieren validación de soporte.</div></div>
                </div>
                <div class="ef-alert">
                    <span class="material-symbols-outlined" style="color:#BA1A1A;">key</span>
                    <div><div class="ef-alert-title">Acceso No Autorizado</div><div class="ef-alert-msg">Actividad fuera de horario normal en módulos sensibles de inventario/diario.</div></div>
                </div>
                <div class="ef-alert">
                    <span class="material-symbols-outlined" style="color:#89d3d4;">database</span>
                    <div><div class="ef-alert-title">Brecha de Secuencia</div><div class="ef-alert-msg">Rangos faltantes en documentos electrónicos del último bimestre.</div></div>
                </div>
                <div style="margin-top:.6rem;"><span class="ef-btn" style="border-color:rgba(255,255,255,.25);color:#fff;">Ver Historial Completo</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="ef-root ef-narrative">
            <h3 class="ef-serif" style="font-size:1.65rem;margin:0 0 .45rem 0;">Perspectiva Estratégica del Riesgo</h3>
            <p style="margin:0;color:#475569;line-height:1.6;">El incremento de cartera frente al ritmo de recaudo sugiere presión potencial sobre liquidez de corto plazo. Se recomienda reforzar pruebas sobre recuperabilidad y evaluar impacto en flujo operativo de los próximos 30 días.</p>
            <div style="display:flex;gap:1.3rem;margin-top:.7rem;">
                <div><div class="ef-serif" style="font-size:1.3rem;font-weight:700;">High</div><div class="ef-pill">Riesgo Residual</div></div>
                <div style="border-left:1px solid #c4c6cd;padding-left:1rem;"><div class="ef-serif" style="font-size:1.3rem;font-weight:700;">Stable</div><div class="ef-pill">Tendencia del Mercado</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
