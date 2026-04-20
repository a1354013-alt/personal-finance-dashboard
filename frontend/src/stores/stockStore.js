import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import * as stockApi from '@/api/stocks'
import { normalizeFilterMetadata, normalizeFundamentalsFilterResult, normalizeWatchlistItem } from '@/api/contracts'

export const useStockStore = defineStore('stock', () => {
  const watchlist = ref([])
  const filterResults = ref([])
  const filterMetadata = ref(null)
  const fundamentalsSyncing = ref(false)
  const fundamentalsError = ref(null)

  const watchlistLoading = ref(false)
  const filterLoading = ref(false)
  const syncAllLoading = ref(false)
  const syncingCodes = ref([])

  const watchlistError = ref(null)
  const filterError = ref(null)

  const passedStocks = computed(() => filterResults.value.filter((stock) => stock.passed))
  const failedStocks = computed(() => filterResults.value.filter((stock) => !stock.passed))

  async function fetchWatchlist() {
    watchlistLoading.value = true
    watchlistError.value = null
    try {
      const result = await stockApi.getWatchlist()
      watchlist.value = Array.isArray(result) ? result.map(normalizeWatchlistItem).filter(Boolean) : []
    } catch (error) {
      watchlistError.value = error.message
    } finally {
      watchlistLoading.value = false
    }
  }

  async function addToWatchlist(stockCode) {
    try {
      const response = await stockApi.addToWatchlist(stockCode)
      await fetchWatchlist()
      return response
    } catch (error) {
      throw new Error(error.message)
    }
  }

  async function deleteFromWatchlist(id) {
    try {
      await stockApi.deleteFromWatchlist(id)
      watchlist.value = watchlist.value.filter((item) => item.id !== id)
    } catch (error) {
      throw new Error(error.message)
    }
  }

  async function syncAllPrices() {
    syncAllLoading.value = true
    try {
      const response = await stockApi.syncAllPrices()
      await fetchWatchlist()
      return response
    } catch (error) {
      throw new Error(error.message)
    } finally {
      syncAllLoading.value = false
    }
  }

  function isSingleSyncing(stockCode) {
    return syncingCodes.value.includes(stockCode)
  }

  async function syncSinglePrice(stockCode) {
    if (isSingleSyncing(stockCode)) {
      return null
    }

    syncingCodes.value.push(stockCode)
    try {
      const response = await stockApi.syncSinglePrice(stockCode)
      await fetchWatchlist()
      return response
    } catch (error) {
      throw new Error(error.message)
    } finally {
      syncingCodes.value = syncingCodes.value.filter((code) => code !== stockCode)
    }
  }

  async function fetchFilterResults() {
    filterLoading.value = true
    filterError.value = null

    try {
      const [results, metadata] = await Promise.all([
        stockApi.getFilterResults(),
        stockApi.getFilterMetadata()
      ])
      filterResults.value = Array.isArray(results) ? results.map(normalizeFundamentalsFilterResult).filter(Boolean) : []
      filterMetadata.value = normalizeFilterMetadata(metadata)
    } catch (error) {
      filterError.value = error.message
    } finally {
      filterLoading.value = false
    }
  }

  async function syncFundamentals({ force = false } = {}) {
    fundamentalsSyncing.value = true
    fundamentalsError.value = null
    try {
      await stockApi.syncWatchlistFundamentals({ force })
      await fetchFilterResults()
    } catch (error) {
      fundamentalsError.value = error.message || 'Unable to sync fundamentals.'
      throw error
    } finally {
      fundamentalsSyncing.value = false
    }
  }

  async function evaluateStock(data) {
    return stockApi.filterSingleStock(data)
  }

  async function getAiStockExplain(data) {
    return stockApi.getAiStockExplain(data)
  }

  return {
    watchlist,
    filterResults,
    filterMetadata,
    fundamentalsSyncing,
    fundamentalsError,
    watchlistLoading,
    filterLoading,
    syncAllLoading,
    syncingCodes,
    watchlistError,
    filterError,
    passedStocks,
    failedStocks,
    fetchWatchlist,
    fetchFilterResults,
    syncFundamentals,
    addToWatchlist,
    deleteFromWatchlist,
    syncAllPrices,
    syncSinglePrice,
    isSingleSyncing,
    evaluateStock,
    getAiStockExplain
  }
})
