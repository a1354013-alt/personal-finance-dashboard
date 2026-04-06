"""
AI 摘要服務
目前使用 template 字串生成摘要，程式結構已預留 LLM 替換介面。
"""
from typing import Optional, List, Dict


def _call_llm(prompt: str) -> Optional[str]:
    """
    預留 LLM 呼叫介面。
    目前回傳 None，由呼叫端 fallback 到 template。
    """
    return None


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

    status = "結餘" if net >= 0 else "赤字"
    return (
        f"【{period}財務摘要】\n"
        f"本期總收入為 {total_income:,.0f} 元，"
        f"總支出為 {total_expense:,.0f} 元，"
        f"淨{status} {abs(net):,.0f} 元。"
        f"支出最高類別為「{top_category}」，"
        f"建議{'持續保持良好財務習慣。' if net >= 0 else '注意控制支出，避免超支。'}"
    )


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


def generate_budget_advice(budget_status: List[Dict]) -> str:
    """
    根據預算執行狀況產生建議
    """
    if not budget_status:
        return "目前尚無預算設定。建議針對『餐飲』或『購物』等高頻率支出類別設定每月限額，幫助您更有效地控制支出。"

    over_budgets = [b for b in budget_status if b.get('over_budget', False)]
    near_limits = [b for b in budget_status if not b.get('over_budget', False) and b.get('percent_used', 0) > 80]
    
    prompt = f"請根據以下預算執行狀況生成一段繁體中文理財建議：\n{budget_status}\n"
    llm_result = _call_llm(prompt)
    if llm_result:
        return llm_result

    advices = []
    if over_budgets:
        categories = "、".join([b['category'] for b in over_budgets])
        advices.append(f"⚠️ 警示：您的【{categories}】類別已超出預算！請立即檢視本月剩餘天數，並嚴格限制相關支出。")
        
    if near_limits:
        categories = "、".join([b['category'] for b in near_limits])
        advices.append(f"💡 提醒：【{categories}】類別的使用率已超過 80%，接近預算上限，請留意後續消費。")
        
    if not advices:
        return "✅ 本月預算執行狀況良好，所有類別皆在控制範圍內。請繼續保持良好的消費習慣！"
        
    return " ".join(advices)
