import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getWatchlist, getFilterResults } from '@/api/stocks'

export const useStockStore = defineStore('stock', () => {
  const watchlist = ref([])
  const filterResults = ref([])
  const loading = ref(false)
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
    loading.value = true
    error.value = null
    try {
      watchlist.value = await getWatchlist()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchFilterResults() {
    loading.value = true
    error.value = null
    try {
      filterResults.value = await getFilterResults()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return {
    watchlist, filterResults, loading, error,
    passedStocks, failedStocks,
    fetchWatchlist, fetchFilterResults,
  }
})
