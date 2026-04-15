from __future__ import annotations

import os
from typing import Any

import requests

from .base import BaseLLMProvider, LLMProviderError, LLMProviderResult


class OpenAIProvider(BaseLLMProvider):
    name = "openai"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 15.0,
        base_url: str | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self._timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", str(timeout_seconds)))
        self._base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def generate(self, *, system: str, user: str, temperature: float = 0.2) -> LLMProviderResult:
        if not self._api_key:
            raise LLMProviderError("OPENAI_API_KEY is missing.")

        url = f"{self._base_url.rstrip('/')}/responses"
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        payload: dict[str, Any] = {
            "model": self._model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system}]},
                {"role": "user", "content": [{"type": "input_text", "text": user}]},
            ],
            "temperature": float(temperature),
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self._timeout)
        except requests.Timeout as exc:
            raise LLMProviderError(f"OpenAI request timed out after {self._timeout}s.") from exc
        except requests.RequestException as exc:
            raise LLMProviderError(f"OpenAI request failed: {exc}") from exc

        if resp.status_code >= 400:
            detail = resp.text[:500]
            raise LLMProviderError(f"OpenAI error {resp.status_code}: {detail}")

        data = resp.json()
        text = _extract_response_text(data)
        if not text:
            raise LLMProviderError("OpenAI response did not contain output text.")

        return LLMProviderResult(text=text, provider=self.name, is_fallback=False, error=None)


def _extract_response_text(data: dict[str, Any]) -> str:
    # Prefer the canonical field when present.
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    # Otherwise traverse "output" structure.
    output = data.get("output")
    if not isinstance(output, list):
        return ""

    chunks: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) or []:
            if not isinstance(content, dict):
                continue
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                chunks.append(content["text"])

    return "\n".join([c.strip() for c in chunks if c and c.strip()]).strip()

