"""
LLM client unificado — soporta DeepSeek y OpenAI con la misma interfaz.
Selecciona el provider desde config.yaml.
"""

from __future__ import annotations

from typing import Any

import yaml
from openai import OpenAI

try:
    from dotenv import load_dotenv
    from pathlib import Path as _Path

    _env_path = _Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=_env_path, override=True)
except ImportError:
    pass  # dotenv optional, env vars may be set externally


def _load_config() -> dict[str, Any]:
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _obtener_api_key(nombre: str) -> str:
    """
    Load API key with priority:
    1. st.secrets (Streamlit Cloud)
    2. os.environ (any environment)
    3. .env file (local dev)
    """

    # 1. Streamlit secrets
    try:
        import streamlit as st

        # Try direct access first
        if hasattr(st, "secrets"):
            val = st.secrets.get(nombre, "")
            if val and str(val).strip():
                return str(val).strip()
    except Exception:
        pass

    # 2. Environment variable
    val = os.environ.get(nombre, "").strip()
    if val:
        return val

    # 3. .env file
    try:
        from dotenv import load_dotenv

        load_dotenv(override=False)
        val = os.environ.get(nombre, "").strip()
        if val:
            return val
    except Exception:
        pass

    return ""


# DO NOT assign at module level — lazy load instead
_DEEPSEEK_KEY_CACHE = None
_OPENAI_KEY_CACHE = None


def _get_deepseek_key() -> str:
    global _DEEPSEEK_KEY_CACHE
    if _DEEPSEEK_KEY_CACHE:
        return _DEEPSEEK_KEY_CACHE
    _DEEPSEEK_KEY_CACHE = _obtener_api_key("DEEPSEEK_API_KEY")
    return _DEEPSEEK_KEY_CACHE


def _get_openai_key() -> str:
    global _OPENAI_KEY_CACHE
    if _OPENAI_KEY_CACHE:
        return _OPENAI_KEY_CACHE
    _OPENAI_KEY_CACHE = _obtener_api_key("OPENAI_API_KEY")
    return _OPENAI_KEY_CACHE


def _get_client() -> tuple[OpenAI, str, dict[str, Any]]:
    """
    Returns (client, model, llm_config) based on config.yaml provider.
    Supports: deepseek, openai.
    """
    cfg = _load_config()
    llm_cfg = cfg.get("llm", {})
    provider = str(llm_cfg.get("provider", "deepseek")).lower()
    model = str(llm_cfg.get("model", "deepseek-chat"))

    if provider == "deepseek":
        api_key = _get_deepseek_key()
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not set. " "Add it to Streamlit Cloud Secrets.")
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
    else:
        api_key = _get_openai_key()
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set.")
        client = OpenAI(api_key=api_key)

    return client, model, llm_cfg


def llamar_llm(
    prompt: str,
    system: str = "Eres un auditor financiero experto en NIAs.",
    temperatura: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """
    Llama al LLM configurado (DeepSeek o OpenAI) y retorna el texto.

    Args:
        prompt: Mensaje del usuario.
        system: Instrucción de sistema.
        temperatura: Override de temperatura (usa config si None).
        max_tokens: Override de max_tokens (usa config si None).

    Returns:
        Texto de respuesta del modelo.

    Raises:
        ValueError: Si falta API key.
        Exception: Si la llamada falla.
    """
    client, model, llm_cfg = _get_client()

    temp = temperatura if temperatura is not None else float(llm_cfg.get("temperature", 0.3))
    tokens = max_tokens if max_tokens is not None else int(llm_cfg.get("max_tokens", 2000))

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temp,
        max_tokens=tokens,
    )

    return response.choices[0].message.content or ""


def llamar_llm_seguro(
    prompt: str,
    system: str = "Eres un auditor financiero experto en NIAs.",
    fallback: str = "[Sin respuesta del modelo]",
) -> str:
    """
    Version segura de llamar_llm que nunca lanza excepcion.
    Retorna fallback si falla.
    """
    try:
        return llamar_llm(prompt, system=system)
    except Exception as e:
        print(f"[LLM] Error: {e}")
        return fallback
