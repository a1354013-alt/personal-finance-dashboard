from __future__ import annotations

import os

from .base import BaseLLMProvider, LLMProviderResult


class MockProvider(BaseLLMProvider):
    """Test-only provider.

    This provider never calls external services and always returns predictable output.
    """

    name = "mock"

    def __init__(self, *, text: str | None = None) -> None:
        self._text = text or os.getenv("LLM_MOCK_TEXT", "mock response")

    def generate(self, *, system: str, user: str, temperature: float = 0.0) -> LLMProviderResult:
        return LLMProviderResult(text=self._text, provider=self.name, is_fallback=False, error=None)

