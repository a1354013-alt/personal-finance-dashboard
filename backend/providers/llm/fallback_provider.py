from __future__ import annotations

import json
import hashlib

from .base import BaseLLMProvider, LLMProviderResult


class FallbackProvider(BaseLLMProvider):
    """Deterministic local fallback.

    This is intentionally *not* a generic text generator. It provides a stable,
    predictable summary given a prompt payload, so dev environments without keys
    can still demonstrate the feature without 500s.
    """

    name = "fallback"

    def generate(self, *, system: str, user: str, temperature: float = 0.0) -> LLMProviderResult:
        digest = hashlib.sha256((system + "\n" + user).encode("utf-8")).hexdigest()[:8]
        text = _render_fallback_text(user=user, request_id=digest)
        return LLMProviderResult(text=text, provider=self.name, is_fallback=True, error=None)


def _render_fallback_text(*, user: str, request_id: str) -> str:
    try:
        payload = json.loads(user)
    except json.JSONDecodeError:
        return (
            "AI insights are running in deterministic fallback mode.\n"
            f"- request_id: {request_id}\n"
            "- note: fallback output is heuristic (no external model)\n\n"
            f"{user}"
        )

    kind = payload.get("kind")
    if kind == "finance_summary":
        period = payload.get("period", "all_time")
        income = payload.get("total_income", 0)
        expense = payload.get("total_expense", 0)
        net = payload.get("net_balance", income - expense)
        top_category = payload.get("top_category", "N/A")
        balance_text = "surplus" if net >= 0 else "deficit"
        return (
            f"[Fallback AI] Finance summary ({period})\n"
            f"- income: {income:,.2f}\n"
            f"- expense: {expense:,.2f}\n"
            f"- net: {net:,.2f} ({balance_text})\n"
            f"- top expense category: {top_category}\n\n"
            "Next steps:\n"
            "- Review recurring expenses in the top category.\n"
            "- Set a monthly budget target and compare against current-month spend.\n"
            f"- request_id: {request_id}"
        )

    if kind == "budget_advice":
        over = payload.get("over_budget", [])
        near = payload.get("near_limit", [])
        lines = ["[Fallback AI] Budget advice"]
        if over:
            lines.append(f"- over budget: {', '.join(over)}")
        if near:
            lines.append(f"- near limit (>=80%): {', '.join(near)}")
        if not over and not near:
            lines.append("- all tracked budgets are within range")
        lines.append("")
        lines.append("Suggestions:")
        lines.append("- Set alerts for categories crossing 80% to avoid end-of-month surprises.")
        lines.append("- If a category is consistently over, adjust the limit or split into sub-categories.")
        lines.append(f"- request_id: {request_id}")
        return "\n".join(lines)

    if kind == "stock_explain":
        stock_code = payload.get("stock_code", "N/A")
        passed = bool(payload.get("passed"))
        reasons = payload.get("fail_reasons", []) or []
        if passed:
            return (
                f"{stock_code} currently passes the baseline screen.\n"
                "Positive signals came from the cached fundamentals used by the rules-based check.\n"
                "Use the detailed metrics panel to confirm valuation, profitability, and growth before making decisions."
            )
        reason_text = "; ".join(map(str, reasons)) if reasons else "One or more screening rules were not met."
        return (
            f"{stock_code} currently does not pass the baseline screen.\n"
            f"Key reason: {reason_text}\n"
            "Refresh fundamentals if the data may be outdated, then review the metrics again."
        )

    if kind == "stock_interpretation":
        stock = payload.get("stock", {})
        stock_code = stock.get("stock_code", "N/A")
        price_change = stock.get("price_change")
        change_percent = stock.get("change_percent")
        volume = stock.get("volume")
        movement = "flat or unavailable"
        if price_change is not None and change_percent is not None:
            direction = "higher" if price_change > 0 else "lower" if price_change < 0 else "flat"
            movement = f"{direction} by {price_change:.2f} ({change_percent:.2f}%)"
        volume_text = f"Volume was {volume:,} shares." if volume is not None else "Volume data is not available."
        return (
            f"{stock_code} data interpretation\n"
            f"- Recent price movement: {movement}.\n"
            f"- Liquidity note: {volume_text}\n"
            "- Risk notes: Price changes may reflect market volatility, provider delays, or incomplete data.\n"
            "- Watch points: Review freshness, volume changes, and company-specific news separately.\n"
            "This is informational only and not financial advice."
        )

    return (
        "AI insights are running in deterministic fallback mode.\n"
        f"- request_id: {request_id}\n"
        "- note: fallback output is heuristic (no external model)\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
