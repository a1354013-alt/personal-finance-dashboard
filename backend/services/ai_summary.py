"""
AI 摘要服務
目前使用 template 字串生成摘要，程式結構已預留 LLM 替換介面。
"""
from typing import Optional  # 點 11: 匯入 Optional


# ── LLM 介面 (點 11: 修正回傳型別為 Optional[str]) ───────────────────────────

def _call_llm(prompt: str) -> Optional[str]:
    """
    預留 LLM 呼叫介面。
    目前回傳 None，由呼叫端 fallback 到 template。
    """
    return None


# ── Dashboard 財務摘要 ────────────────────────────────────────────────────────

def generate_finance_summary(
    total_income: float,
    total_expense: float,
    top_category: str,
    month: Optional[str] = None,
) -> str:
    """生成財務摘要文字"""
    net = total_income - total_expense
    period = f"{month} 月份" if month else "本期"
    prompt = (
        f"請根據以下財務資料生成一段繁體中文摘要：\n"
        f"期間：{period}\n"
        f"總收入：{total_income}\n"
        f"總支出：{total_expense}\n"
        f"淨餘額：{net}\n"
        f"最高支出類別：{top_category}\n"
    )

    llm_result = _call_llm(prompt)
    if llm_result:
        return llm_result

    # Template fallback
    status = "結餘" if net >= 0 else "赤字"
    return (
        f"【{period}財務摘要】\n"
        f"本期總收入為 {total_income:,.0f} 元，"
        f"總支出為 {total_expense:,.0f} 元，"
        f"淨{status} {abs(net):,.0f} 元。"
        f"支出最高類別為「{top_category}」，"
        f"建議{'持續保持良好財務習慣。' if net >= 0 else '注意控制支出，避免超支。'}"
    )


# ── 股票解說 ──────────────────────────────────────────────────────────────────

def generate_stock_explanation(
    stock_code: str,
    passed: bool,
    fail_reasons: list,
    net_income: float,
    free_cash_flow: float,
    revenue_growth: float,
) -> str:
    """生成股票篩選結果解說文字"""
    prompt = (
        f"請解說股票 {stock_code} 的篩選結果：\n"
        f"通過篩選：{passed}\n"
        f"未通過原因：{fail_reasons}\n"
        f"淨利潤：{net_income}\n"
        f"自由現金流：{free_cash_flow}\n"
        f"營收成長率：{revenue_growth}%\n"
    )

    llm_result = _call_llm(prompt)
    if llm_result:
        return llm_result

    # Template fallback
    if passed:
        return (
            f"【{stock_code} 分析】\n"
            f"該股票通過所有篩選條件。"
            f"淨利潤 {net_income:,.0f}（正值），"
            f"自由現金流 {free_cash_flow:,.0f}（正值），"
            f"營收成長率 {revenue_growth:.1f}%（正成長），"
            f"基本面表現良好，符合投資篩選標準。"
        )
    else:
        reasons_text = "；".join(fail_reasons)
        return (
            f"【{stock_code} 分析】\n"
            f"該股票未通過篩選，原因如下：{reasons_text}。"
            f"建議持續追蹤基本面改善情況後再行評估。"
        )
