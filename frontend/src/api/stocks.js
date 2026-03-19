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
