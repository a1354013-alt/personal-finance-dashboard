from __future__ import annotations

from dataclasses import dataclass


class LLMProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMProviderResult:
    text: str
    provider: str
    is_fallback: bool
    error: str | None = None


class BaseLLMProvider:
    """LLM provider interface.

    Providers must be:
    - deterministic in tests (mockable)
    - safe to call in API paths (timeouts + predictable errors)
    """

    name: str = "base"

    def is_configured(self) -> bool:
        return True

    def generate(self, *, system: str, user: str, temperature: float = 0.2) -> LLMProviderResult:
        raise NotImplementedError

