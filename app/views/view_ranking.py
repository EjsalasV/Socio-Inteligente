from __future__ import annotations

from typing import Any
from html import escape
import re

import pandas as pd
import streamlit as st
from app.utils.theme_engine import render_editorial_table

try:
    from domain.services.area_briefing import top_cuentas_significativas
except Exception:
    top_cuentas_significativas = None

try:
    from infra.repositories.catalogo_repository import obtener_area_por_codigo
except Exception:
    obtener_area_por_codigo = None


def safe_call(func: Any, *args: Any, default: Any = None, **kwargs: Any) -> Any:
    if func is None:
        return default
    try:
        return func(*args, **kwargs)
    except Exception:
        return default


def fmt_num(value: Any, decimals: int = 2) -> str:
    try:
        return f"{float(value):,.{decimals}f}"
    except Exception:
        return "0.00"


def fmt_money(value: Any) -> str:
    try:
        v = float(value)
        if v < 0:
            return f"(${abs(v):,.2f})"
        return f"${v:,.2f}"
    except Exception:
        return "$0.00"


def _money_cell(value: Any) -> str:
    try:
        v = float(value)
    except Exception:
        v = 0.0
    color = "#BA1A1A" if v < 0 else "#1E293B"
    return f"<span style='color:{color};font-variant-numeric:tabular-nums;'>{fmt_money(v)}</span>"


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _is_level1_row(numero: str, nombre: str) -> bool:
    n = normalize_text(nombre).lower()
    code = normalize_text(numero)
    roots = {"1", "2", "3", "4", "5", "6", "7", "8", "9"}
    l1_names = {"activo", "pasivo", "patrimonio", "ingresos", "gastos", "costos"}
    return (code in roots) or (n in l1_names)


