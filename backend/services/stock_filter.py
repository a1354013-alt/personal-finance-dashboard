"""
股票篩選引擎 (Rule-Based Filtering System)

規則設計原則：
  - 每條規則為一個獨立函式，回傳 (passed: bool, reason: str)
  - evaluate_stock 彙整所有規則，回傳 passed 與 fail_reasons
"""
from typing import List, Tuple


# ── 個別規則函式 ──────────────────────────────────────────────────────────────

def rule_net_income_positive(net_income: float) -> Tuple[bool, str]:
    """規則 1：淨利潤必須大於 0"""
    if net_income > 0:
        return True, ""
    return False, f"net_income={net_income} 未達標準（需 > 0）"


def rule_free_cash_flow_positive(free_cash_flow: float) -> Tuple[bool, str]:
    """規則 2：自由現金流必須大於 0"""
    if free_cash_flow > 0:
        return True, ""
    return False, f"free_cash_flow={free_cash_flow} 未達標準（需 > 0）"


def rule_revenue_growth_positive(revenue_growth: float) -> Tuple[bool, str]:
    """規則 3：營收成長率必須大於 0"""
    if revenue_growth > 0:
        return True, ""
    return False, f"revenue_growth={revenue_growth}% 未達標準（需 > 0%）"


# ── 所有規則清單（可擴充）────────────────────────────────────────────────────

RULES = [
    ("net_income",      rule_net_income_positive),
    ("free_cash_flow",  rule_free_cash_flow_positive),
    ("revenue_growth",  rule_revenue_growth_positive),
]


# ── 核心評估函式 ──────────────────────────────────────────────────────────────

def evaluate_stock(
    stock_code: str,
    net_income: float,
    free_cash_flow: float,
    revenue_growth: float,
) -> dict:
    """
    對單一股票執行所有篩選規則。

    Returns:
        {
            "stock_code": str,
            "passed": bool,
            "fail_reasons": List[str]
        }
    """
    fail_reasons: List[str] = []

    values = {
        "net_income":     net_income,
        "free_cash_flow": free_cash_flow,
        "revenue_growth": revenue_growth,
    }

    for rule_key, rule_fn in RULES:
        passed, reason = rule_fn(values[rule_key])
        if not passed:
            fail_reasons.append(reason)

    return {
        "stock_code":   stock_code,
        "passed":       len(fail_reasons) == 0,
        "fail_reasons": fail_reasons,
    }
