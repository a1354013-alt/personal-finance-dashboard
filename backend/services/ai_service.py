from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from providers.llm import BaseLLMProvider
from providers.llm.base import LLMProviderError, LLMProviderResult
from providers.llm.fallback_provider import FallbackProvider


@dataclass(frozen=True)
class AITextResult:
    text: str
    provider: str
    is_fallback: bool
    error: str | None = None


class AIInsightsService:
    def __init__(self, provider: BaseLLMProvider) -> None:
        self._provider = provider
        self._fallback = FallbackProvider()

    def finance_summary(
        self,
        *,
        total_income: float,
        total_expense: float,
        top_category: str,
        period: str,
    ) -> AITextResult:
        net_balance = total_income - total_expense
        payload = {
            "kind": "finance_summary",
            "period": period,
            "total_income": round(float(total_income), 2),
            "total_expense": round(float(total_expense), 2),
            "net_balance": round(float(net_balance), 2),
            "top_category": top_category,
        }
        return self._safe_generate(
            system=_SYSTEM_PROMPT_FINANCE,
            user=json.dumps(payload, ensure_ascii=False),
            temperature=0.2,
        )

    def budget_advice(self, *, budget_status: list[dict]) -> AITextResult:
        over_budget = [item["category"] for item in budget_status if item.get("over_budget")]
        near_limit = [
            item["category"]
            for item in budget_status
            if (not item.get("over_budget")) and float(item.get("percent_used", 0)) >= 80
        ]
        payload = {
            "kind": "budget_advice",
            "over_budget": over_budget,
            "near_limit": near_limit,
            "budget_status": _json_sanitize(budget_status),
        }
        return self._safe_generate(
            system=_SYSTEM_PROMPT_BUDGET,
            user=json.dumps(payload, ensure_ascii=False),
            temperature=0.2,
        )

    def stock_explanation(
        self,
        *,
        stock_code: str,
        passed: bool,
        fail_reasons: list[str],
        metrics: dict,
    ) -> AITextResult:
        payload = {
            "kind": "stock_explain",
            "stock_code": stock_code,
            "passed": passed,
            "fail_reasons": fail_reasons,
            "metrics": _json_sanitize(metrics),
        }
        return self._safe_generate(
            system=_SYSTEM_PROMPT_STOCK,
            user=json.dumps(payload, ensure_ascii=False),
            temperature=0.2,
        )

    def _safe_generate(self, *, system: str, user: str, temperature: float) -> AITextResult:
        try:
            result: LLMProviderResult = self._provider.generate(system=system, user=user, temperature=temperature)
            return AITextResult(text=result.text, provider=result.provider, is_fallback=result.is_fallback, error=None)
        except (LLMProviderError, Exception) as exc:
            fallback = self._fallback.generate(system=system, user=user, temperature=0.0)
            return AITextResult(
                text=fallback.text,
                provider=fallback.provider,
                is_fallback=True,
                error=str(exc),
            )


_SYSTEM_PROMPT_FINANCE = (
    "You are a finance assistant for a personal finance dashboard.\n"
    "Generate a concise, actionable summary based on the provided JSON payload.\n"
    "Constraints:\n"
    "- Use the numbers exactly as provided.\n"
    "- Provide 3-6 bullet points and a short closing sentence.\n"
    "- Do not claim real-time market data access.\n"
)

_SYSTEM_PROMPT_BUDGET = (
    "You are a budgeting assistant.\n"
    "Given the JSON payload, provide short advice prioritizing overspent categories.\n"
    "Constraints:\n"
    "- Be specific and actionable.\n"
    "- Do not suggest impossible actions.\n"
)

_SYSTEM_PROMPT_STOCK = (
    "You are an investing education assistant.\n"
    "Explain why a stock passed or failed a rules-based screen using the JSON payload.\n"
    "Constraints:\n"
    "- Do not provide financial advice.\n"
    "- Focus on explaining the rules and the supplied metrics.\n"
)


def _json_sanitize(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_sanitize(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _json_sanitize(v) for k, v in value.items()}
    return value
