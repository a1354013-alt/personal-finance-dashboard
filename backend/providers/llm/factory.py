from __future__ import annotations

import os
from functools import lru_cache

from .base import BaseLLMProvider
from .fallback_provider import FallbackProvider
from .mock_provider import MockProvider
from .openai_provider import OpenAIProvider


@lru_cache(maxsize=1)
def get_llm_provider() -> BaseLLMProvider:
    """Return the configured LLM provider.

    Rules:
    - Provider selected by LLM_PROVIDER env var: openai|fallback
    - If openai is selected but not configured, auto-degrade to fallback
    - Never crash the API path by failing to build the provider
    """

    name = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if name in {"fallback", "local"}:
        return FallbackProvider()

    if name in {"mock", "test"}:
        return MockProvider()

    if name in {"openai"}:
        provider = OpenAIProvider()
        if provider.is_configured():
            return provider
        return FallbackProvider()

    # Unknown -> stable fallback
    return FallbackProvider()


def reset_llm_provider_cache() -> None:
    get_llm_provider.cache_clear()
