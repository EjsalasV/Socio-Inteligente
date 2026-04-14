"""
Web search fallback for the RAG pipeline.

Uses Tavily to retrieve external context when local normative chunks
have low confidence. Degrades gracefully — returns [] if TAVILY_API_KEY
is not set or if the search fails for any reason.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_AUDIT_TERMS = {
    "auditor", "auditoria", "nia", "niif", "ifrs", "iaasb",
    "contable", "financiero", "financiera", "aseveracion",
    "materialidad", "riesgo", "evidencia",
}


def _audit_contextualize(query: str) -> str:
    """Prefix with audit context if query has no audit terminology."""
    q = query.strip()
    q_lower = q.lower()
    if any(t in q_lower for t in _AUDIT_TERMS):
        return q
    return f"auditoria financiera {q}"


def search_web(query: str, max_results: int = 3) -> list[dict[str, str]]:
    """
    Search the web for audit-related context via Tavily.

    Returns a list of {title, url, content} dicts (content truncated to 600 chars).
    Returns [] if TAVILY_API_KEY is unset or on any error — caller must handle empty list.
    """
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return []

    try:
        from tavily import TavilyClient  # type: ignore[import-untyped]
        client = TavilyClient(api_key=api_key)
        contextualized = _audit_contextualize(query)
        response = client.search(
            query=contextualized,
            max_results=max_results,
            search_depth="basic",
            include_answer=False,
        )
        results: list[dict[str, str]] = []
        for r in (response.get("results") or []):
            title = str(r.get("title") or "").strip()
            url = str(r.get("url") or "").strip()
            content = str(r.get("content") or "").strip()
            if content:
                results.append({"title": title, "url": url, "content": content[:600]})
        return results
    except Exception as exc:
        logger.warning("web_search_service: search failed — %s", exc)
        return []
