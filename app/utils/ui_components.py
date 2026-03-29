from __future__ import annotations

import streamlit as st


def inject_head() -> None:
    if st.session_state.get("_ui_head_injected"):
        return
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
        """,
        unsafe_allow_html=True,
    )
    st.session_state["_ui_head_injected"] = True


def render_html(html_string: str) -> None:
    st.markdown(html_string, unsafe_allow_html=True)


def card_start(extra_class: str = "") -> str:
    extra = f" {extra_class.strip()}" if extra_class.strip() else ""
    return f"<div class='sovereign-card{extra}'>"


def card_end() -> str:
    return "</div>"


def ai_memo(text: str) -> str:
    return f"<div class='ai-memo'>{text}</div>"


def status_badge(label: str, type: str = "info") -> str:
    color = {
        "high": "#BA1A1A",
        "error": "#BA1A1A",
        "medium": "#B45309",
        "warning": "#B45309",
        "success": "#047857",
        "low": "#64748B",
        "info": "#041627",
    }.get((type or "info").lower(), "#041627")
    return (
        "<span style='display:inline-block;padding:.2rem .55rem;border-radius:999px;"
        f"background:{color};color:#fff;font-size:.68rem;font-weight:700;'>{label}</span>"
    )
