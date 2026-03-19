"""
LLM client unificado — soporta DeepSeek y OpenAI con la misma interfaz.
Selecciona el provider desde config.yaml.
"""
from __future__ import annotations

import os
from typing import Any

import yaml
from openai import OpenAI


def _load_config() -> dict[str, Any]:
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


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
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY not set. "
                "Add it to your .env file: DEEPSEEK_API_KEY=sk-..."
            )
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
    else:
        api_key = os.getenv("OPENAI_API_KEY", "")
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
