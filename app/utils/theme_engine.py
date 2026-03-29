from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st

GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700;800"
    "&family=Newsreader:ital,wght@0,400;0,600;0,700;1,700"
    "&display=swap"
)

MATERIAL_SYMBOLS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD"
    "@20..48,100..700,0..1,-50..200"
    "&display=swap"
)

FONT_PRECONNECT = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
"""


def get_font_html() -> str:
    return (
        FONT_PRECONNECT
        + f'<link href="{GOOGLE_FONTS_URL}" rel="stylesheet">\n'
        + f'<link href="{MATERIAL_SYMBOLS_URL}" rel="stylesheet">\n'
    )


_TOP_LEVEL_ACCOUNT_NAMES = {
    "activo",
    "pasivo",
    "patrimonio",
    "ingresos",
    "gastos",
    "costos",
    "utilidad",
    "resultado",
}


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _fmt_cell(value: object) -> str:
    n = _to_float(value)
    if n is None:
        return escape(str(value if value is not None else ""))
    if n < 0:
        return (
            f"<span style='color:#BA1A1A;font-variant-numeric:tabular-nums;'>({abs(n):,.2f})</span>"
        )
    return f"<span style='color:#1E293B;font-variant-numeric:tabular-nums;'>{n:,.2f}</span>"


def _detect_col(columns: list[str], candidates: list[str]) -> str | None:
    cols_lower = {str(c).strip().lower(): c for c in columns}
    for c in candidates:
        hit = cols_lower.get(c.lower())
        if hit is not None:
            return str(hit)
    return None


def _is_top_level_account(row: pd.Series, code_col: str | None, name_col: str | None) -> bool:
    code = str(row.get(code_col, "") if code_col else "").strip()
    name = str(row.get(name_col, "") if name_col else "").strip().lower()
    if code in {"1", "2", "3", "4", "5", "6", "7", "8", "9"}:
        return True
    return name in _TOP_LEVEL_ACCOUNT_NAMES


def _render_notice(kind: str, body: object) -> None:
    txt = escape(str(body if body is not None else "")).replace("\n", "<br>")
    if kind == "error":
        st.markdown(
            f"<div class='risk-high'><b>Error</b><div style='margin-top:.35rem;'>{txt}</div></div>",
            unsafe_allow_html=True,
        )
    elif kind == "warning":
        st.markdown(
            (
                "<div class='sovereign-card' style='background:#FFF7ED;"
                "border-left:6px solid #B45309;'><b>Atencion</b>"
                f"<div style='margin-top:.35rem;'>{txt}</div></div>"
            ),
            unsafe_allow_html=True,
        )
    elif kind == "success":
        st.markdown(
            (
                "<div class='sovereign-card' style='background:#ECFDF5;"
                "border-left:6px solid #047857;'><b>OK</b>"
                f"<div style='margin-top:.35rem;'>{txt}</div></div>"
            ),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"<div class='ai-memo'>{txt}</div>", unsafe_allow_html=True)


def _render_editorial_table(data: object, *, max_rows: int = 250) -> None:
    if isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        try:
            df = pd.DataFrame(data)
        except Exception:
            df = pd.DataFrame({"valor": [str(data)]})

    if df.empty:
        st.markdown(
            "<div class='sovereign-card'>Sin datos tabulares.</div>", unsafe_allow_html=True
        )
        return

    if len(df) > max_rows:
        df = df.head(max_rows)

    cols = [str(c) for c in df.columns]
    code_col = _detect_col(cols, ["numero_cuenta", "codigo", "cuenta", "id"])
    name_col = _detect_col(cols, ["nombre_cuenta", "nombre", "descripcion", "concepto"])

    head_html = "".join([f"<th>{escape(c)}</th>" for c in cols])
    body_rows: list[str] = []

    for _, row in df.iterrows():
        is_l1 = _is_top_level_account(row, code_col, name_col)
        tr_cls = "tb-row tb-row-l1" if is_l1 else "tb-row"
        tds: list[str] = []

        for c in cols:
            raw = row.get(c)
            n = _to_float(raw)
            base_cls = "tb-cell"
            if n is not None:
                base_cls += " tb-num"
                cell_html = _fmt_cell(n)
            else:
                cell_html = escape(str(raw if raw is not None else ""))

            if name_col and c == name_col:
                base_cls += " tb-l1-name" if is_l1 else " tb-detail-name"

            tds.append(f"<td class='{base_cls}'>{cell_html}</td>")

        body_rows.append(f"<tr class='{tr_cls}'>{''.join(tds)}</tr>")

    st.markdown(
        f"""
        <div class="tb-shell">
          <div class="tb-card">
            <div style="max-height:560px;overflow:auto;">
              <table class="tb-table">
                <thead><tr>{head_html}</tr></thead>
                <tbody>{''.join(body_rows)}</tbody>
              </table>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_editorial_table(data: object, *, max_rows: int = 250) -> None:
    _render_editorial_table(data, max_rows=max_rows)


