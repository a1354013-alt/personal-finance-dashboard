from __future__ import annotations

from typing import Optional


def _call_llm(prompt: str) -> Optional[str]:
    return None


def generate_finance_summary(
    total_income: float,
    total_expense: float,
    top_category: str,
    month: str | None = None,
) -> str:
    net = total_income - total_expense
    period = month or "all recorded periods"
    prompt = (
        f"Period: {period}\n"
        f"Income: {total_income}\n"
        f"Expense: {total_expense}\n"
        f"Net: {net}\n"
        f"Top category: {top_category}\n"
    )

    llm_result = _call_llm(prompt)
    if llm_result:
      return llm_result

    balance_text = "positive" if net >= 0 else "negative"
    return (
        f"For {period}, total income is {total_income:,.0f} and total expense is {total_expense:,.0f}. "
        f"The net balance is {balance_text} at {net:,.0f}. "
        f"The largest expense category so far is {top_category}. "
        f"Keep reviewing recurring expenses and compare them against the monthly budgets."
    )


def generate_stock_explanation(
    stock_code: str,
    passed: bool,
    fail_reasons: list[str],
    net_income: float,
    free_cash_flow: float,
    revenue_growth: float,
) -> str:
    prompt = (
        f"Stock: {stock_code}\n"
        f"Passed: {passed}\n"
        f"Reasons: {fail_reasons}\n"
        f"Net income: {net_income}\n"
        f"Free cash flow: {free_cash_flow}\n"
        f"Revenue growth: {revenue_growth}\n"
    )

    llm_result = _call_llm(prompt)
    if llm_result:
      return llm_result

    if passed:
        return (
            f"{stock_code} passes the current mock screen. "
            f"Net income ({net_income:,.0f}), free cash flow ({free_cash_flow:,.0f}), "
            f"and revenue growth ({revenue_growth:.1f}%) are all positive."
        )

    return (
        f"{stock_code} does not pass the current mock screen. "
        f"Reasons: {', '.join(fail_reasons)}."
    )


def generate_budget_advice(budget_status: list[dict]) -> str:
    if not budget_status:
        return "No budgets have been created yet. Add at least one budget to receive advice."

    over_budget = [item for item in budget_status if item.get("over_budget")]
    near_limit = [item for item in budget_status if not item.get("over_budget") and item.get("percent_used", 0) >= 80]

    llm_result = _call_llm(str(budget_status))
    if llm_result:
      return llm_result

    messages = []
    if over_budget:
        categories = ", ".join(item["category"] for item in over_budget)
        messages.append(f"Over budget categories: {categories}. Review these first and consider lowering discretionary spending.")

    if near_limit:
        categories = ", ".join(item["category"] for item in near_limit)
        messages.append(f"Categories close to the limit: {categories}. Monitor the remaining days of the month carefully.")

    if not messages:
        return "All tracked budgets are currently within range. Keep the same pace and continue logging expenses consistently."

    return " ".join(messages)
