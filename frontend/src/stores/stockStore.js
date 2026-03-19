import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getWatchlist, getFilterResults } from '@/api/stocks'

export const useStockStore = defineStore('stock', () => {
  const watchlist = ref([])
  const filterResults = ref([])
  
  // 點 5: 將單一 loading 拆為 watchlistLoading 與 filterLoading
  const watchlistLoading = ref(false)
  const filterLoading = ref(false)
  const error = ref(null)

  // 通過篩選的股票
  const passedStocks = computed(() =>
    filterResults.value.filter(s => s.passed)
  )

  // 未通過篩選的股票
  const failedStocks = computed(() =>
    filterResults.value.filter(s => !s.passed)
  )

  async function fetchWatchlist() {
    watchlistLoading.value = true
    error.value = null
    try {
      watchlist.value = await getWatchlist()
    } catch (e) {
      error.value = e.message
    } finally {
      watchlistLoading.value = false
    }
  }

  async function fetchFilterResults() {
    filterLoading.value = true
    error.value = null
    try {
      filterResults.value = await getFilterResults()
    } catch (e) {
      error.value = e.message
    } finally {
      filterLoading.value = false
    }
  }

  return {
    watchlist, filterResults, error,
    watchlistLoading, filterLoading,
    passedStocks, failedStocks,
    fetchWatchlist, fetchFilterResults,
  }
})