def apply_editorial_runtime_overrides() -> None:
    """Replace legacy Streamlit primitives with Sovereign-styled renderers."""
    if st.session_state.get("_sovereign_runtime_overrides_loaded"):
        return

    st.info = lambda body="", *args, **kwargs: _render_notice("info", body)
    st.warning = lambda body="", *args, **kwargs: _render_notice("warning", body)
    st.error = lambda body="", *args, **kwargs: _render_notice("error", body)
    st.success = lambda body="", *args, **kwargs: _render_notice("success", body)

    st.dataframe = lambda data=None, *args, **kwargs: _render_editorial_table(data)
    st.table = lambda data=None, *args, **kwargs: _render_editorial_table(data)

    st.session_state["_sovereign_runtime_overrides_loaded"] = True


def inject_sovereign_theme() -> None:
    """Inject global Sovereign Intelligence theme."""
    if st.session_state.get("_sovereign_theme_loaded"):
        return

    st.markdown(get_font_html(), unsafe_allow_html=True)

    css = """
:root {
  --sv-primary: #041627;
  --sv-primary-soft: #1a2b3c;
  --sv-surface: #f7fafc;
  --sv-surface-low: #f1f4f6;
  --sv-border-ghost: rgba(4, 22, 39, 0.15);
  --sv-text: #18212f;
  --sv-text-muted: #64748b;
  --sv-error: #ba1a1a;
  --sv-error-soft: #ffdad6;
  --sv-tertiary-fixed: #a5eff0;
}

.block-container { padding-top: 2rem !important; }

h1, h2, h3, [data-testid="stHeader"], .sv-heading {
  font-family: 'Newsreader', serif !important;
}

div, span, p, table, input, textarea, label {
  font-family: 'Inter', sans-serif !important;
}

.stApp,
.main,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {
  background: #f7fafc !important;
}

[data-testid="stSidebar"] {
  background-color: #f1f4f6 !important;
  border-right: none !important;
}

.sovereign-card {
  background: #ffffff !important;
  border-radius: 12px !important;
  padding: 1rem 1.1rem !important;
  box-shadow: 0 10px 30px rgba(24, 28, 30, 0.04) !important;
  border: 1px solid rgba(196, 198, 205, 0.15) !important;
  margin-bottom: 1rem !important;
}

[data-testid="stExpander"],
[data-testid="stMetricContainer"],
[data-testid="metric-container"],
[data-testid="stTabs"],
[data-testid="stTabs"] [role="tablist"],
[data-testid="stTabs"] [role="tab"] {
  border: none !important;
  box-shadow: none !important;
}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stDateInput input,
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
  border-radius: 12px !important;
  border: 1px solid var(--sv-border-ghost) !important;
  background: #ffffff !important;
  box-shadow: none !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus,
.stSelectbox [data-baseweb="select"] > div:focus-within,
.stMultiSelect [data-baseweb="select"] > div:focus-within {
  border-color: rgba(4, 22, 39, 0.30) !important;
  outline: none !important;
  box-shadow: none !important;
}

.stButton button,
.stDownloadButton button {
  border-radius: 12px !important;
  border: 1px solid var(--sv-border-ghost) !important;
  font-weight: 700 !important;
}

.stButton button[kind="primary"] {
  background: linear-gradient(135deg, #041627 0%, #1a2b3c 100%) !important;
  color: #fff !important;
  border: 0 !important;
  min-height: 46px !important;
  border-radius: 999px !important;
}

.sv-heading {
  color: var(--sv-primary) !important;
  font-size: 1.45rem;
  font-weight: 700;
  margin: .2rem 0 .8rem 0;
}

.ai-memo {
  background: var(--sv-primary);
  color: var(--sv-tertiary-fixed);
  border-radius: 16px;
  padding: 1rem 1.2rem;
  font-family: 'Newsreader', serif !important;
  font-style: italic;
  line-height: 1.6;
}

.risk-high {
  background: var(--sv-error-soft);
  border-left: 8px solid var(--sv-error);
  border-radius: 12px;
  padding: .9rem 1rem;
}

.tb-shell { background: var(--sv-surface-low); border-radius: 16px; padding: .8rem; }
.tb-card { background: #fff; border-radius: 12px; box-shadow: 0 10px 24px rgba(24, 28, 30, 0.06); padding: .45rem .55rem; }
.tb-table { width: 100%; border-collapse: collapse; border-spacing: 0; font-size: .84rem; }
.tb-table thead th { background: #f8fbff; color: #64748b; font-size: .64rem; letter-spacing: .11em; text-transform: uppercase; font-weight: 800; padding: .56rem .5rem; text-align: left; border-left: 0 !important; border-right: 0 !important; }
.tb-table tbody tr { border-bottom: 1px solid rgba(0,0,0,0.05) !important; }
.tb-table td { padding: .52rem .5rem; border-left: 0 !important; border-right: 0 !important; border-top: 0 !important; }
.tb-row:hover td { background: #eef5fb; }
.tb-l1-name { font-family: 'Newsreader', serif !important; font-size: 1.08rem; font-weight: 700; color: #041627; }
.tb-detail-name { font-family: 'Inter', sans-serif !important; font-size: .82rem; font-weight: 500; color: #334155; }
"""
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    apply_editorial_runtime_overrides()
    st.session_state["_sovereign_theme_loaded"] = True
