import api from './index'

/** 取得自選股清單 */
export function getWatchlist() {
  return api.get('/stocks/watchlist')
}

/** 取得所有 mock 股票篩選結果 */
export function getFilterResults() {
  return api.get('/stocks/filter')
}

/**
 * 對單一股票進行篩選
 * @param {Object} data - { stock_code, net_income, free_cash_flow, revenue_growth }
 */
export function filterSingleStock(data) {
  return api.post('/stocks/filter', data)
}

/**
 * 點 6: 取得 AI 股票解說 (從 dashboard.js 移至此處獨立模組)
 * @param {Object} data - { stock_code, net_income, free_cash_flow, revenue_growth }
 */
export function getAiStockExplain(data) {
  return api.post('/ai/stock-explain', data)
}
