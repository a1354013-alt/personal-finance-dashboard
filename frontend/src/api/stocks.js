import api from './index'

export function getWatchlist() {
  return api.get('/stocks/watchlist')
}

export function addToWatchlist(stockCode) {
  return api.post('/stocks/watchlist', { stock_code: stockCode })
}

export function deleteFromWatchlist(id) {
  return api.delete(`/stocks/watchlist/${id}`)
}

export function syncAllPrices() {
  return api.post('/stocks/sync')
}

export function syncSinglePrice(stockCode) {
  return api.post(`/stocks/${stockCode.toUpperCase()}/sync`)
}

export function getFilterResults() {
  return api.get('/stocks/filter')
}

export function getFilterMetadata() {
  return api.get('/stocks/filter-metadata')
}

export function filterSingleStock(data) {
  return api.post('/stocks/filter', data)
}

export function getAiStockExplain(data) {
  return api.post('/ai/stock-explain', data)
}
