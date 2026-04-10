from __future__ import annotations

from typing import Callable

RuleResult = tuple[bool, str]


def rule_net_income_positive(net_income: float) -> RuleResult:
    if net_income > 0:
        return True, ""
    return False, "Net income must be positive."


def rule_free_cash_flow_positive(free_cash_flow: float) -> RuleResult:
    if free_cash_flow > 0:
        return True, ""
    return False, "Free cash flow must be positive."


def rule_revenue_growth_positive(revenue_growth: float) -> RuleResult:
    if revenue_growth > 0:
        return True, ""
    return False, "Revenue growth must be positive."


RULES: list[tuple[str, Callable[[float], RuleResult]]] = [
    ("net_income", rule_net_income_positive),
    ("free_cash_flow", rule_free_cash_flow_positive),
    ("revenue_growth", rule_revenue_growth_positive),
]


def evaluate_stock(
    stock_code: str,
    net_income: float,
    free_cash_flow: float,
    revenue_growth: float,
) -> dict:
    values = {
        "net_income": net_income,
        "free_cash_flow": free_cash_flow,
        "revenue_growth": revenue_growth,
    }
    fail_reasons: list[str] = []

    for key, rule in RULES:
        passed, reason = rule(values[key])
        if not passed:
            fail_reasons.append(reason)

    return {
        "stock_code": stock_code,
        "passed": len(fail_reasons) == 0,
        "fail_reasons": fail_reasons,
    }
