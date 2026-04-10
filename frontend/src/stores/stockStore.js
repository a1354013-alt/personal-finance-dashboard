import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import * as stockApi from '@/api/stocks'

export const useStockStore = defineStore('stock', () => {
  const watchlist = ref([])
  const filterResults = ref([])
  const filterMetadata = ref(null)

  const watchlistLoading = ref(false)
  const filterLoading = ref(false)
  const syncLoading = ref(false)

  const watchlistError = ref(null)
  const filterError = ref(null)

  const passedStocks = computed(() => filterResults.value.filter((stock) => stock.passed))
  const failedStocks = computed(() => filterResults.value.filter((stock) => !stock.passed))

  async function fetchWatchlist() {
    watchlistLoading.value = true
    watchlistError.value = null
    try {
      watchlist.value = await stockApi.getWatchlist()
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
    syncLoading.value = true
    try {
      const response = await stockApi.syncAllPrices()
      await fetchWatchlist()
      return response
    } catch (error) {
      throw new Error(error.message)
    } finally {
      syncLoading.value = false
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
      filterResults.value = results
      filterMetadata.value = metadata
    } catch (error) {
      filterError.value = error.message
    } finally {
      filterLoading.value = false
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
    watchlistLoading,
    filterLoading,
    syncLoading,
    watchlistError,
    filterError,
    passedStocks,
    failedStocks,
    fetchWatchlist,
    fetchFilterResults,
    addToWatchlist,
    deleteFromWatchlist,
    syncAllPrices,
    evaluateStock,
    getAiStockExplain
  }
})
