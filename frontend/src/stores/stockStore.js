import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getWatchlist, getFilterResults } from '@/api/stocks'

export const useStockStore = defineStore('stock', () => {
  const watchlist = ref([])
  const filterResults = ref([])
  
  // 點 5 (v0.3.0): 拆分 loading
  const watchlistLoading = ref(false)
  const filterLoading = ref(false)
  
  // 點 1 (v0.3.1): 拆分錯誤狀態管理，避免覆蓋
  const watchlistError = ref(null)
  const filterError = ref(null)

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
    watchlistError.value = null
    try {
      watchlist.value = await getWatchlist()
    } catch (e) {
      watchlistError.value = e.message
    } finally {
      watchlistLoading.value = false
    }
  }

  async function fetchFilterResults() {
    filterLoading.value = true
    filterError.value = null
    try {
      filterResults.value = await getFilterResults()
    } catch (e) {
      filterError.value = e.message
    } finally {
      filterLoading.value = false
    }
  }

  return {
    watchlist, filterResults,
    watchlistLoading, filterLoading,
    watchlistError, filterError,
    passedStocks, failedStocks,
    fetchWatchlist, fetchFilterResults,
  }
})
