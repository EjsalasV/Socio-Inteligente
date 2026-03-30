from __future__ import annotations

import os

from openai import OpenAI

from .prompt_builder import load_system_prompt, max_tokens_for_mode


def _provider_client() -> tuple[OpenAI, str, str]:
    provider = (os.getenv("AI_PROVIDER") or "openai").strip().lower()
    if provider == "deepseek":
        api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY no configurada")
        model = (os.getenv("DEEPSEEK_CHAT_MODEL") or "deepseek-chat").strip() or "deepseek-chat"
        base_url = (os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").strip()
        return OpenAI(api_key=api_key, base_url=base_url), model, provider

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no configurada")
    model = (os.getenv("OPENAI_CHAT_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"
    return OpenAI(api_key=api_key), model, provider


def call_llm(
    *,
    prompt_usuario: str,
    modo: str,
    system_prompt: str | None = None,
) -> tuple[str, dict[str, str]]:
    if system_prompt is None:
        system_prompt = load_system_prompt()
    max_tokens = max_tokens_for_mode(modo)
    client, model, provider = _provider_client()

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_usuario},
        ],
        temperature=0.2,
        max_output_tokens=max_tokens,
    )
    text = getattr(response, "output_text", "") or ""
    return text, {"provider": provider, "model": model, "max_tokens": str(max_tokens)}
