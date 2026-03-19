import api from './index'

/** 取得 Dashboard 彙整資料 */
export function getDashboardSummary() {
  return api.get('/dashboard/summary')
}

/** 取得 AI 財務摘要 */
export function getAiSummary() {
  return api.get('/ai/summary')
}

/**
 * 取得 AI 股票解說
 * @param {Object} data - { stock_code, net_income, free_cash_flow, revenue_growth }
 */
export function getAiStockExplain(data) {
  return api.post('/ai/stock-explain', data)
}