def render_trial_balance_editorial(
    tb: pd.DataFrame | None,
    materialidad_ejecucion: float,
) -> None:
    st.markdown("<div class='section-header'>Trial Balance Editorial</div>", unsafe_allow_html=True)

    if not isinstance(tb, pd.DataFrame) or tb.empty:
        st.error("No se pudo cargar el trial balance.")
        return

    tb_filtrado = tb.copy()
    if "tipo_cuenta" in tb_filtrado.columns:
        tipos = sorted([str(x) for x in tb_filtrado["tipo_cuenta"].dropna().unique()])
        if tipos:
            sel_tipos = st.multiselect(
                "Filtrar por tipo", options=tipos, default=tipos, key="tb_editorial_tipos"
            )
            if sel_tipos:
                tb_filtrado = tb_filtrado[tb_filtrado["tipo_cuenta"].astype(str).isin(sel_tipos)]

    numero_col = next(
        (c for c in ["numero_cuenta", "codigo", "cuenta"] if c in tb_filtrado.columns), None
    )
    nombre_col = next(
        (c for c in ["nombre_cuenta", "nombre", "descripcion"] if c in tb_filtrado.columns), None
    )
    saldo_col = next(
        (c for c in ["saldo_actual", "saldo_2025", "saldo"] if c in tb_filtrado.columns), None
    )
    saldo_ant_col = next(
        (c for c in ["saldo_anterior", "saldo_2024"] if c in tb_filtrado.columns), None
    )
    ls_col = next((c for c in ["ls", "L/S", "l/s", "l_s"] if c in tb_filtrado.columns), None)

    if not saldo_col:
        st.warning("No se encontró una columna de saldo para construir la vista editorial.")
        return

    if not numero_col:
        tb_filtrado["numero_cuenta"] = ""
        numero_col = "numero_cuenta"
    if not nombre_col:
        tb_filtrado["nombre_cuenta"] = ""
        nombre_col = "nombre_cuenta"

    tb_filtrado[saldo_col] = pd.to_numeric(tb_filtrado[saldo_col], errors="coerce").fillna(0.0)
    if saldo_ant_col:
        tb_filtrado[saldo_ant_col] = pd.to_numeric(
            tb_filtrado[saldo_ant_col], errors="coerce"
        ).fillna(0.0)
    else:
        tb_filtrado["_saldo_anterior_tmp"] = 0.0
        saldo_ant_col = "_saldo_anterior_tmp"

    tb_filtrado["_var_abs"] = tb_filtrado[saldo_col] - tb_filtrado[saldo_ant_col]
    tb_filtrado["_var_pct"] = tb_filtrado.apply(
        lambda r: (
            ((r["_var_abs"] / r[saldo_ant_col]) * 100.0)
            if float(r[saldo_ant_col]) not in (0.0, -0.0)
            else 0.0
        ),
        axis=1,
    )

    show = tb_filtrado.copy()
    if ls_col:
        show = show.sort_values(by=[ls_col, numero_col], na_position="last")
    else:
        show = show.sort_values(by=[numero_col], na_position="last")

    max_rows = 350
    if len(show) > max_rows:
        st.caption(f"Mostrando primeras {max_rows} filas de {len(show)}.")
        show = show.head(max_rows)

    rows_html: list[str] = []
    for _, row in show.iterrows():
        numero = normalize_text(row.get(numero_col, ""))
        nombre = normalize_text(row.get(nombre_col, ""))
        ls_txt = normalize_text(row.get(ls_col, "")) if ls_col else ""
        saldo = float(row.get(saldo_col, 0) or 0)
        var_abs = float(row.get("_var_abs", 0) or 0)
        var_pct = float(row.get("_var_pct", 0) or 0)
        high_var = abs(var_abs) > float(materialidad_ejecucion or 0)
        l1 = _is_level1_row(numero, nombre)
        name_cls = "tb-l1-name" if l1 else "tb-detail-name"
        var_cls = "tb-var-high" if high_var else "tb-var-norm"
        icon = "   -" if high_var else ""
        name_render = f"{escape(nombre)}{icon}"

        rows_html.append(f"""
            <tr class="tb-row">
              <td>{escape(numero)}</td>
              <td class="{name_cls}">{name_render}</td>
              <td>{escape(ls_txt)}</td>
              <td style="text-align:right;">{_money_cell(saldo)}</td>
              <td style="text-align:right;">{_money_cell(var_abs)}</td>
              <td style="text-align:right;" class="{var_cls}">{var_pct:,.1f}%</td>
            </tr>
            """)

    table_html = f"""
    <div class="tb-shell grid-cols-1">
      <div class="tb-card">
        <div style="max-height:560px;overflow:auto;">
          <table class="tb-table">
            <thead>
              <tr>
                <th>Cuenta</th>
                <th>Nombre</th>
                <th>L/S</th>
                <th style="text-align:right;">Saldo</th>
                <th style="text-align:right;">Variación $</th>
                <th style="text-align:right;">Variación %</th>
              </tr>
            </thead>
            <tbody>
              {''.join(rows_html)}
            </tbody>
          </table>
        </div>
      </div>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)

    cc1, cc2, cc3 = st.columns(3)
    vals = pd.to_numeric(tb_filtrado[saldo_col], errors="coerce").fillna(0)
    cc1.metric("Cuentas", len(tb_filtrado))
    cc2.metric("Suma", fmt_money(vals.sum()))
    cc3.metric("Mayor saldo", fmt_money(vals.max()))


def _as_float_safe(v: Any) -> float:
    try:
        return float(v or 0)
    except Exception:
        return 0.0


def _detect_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def render_variaciones_editorial(
    variaciones: pd.DataFrame | None,
    materialidad_ejecucion: float,
    sector: str = "",
) -> None:
    st.markdown(
        "<div class='section-header'>Variaciones Significativas</div>", unsafe_allow_html=True
    )

    if not isinstance(variaciones, pd.DataFrame) or variaciones.empty:
        st.info("Sin variaciones significativas detectadas.")
        return

    dfv = variaciones.copy()
    cod_col = _detect_column(dfv, ["codigo", "numero_cuenta", "cuenta"])
    nom_col = _detect_column(dfv, ["nombre", "nombre_cuenta", "descripcion"])
    saldo_col = _detect_column(dfv, ["saldo", "saldo_actual"])
    imp_col = _detect_column(dfv, ["impacto", "variacion_absoluta", "variacion", "delta"])
    pct_col = _detect_column(dfv, ["variacion_pct", "porcentaje", "pct", "impacto_pct"])

    if imp_col is None:
        st.warning("No se encontró una columna de impacto/variación en el DataFrame.")
        return

    for c in [imp_col, saldo_col, pct_col]:
        if c and c in dfv.columns:
            dfv[c] = pd.to_numeric(dfv[c], errors="coerce").fillna(0.0)

    if pct_col is None:
        base_col = saldo_col if saldo_col else imp_col
        dfv["_pct_tmp"] = dfv.apply(
            lambda r: (
                ((_as_float_safe(r.get(imp_col, 0)) / _as_float_safe(r.get(base_col, 0))) * 100.0)
                if _as_float_safe(r.get(base_col, 0)) not in (0.0, -0.0)
                else 0.0
            ),
            axis=1,
        )
        pct_col = "_pct_tmp"

    dfv["_abs_imp"] = dfv[imp_col].abs()
    dfv = dfv.sort_values(by="_abs_imp", ascending=False).head(24)

    c_main, c_side = st.columns([3, 1], gap="large")
    with c_main:
        for _, r in dfv.iterrows():
            codigo = normalize_text(r.get(cod_col, "")) if cod_col else ""
            nombre = normalize_text(r.get(nom_col, "Cuenta")) if nom_col else "Cuenta"
            impacto = _as_float_safe(r.get(imp_col, 0))
            pct = _as_float_safe(r.get(pct_col, 0))
            over_me = abs(impacto) > float(materialidad_ejecucion or 0)
            pct_color = "#ba1a1a" if over_me else "#475569"
            marker = "   -" if over_me else ""

            st.markdown(
                f"""
                <div class="sovereign-card leading-relaxed" style="margin:0 0 .5rem 0;">
                  <div style="display:flex;justify-content:space-between;gap:.7rem;align-items:center;">
                    <div style="min-width:0;">
                      <div class="tb-detail-name" style="font-weight:700;color:#041627;">
                        {escape(codigo)} {escape(nombre)}{marker}
                      </div>
                      <div style="font-size:.77rem;color:#64748B;margin-top:.18rem;">
                        Impacto: <b>{fmt_money(impacto)}</b>
                      </div>
                    </div>
                    <div style="text-align:right;">
                      <div style="font-size:1rem;font-weight:800;color:{pct_color};">{pct:,.1f}%</div>
                      <div style="font-size:.72rem;color:#64748B;">Variación</div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with c_side:
        sec = normalize_text(sector).lower()
        if "holding" in sec:
            perspectiva = (
                "La dispersin de variaciones suele concentrarse en inversiones y patrimonio. "
                "Priorizamos consistencia de método de participacin y revelacin de vinculadas."
            )
        elif "funer" in sec:
            perspectiva = (
                "El negocio funerario puede mostrar estacionalidad y anticipo de servicios. "
                "Las variaciones altas deben contrastarse con devengo y corte de ingresos."
            )
        else:
            perspectiva = (
                "Las variaciones elevadas deben validarse contra el ciclo operativo del sector, "
                "control interno y evidencia de cierre para evitar sesgos de reconocimiento."
            )
        st.markdown(
            f"""
            <div class="ai-memo leading-relaxed">
              <div style="font-size:.62rem;letter-spacing:.16em;text-transform:uppercase;font-weight:800;opacity:.9;">
                Perspectiva Estratégica
              </div>
              <div style="font-size:1.22rem;font-weight:700;margin:.2rem 0 .4rem 0;">
                Lectura IA por Sector
              </div>
              <div style="font-size:.95rem;line-height:1.55;">
                {escape(perspectiva)}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_mayor_critico_editorial(
    df_mayor: pd.DataFrame | None,
    materialidad_ejecucion: float,
    selected_area_code: str = "",
) -> None:
    st.markdown(
        "<div class='section-header'>Análisis de Transacciones Críticas</div>",
        unsafe_allow_html=True,
    )

    if df_mayor is None or (isinstance(df_mayor, pd.DataFrame) and df_mayor.empty):
        st.info("No se encontró mayor.xlsx para este cliente.")
        return

    df_view = df_mayor.copy()
    f1, f2, f3, f4 = st.columns([1, 1, 2, 1])
    with f1:
        filtro_ls = st.text_input(
            "Área L/S", value=selected_area_code or "", key="m_ls_editorial", placeholder="ej. 14"
        )
    with f2:
        filtro_cuenta = st.text_input(
            "Cdigo cuenta", key="m_cuenta_editorial", placeholder="ej. 1.02"
        )
    with f3:
        filtro_texto = st.text_input("Buscar", key="m_texto_editorial", placeholder="ej. ajuste")
    with f4:
        filtro_monto = st.number_input(
            "Monto mínimo", min_value=0.0, value=0.0, step=100.0, key="m_monto_editorial"
        )

    if filtro_ls.strip() and "ls" in df_view.columns:
        df_view = df_view[df_view["ls"].astype(str).str.strip() == filtro_ls.strip()]
    if filtro_cuenta.strip() and "numero_cuenta" in df_view.columns:
        df_view = df_view[
            df_view["numero_cuenta"].astype(str).str.startswith(filtro_cuenta.strip())
        ]
    if filtro_texto.strip():
        q = filtro_texto.strip().lower()
        for c in ["descripcion", "referencia", "nombre_cuenta"]:
            if c in df_view.columns:
                df_view[f"_q_{c}"] = df_view[c].astype(str).str.lower().str.contains(q, na=False)
        q_cols = [c for c in df_view.columns if c.startswith("_q_")]
        if q_cols:
            mask = df_view[q_cols].any(axis=1)
            df_view = df_view[mask]
            df_view = df_view.drop(columns=q_cols, errors="ignore")

    if filtro_monto > 0:
        debe = pd.to_numeric(df_view.get("debe", 0), errors="coerce").fillna(0).abs()
        haber = pd.to_numeric(df_view.get("haber", 0), errors="coerce").fillna(0).abs()
        saldo = pd.to_numeric(df_view.get("saldo", 0), errors="coerce").fillna(0).abs()
        df_view = df_view[
            (debe >= filtro_monto) | (haber >= filtro_monto) | (saldo >= filtro_monto)
        ]

    risk_words = re.compile(r"(ajuste|correcci[o3]n|reverso)", flags=re.IGNORECASE)

    def _after_hours(v: Any) -> bool:
        if v is None:
            return False
        try:
            dt = pd.to_datetime(v, errors="coerce")
            if pd.isna(dt):
                return False
            if isinstance(dt, pd.Timestamp):
                h = dt.hour
                return h >= 19 or h < 7
        except Exception:
            return False
        return False

    def _risk_desc(row: pd.Series) -> bool:
        txt = " ".join(
            [
                str(row.get("descripcion", "")),
                str(row.get("referencia", "")),
            ]
        ).strip()
        return bool(risk_words.search(txt))

    def _over_me(row: pd.Series) -> bool:
        debe = abs(_as_float_safe(row.get("debe", 0)))
        haber = abs(_as_float_safe(row.get("haber", 0)))
        saldo = abs(_as_float_safe(row.get("saldo", 0)))
        return max(debe, haber, saldo) > float(materialidad_ejecucion or 0)

    df_view["_risk_time"] = (
        df_view.apply(lambda r: _after_hours(r.get("fecha")), axis=1)
        if "fecha" in df_view.columns
        else False
    )
    df_view["_risk_desc"] = df_view.apply(_risk_desc, axis=1)
    df_view["_risk_me"] = df_view.apply(_over_me, axis=1)
    df_view["_risk_any"] = df_view[["_risk_time", "_risk_desc", "_risk_me"]].any(axis=1)

    crit = df_view[df_view["_risk_any"]].copy()
    base = df_view[~df_view["_risk_any"]].copy()
    ordered = pd.concat([crit, base], axis=0).head(320)

    st.caption(f"Mostrando {len(ordered)} de {len(df_view)} transacciones.")

    rows_html: list[str] = []
    for _, row in ordered.iterrows():
        rc = bool(row.get("_risk_any", False))
        risk_lbl = []
        if bool(row.get("_risk_time", False)):
            risk_lbl.append("Nocturno")
        if bool(row.get("_risk_desc", False)):
            risk_lbl.append("Palabra clave")
        if bool(row.get("_risk_me", False)):
            risk_lbl.append("> ME")
        flags = " | ".join(risk_lbl) if risk_lbl else "Normal"
        tr_style = "background:#ffefef;" if rc else ""
        risk_color = "#ba1a1a" if rc else "#475569"

        fecha_txt = ""
        if "fecha" in row.index:
            try:
                _d = pd.to_datetime(row.get("fecha"), errors="coerce")
                fecha_txt = (
                    _d.strftime("%Y-%m-%d %H:%M")
                    if not pd.isna(_d)
                    else str(row.get("fecha", ""))[:16]
                )
            except Exception:
                fecha_txt = str(row.get("fecha", ""))[:16]

        rows_html.append(f"""
            <tr class="tb-row" style="{tr_style}">
              <td>{escape(fecha_txt)}</td>
              <td>{escape(normalize_text(row.get("numero_cuenta", "")))}</td>
              <td class="tb-detail-name">{escape(normalize_text(row.get("descripcion", ""))[:90])}</td>
              <td style="text-align:right;">{_money_cell(_as_float_safe(row.get("debe", 0)))}</td>
              <td style="text-align:right;">{_money_cell(_as_float_safe(row.get("haber", 0)))}</td>
              <td style="color:{risk_color};font-weight:700;">{escape(flags)}</td>
            </tr>
            """)

    st.markdown(
        f"""
        <div class="tb-shell">
          <div class="tb-card">
            <div style="max-height:560px;overflow:auto;">
              <table class="tb-table">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Cuenta</th>
                    <th>Descripcin</th>
                    <th style="text-align:right;">Debe</th>
                    <th style="text-align:right;">Haber</th>
                    <th>Señal crítica</th>
                  </tr>
                </thead>
                <tbody>{''.join(rows_html)}</tbody>
              </table>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_contexto_tab(ws: dict[str, Any]) -> None:
    area_df = ws["area_df"]

    st.markdown("**Top cuentas principales del area**")
    top_df = safe_call(top_cuentas_significativas, area_df, 8, default=pd.DataFrame())
    if top_df is None or top_df.empty:
        top_df = area_df.head(8) if isinstance(area_df, pd.DataFrame) else pd.DataFrame()

    if top_df is not None and not top_df.empty:
        cols = [
            c
            for c in ["numero_cuenta", "nombre_cuenta", "saldo_actual", "variacion_absoluta"]
            if c in top_df.columns
        ]
        if cols:
            show = top_df[cols].copy()
            if "saldo_actual" in show.columns:
                show["saldo_actual"] = show["saldo_actual"].apply(fmt_money)
            if "variacion_absoluta" in show.columns:
                show["variacion_absoluta"] = show["variacion_absoluta"].apply(fmt_money)
            render_editorial_table(show)
        else:
            render_editorial_table(top_df.head(8))
    else:
        st.info("No hay cuentas principales disponibles para esta area.")

    st.markdown("**Objetivo del area**")
    if ws["focos"]:
        st.markdown(str(ws["focos"][0]))
    else:
        st.markdown("Objetivo no disponible. Revisar mapeo de area y reglas de negocio.")

    st.markdown("**Riesgos del area**")
    if ws["riesgos"]:
        for r in ws["riesgos"]:
            st.markdown(
                f"- [{normalize_text(r.get('nivel', 'N/A'))}] {normalize_text(r.get('titulo', ''))}: {normalize_text(r.get('descripcion', ''))}"
            )
    else:
        st.info("No se detectaron riesgos del motor base para esta area.")

    riesgos = (
        ws.get("riesgos_automaticos", [])
        if isinstance(ws.get("riesgos_automaticos", []), list)
        else []
    )
    st.subheader("Riesgos automaticos")
    if riesgos:
        for r in riesgos:
            nivel = normalize_text(r.get("nivel", ""))
            color = {"ALTO": "RED", "MEDIO": "ORANGE", "BAJO": "GREEN"}.get(nivel.upper(), "GRAY")
            st.markdown(
                f"- `{color}` **{normalize_text(r.get('tipo', 'RIESGO'))} ({nivel.upper() or 'N/A'})**  \n"
                f"  - {normalize_text(r.get('descripcion', 'Sin descripcion'))}  \n"
                f"  - Accion: {normalize_text(r.get('accion_sugerida', 'Sin accion sugerida'))}"
            )
    else:
        st.success("No se detectaron riesgos automáticos para esta área.")

    st.markdown("**Aseveraciones esperadas**")
    esperadas = ws["cobertura"].get("esperadas", [])
    if esperadas:
        st.markdown(", ".join(esperadas))
    else:
        st.info("No existe mapeo de aseveraciones esperadas para esta area.")

    st.markdown("**Alertas contextuales**")
    alertas = []
    if ws["hallazgos_count"] > 0:
        alertas.append(f"Hay {ws['hallazgos_count']} hallazgo(s) abierto(s).")
    if ws["pending_count"] > 0:
        alertas.append(f"Hay {ws['pending_count']} procedimiento(s) pendiente(s).")
    if ws["coverage"] < 60:
        alertas.append("Cobertura menor al 60%.")

    if alertas:
        for a in alertas:
            st.warning(a)
    else:
        st.success("Sin alertas contextuales relevantes.")


def render_briefing_tab(ws: dict[str, Any]) -> None:
    st.markdown("**Briefing ejecutivo del area**")
    st.markdown(str(ws["lectura"]))

    st.markdown("**Resumen practico**")
    s = ws["area_summary"]
    st.markdown(
        f"Cuentas: {int(s.get('cuentas', 0) or 0)} | "
        f"Saldo actual: {fmt_money(s.get('saldo_actual', 0))} | "
        f"Variacion acumulada: {fmt_money(s.get('variacion_acumulada', 0))}"
    )

    st.markdown("**Foco de auditoria**")
    if ws["focos"]:
        for foco in ws["focos"]:
            st.markdown(f"- {foco}")
    else:
        st.info("No hay foco de auditoria definido para esta area.")

    if ws.get("es_holding"):
        st.markdown("**Foco holding**")
        foco_holding = (
            ws.get("foco_holding", []) if isinstance(ws.get("foco_holding", []), list) else []
        )
        if foco_holding:
            for foco in foco_holding:
                st.markdown(f"- {foco}")
        else:
            st.info("Sin foco holding específico para esta area.")

    st.markdown("**Why this area matters**")
    if ws["coverage"] < 80 or ws["hallazgos_count"] > 0:
        st.markdown(
            "Esta area importa porque puede concentrar riesgo residual por cobertura parcial y/o hallazgos abiertos."
        )
    else:
        st.markdown(
            "Esta area importa por su relevancia en el cierre, aun con cobertura favorable."
        )


def render_procedimientos_tab(ws: dict[str, Any]) -> None:
    st.markdown("**Procedimientos del area**")
    proc_df = ws["proc_df"].copy()

    if proc_df.empty:
        st.info("No existen procedimientos cargados para esta area.")
        return

    if "id" not in proc_df.columns:
        proc_df["id"] = ""
    if "descripcion" not in proc_df.columns:
        proc_df["descripcion"] = ""
    if "estado" not in proc_df.columns:
        proc_df["estado"] = "planificado"

    proc_df["estado"] = proc_df["estado"].astype(str).str.lower()

    estado_labels = {
        "ejecutado": "Ejecutado",
        "completado": "Completado",
        "cerrado": "Cerrado",
        "en_proceso": "En proceso",
        "planificado": "Planificado",
        "pendiente": "Pendiente",
        "no_aplicable": "No aplicable",
        "no_aplica": "No aplica",
    }
    proc_df["estado_legible"] = proc_df["estado"].map(estado_labels).fillna(proc_df["estado"])

    resumen = proc_df["estado_legible"].value_counts().to_dict()
    resumen_txt = " | ".join([f"{k}: {v}" for k, v in resumen.items()])
    st.caption(f"Resumen estados: {resumen_txt}")
    st.caption(f"Pendientes: {ws['pending_count']}")

    view_df = proc_df[["id", "descripcion", "estado_legible"]].rename(
        columns={"id": "ID", "descripcion": "Procedimiento", "estado_legible": "Estado"}
    )

    render_editorial_table(view_df)


def render_cobertura_tab(ws: dict[str, Any]) -> None:
    cobertura = ws["cobertura"]
    codigo_ls = normalize_text(ws.get("codigo_ls", ""))
    area_oficial = safe_call(obtener_area_por_codigo, codigo_ls, default=None)
    titulo_ls = (
        normalize_text(area_oficial.get("titulo", "")) if isinstance(area_oficial, dict) else ""
    )
    calidad = (
        ws.get("calidad_metodologia", {})
        if isinstance(ws.get("calidad_metodologia", {}), dict)
        else {}
    )
    guia_det = (
        calidad.get("aseveraciones_guia_detalle", {})
        if isinstance(calidad.get("aseveraciones_guia_detalle", {}), dict)
        else {}
    )
    guia_ls = (
        guia_det.get("aseveraciones_sugeridas", [])
        if isinstance(guia_det.get("aseveraciones_sugeridas", []), list)
        else []
    )
    guia_nota = normalize_text(guia_det.get("nota", "")) or "Guia referencial, no exhaustiva."

    st.markdown("**Resumen de cobertura**")
    c1, c2, c3 = st.columns(3)
    c1.metric("Cobertura", f"{fmt_num(cobertura.get('cobertura_porcentaje', 0), 1)}%")
    c2.metric("Aseveraciones cubiertas", len(cobertura.get("cubiertas", [])))
    c3.metric("Aseveraciones no cubiertas", len(cobertura.get("no_cubiertas", [])))

    if codigo_ls:
        st.caption(f"LS {codigo_ls} - {titulo_ls or ws.get('area_name', 'Sin título oficial')}")

    st.markdown("**Aseveraciones esperadas**")
    st.markdown(", ".join(cobertura.get("esperadas", [])) or "Sin datos")

    st.markdown("**Aseveraciones guía sugeridas (referencial)**")
    if guia_ls:
        st.markdown(", ".join([str(x) for x in guia_ls]))
    else:
        st.info("Sin guía específica disponible")
    st.caption(
        "Esta guía es referencial y puede complementarse segon el juicio profesional y la naturaleza del saldo."
    )
    if guia_nota and guia_nota.lower() != "guia referencial, no exhaustiva.":
        st.caption(guia_nota)

    st.markdown("**Aseveraciones cubiertas**")
    st.markdown(", ".join(cobertura.get("cubiertas", [])) or "Sin cobertura fuerte")

    st.markdown("**Aseveraciones debiles**")
    st.markdown(", ".join(cobertura.get("debiles", [])) or "Sin aseveraciones debiles")

    st.markdown("**Aseveraciones no cubiertas**")
    st.markdown(", ".join(cobertura.get("no_cubiertas", [])) or "Sin aseveraciones no cubiertas")

    st.markdown("**Conclusion**")
    conclusion = normalize_text(cobertura.get("conclusion", "sin_mapeo")) or "sin_mapeo"
    if conclusion == "completa":
        st.success("Cobertura completa")
    elif conclusion == "con_reservas":
        st.warning("Cobertura con reservas")
    elif conclusion == "incompleta":
        st.error("Cobertura incompleta")
    else:
        st.info("Cobertura sin mapeo")


def render_hallazgos_tab(ws: dict[str, Any]) -> None:
    st.markdown("**Hallazgos abiertos**")
    hallazgos = ws["hallazgos"]

    if not hallazgos:
        st.info("No existen hallazgos abiertos para esta area.")
        return

    for idx, h in enumerate(hallazgos, start=1):
        st.markdown(f"{idx}. {h}")
