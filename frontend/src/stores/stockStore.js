import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as stockApi from '@/api/stocks'

/**
 * 股票模組 Store
 * 管理自選股清單、篩選結果與同步狀態。
 */
export const useStockStore = defineStore('stock', () => {
  const watchlist = ref([])
  const filterResults = ref([])
  
  const watchlistLoading = ref(false)
  const filterLoading = ref(false)
  const syncLoading = ref(false)
  
  const watchlistError = ref(null)
  const filterError = ref(null)

  const passedStocks = computed(() =>
    filterResults.value.filter(s => s.passed)
  )

  const failedStocks = computed(() =>
    filterResults.value.filter(s => !s.passed)
  )

  /** 取得自選股清單 (含最新價格) */
  async function fetchWatchlist() {
    watchlistLoading.value = true
    watchlistError.value = null
    try {
      const res = await stockApi.getWatchlist()
      watchlist.value = res
    } catch (e) {
      watchlistError.value = e.message
    } finally {
      watchlistLoading.value = false
    }
  }

  /** 新增自選股 */
  async function addToWatchlist(stockCode) {

    try {
      const res = await stockApi.addToWatchlist(stockCode)
      await fetchWatchlist()
      return res
    } catch (e) {
      throw e.message
    }
  }

  /** 刪除自選股 */
  async function deleteFromWatchlist(id) {
    try {
      await stockApi.deleteFromWatchlist(id)
      watchlist.value = watchlist.value.filter(item => item.id !== id)
    } catch (e) {
      throw e.message
    }
  }

  /** 同步所有價格 */
  async function syncAllPrices() {
    syncLoading.value = true
    try {
      const res = await stockApi.syncAllPrices()
      await fetchWatchlist()
      return res
    } catch (e) {
      throw e.message
    } finally {
      syncLoading.value = false
    }
  }

  /** 取得自選股篩選結果 */
  async function fetchFilterResults() {
    filterLoading.value = true
    filterError.value = null
    try {
      const res = await stockApi.getFilterResults()
      filterResults.value = res
    } catch (e) {
      filterError.value = e.message
    } finally {
      filterLoading.value = false
    }
  }

  /** 單一股票篩選評估 */
  async function evaluateStock(data) {
    return stockApi.filterSingleStock(data)
  }

  /** 取得 AI 股票解說 */
  async function getAiStockExplain(data) {
    return stockApi.getAiStockExplain(data)
  }

  return {
    watchlist, filterResults,
    watchlistLoading, filterLoading, syncLoading,
    watchlistError, filterError,
    passedStocks, failedStocks,
    fetchWatchlist, fetchFilterResults,
    addToWatchlist, deleteFromWatchlist, syncAllPrices,
    evaluateStock, getAiStockExplain
  }
})
