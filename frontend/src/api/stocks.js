/**
 * 股票模組 API (v0.5.0)
 * 包含自選股管理、價格同步與篩選功能。
 */
import api from './index'

/** 取得自選股清單 */
export function getWatchlist() {
  return api.get('/stocks/watchlist')
}

/** 新增自選股 (點 5) */
export function addToWatchlist(stockCode) {
  return api.post('/stocks/watchlist', { stock_code: stockCode })
}

/** 刪除自選股 (點 5) */
export function deleteFromWatchlist(id) {
  return api.delete(`/stocks/watchlist/${id}`)
}

/** 同步所有自選股價格 (點 10) */
export function syncAllPrices() {
  return api.post('/stocks/sync')
}

/** 同步單一股票價格 (點 10) */
export function syncSinglePrice(stockCode) {
  return api.post(`/stocks/${stockCode.toUpperCase()}/sync`)
}

/** 取得所有 mock 股票篩選結果 (點 9) */
export function getFilterResults() {
  return api.get('/stocks/filter')
}

/**
 * 對單一股票進行篩選 (點 9)
 * @param {Object} data - { stock_code, net_income, free_cash_flow, revenue_growth }
 */
export function filterSingleStock(data) {
  return api.post('/stocks/filter', data)
}

/**
 * 取得 AI 股票解說
 * @param {Object} data - { stock_code, net_income, free_cash_flow, revenue_growth }
 */
export function getAiStockExplain(data) {
  return api.post('/ai/stock-explain', data)
}
