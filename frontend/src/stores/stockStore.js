import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import * as stockApi from '@/api/stocks'
import i18n from '@/i18n'
import {
  normalizeFilterMetadata,
  normalizeFundamentalsFilterResult,
  normalizeStockHolding,
  normalizeStockAiAnalysis,
  normalizeStockDashboard,
  normalizeStockAlert,
  normalizeStockIndicators,
  normalizeStockPortfolio,
  normalizeWatchlistItem
} from '@/api/contracts'
import { toErrorMessage } from '@/stores/storeUtils'

export const useStockStore = defineStore('stock', () => {
  const watchlist = ref([])
  const filterResults = ref([])
  const filterMetadata = ref(null)
  const dashboard = ref(null)
  const fundamentalsSyncing = ref(false)
  const fundamentalsError = ref(null)
  const syncingFundamentalsCodes = ref([])
  const aiAnalysisById = ref({})
  const aiAnalysisError = ref(null)
  const analyzingIds = ref([])
  const indicatorsByItemId = ref({})
  const indicatorsLoadingIds = ref([])
  const indicatorsError = ref(null)
  const alerts = ref([])
  const alertsLoading = ref(false)
  const alertsChecking = ref(false)
  const alertsError = ref(null)
  const holdings = ref([])
  const portfolio = ref(null)
  const holdingsLoading = ref(false)
  const holdingsSaving = ref(false)
  const holdingsDeletingIds = ref([])
  const portfolioLoading = ref(false)
  const holdingsError = ref(null)

  const watchlistLoading = ref(false)
  const filterLoading = ref(false)
  const dashboardLoading = ref(false)
  const syncAllLoading = ref(false)
  const syncingCodes = ref([])
  const syncingItemIds = ref([])
  const deleting = ref(false)

  const watchlistError = ref(null)
  const filterError = ref(null)

  const passedStocks = computed(() => filterResults.value.filter((stock) => stock.passed))
  const failedStocks = computed(() => filterResults.value.filter((stock) => !stock.passed))
  const selectedStockCode = computed(() => dashboard.value?.selected_stock_code || watchlist.value[0]?.stock_code || null)
  const selectedWatchlistItem = computed(() => watchlist.value.find((item) => item.stock_code === selectedStockCode.value) || watchlist.value[0] || null)
  const selectedIndicators = computed(() => {
    const itemId = selectedWatchlistItem.value?.id
    return itemId ? indicatorsByItemId.value[itemId] || null : null
  })

  async function fetchHoldings() {
    holdingsLoading.value = true
    holdingsError.value = null
    try {
      const response = await stockApi.getStockHoldings()
      holdings.value = Array.isArray(response) ? response.map(normalizeStockHolding).filter(Boolean) : []
      return holdings.value
    } catch (error) {
      holdings.value = []
      holdingsError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      holdingsLoading.value = false
    }
  }

  async function fetchPortfolio() {
    portfolioLoading.value = true
    holdingsError.value = null
    try {
      const response = await stockApi.getStockPortfolio()
      portfolio.value = normalizeStockPortfolio(response)
      return portfolio.value
    } catch (error) {
      portfolio.value = null
      holdingsError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      portfolioLoading.value = false
    }
  }

  async function refreshPortfolioWorkspace() {
    await Promise.allSettled([fetchHoldings(), fetchPortfolio()])
  }

  async function createHolding(payload) {
    holdingsSaving.value = true
    holdingsError.value = null
    try {
      const response = await stockApi.createStockHolding(payload)
      const normalized = normalizeStockHolding(response)
      await refreshPortfolioWorkspace()
      return normalized || response
    } catch (error) {
      holdingsError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      holdingsSaving.value = false
    }
  }

  async function updateHolding(holdingId, payload) {
    holdingsSaving.value = true
    holdingsError.value = null
    try {
      const response = await stockApi.updateStockHolding(holdingId, payload)
      const normalized = normalizeStockHolding(response)
      await refreshPortfolioWorkspace()
      return normalized || response
    } catch (error) {
      holdingsError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      holdingsSaving.value = false
    }
  }

  function isHoldingDeleting(id) {
    return holdingsDeletingIds.value.includes(Number(id))
  }

  async function deleteHolding(holdingId) {
    const numericId = Number(holdingId)
    if (!Number.isFinite(numericId) || isHoldingDeleting(numericId)) {
      return null
    }
    holdingsDeletingIds.value.push(numericId)
    holdingsError.value = null
    try {
      await stockApi.deleteStockHolding(numericId)
      await refreshPortfolioWorkspace()
      return true
    } catch (error) {
      holdingsError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      holdingsDeletingIds.value = holdingsDeletingIds.value.filter((id) => id !== numericId)
    }
  }

  async function fetchWatchlist() {
    watchlistLoading.value = true
    watchlistError.value = null
    try {
      const result = await stockApi.getWatchlist()
      watchlist.value = Array.isArray(result) ? result.map(normalizeWatchlistItem).filter(Boolean) : []
    } catch (error) {
      watchlist.value = []
      watchlistError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
    } finally {
      watchlistLoading.value = false
    }
  }

  async function fetchDashboard(selectedCode = null) {
    dashboardLoading.value = true
    watchlistError.value = null
    try {
      const result = await stockApi.getStockDashboard(selectedCode)
      dashboard.value = normalizeStockDashboard(result)
      watchlist.value = dashboard.value?.watchlist || []
      await refreshIndicatorsForWatchlist()
      const aiExplanation = dashboard.value?.ai_explanation
      if (import.meta.env.DEV && aiExplanation?.request_id) {
        console.info('[stocks.ai_explanation]', {
          stock_code: aiExplanation.stock_code,
          status: aiExplanation.status,
          request_id: aiExplanation.request_id
        })
      }
    } catch (error) {
      dashboard.value = null
      watchlistError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
    } finally {
      dashboardLoading.value = false
    }
  }

  async function addToWatchlist(stockCode) {
    watchlistError.value = null
    try {
      const response = await stockApi.addToWatchlist(stockCode)
      await fetchDashboard(response.stock_code)
      return normalizeWatchlistItem(response) || response
    } catch (error) {
      watchlistError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    }
  }

  async function deleteFromWatchlist(id) {
    try {
      if (deleting.value) return null
      deleting.value = true
      watchlistError.value = null
      await stockApi.deleteFromWatchlist(id)
      await fetchDashboard()
    } catch (error) {
      watchlistError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      deleting.value = false
    }
  }

  async function syncAllPrices() {
    syncAllLoading.value = true
    watchlistError.value = null
    try {
      const response = await stockApi.syncAllPrices()
      await fetchDashboard(selectedStockCode.value)
      return response
    } catch (error) {
      watchlistError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
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
    watchlistError.value = null
    try {
      const response = await stockApi.syncSinglePrice(stockCode)
      await fetchDashboard(stockCode)
      return response
    } catch (error) {
      watchlistError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      syncingCodes.value = syncingCodes.value.filter((code) => code !== stockCode)
    }
  }

  function isIndicatorLoading(id) {
    return indicatorsLoadingIds.value.includes(Number(id))
  }

  async function fetchStockIndicators(watchlistItemId) {
    const numericId = Number(watchlistItemId)
    if (!Number.isFinite(numericId) || isIndicatorLoading(numericId)) {
      return null
    }
    indicatorsLoadingIds.value.push(numericId)
    indicatorsError.value = null
    try {
      const response = await stockApi.fetchStockIndicators(numericId)
      const normalized = normalizeStockIndicators(response)
      if (normalized) {
        indicatorsByItemId.value = { ...indicatorsByItemId.value, [numericId]: normalized }
      }
      return normalized
    } catch (error) {
      indicatorsError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      indicatorsLoadingIds.value = indicatorsLoadingIds.value.filter((id) => id !== numericId)
    }
  }

  async function refreshIndicatorsForWatchlist() {
    const ids = watchlist.value.map((item) => item.id).filter((id) => Number.isFinite(Number(id)))
    await Promise.allSettled(ids.map((id) => fetchStockIndicators(id)))
  }

  async function listStockAlerts() {
    alertsLoading.value = true
    alertsError.value = null
    try {
      const response = await stockApi.listStockAlerts()
      alerts.value = Array.isArray(response) ? response.map(normalizeStockAlert).filter(Boolean) : []
      return alerts.value
    } catch (error) {
      alerts.value = []
      alertsError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      alertsLoading.value = false
    }
  }

  async function createStockAlert(watchlistItemId, payload) {
    alertsError.value = null
    try {
      const response = await stockApi.createStockAlert(watchlistItemId, payload)
      const normalized = normalizeStockAlert(response)
      if (normalized) {
        alerts.value = [normalized, ...alerts.value.filter((alert) => alert.id !== normalized.id)]
      }
      return normalized
    } catch (error) {
      alertsError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    }
  }

  async function updateStockAlert(alertId, payload) {
    alertsError.value = null
    try {
      const response = await stockApi.updateStockAlert(alertId, payload)
      const normalized = normalizeStockAlert(response)
      if (normalized) {
        alerts.value = alerts.value.map((alert) => (alert.id === normalized.id ? normalized : alert))
      }
      return normalized
    } catch (error) {
      alertsError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    }
  }

  async function deleteStockAlert(alertId) {
    alertsError.value = null
    try {
      await stockApi.deleteStockAlert(alertId)
      alerts.value = alerts.value.filter((alert) => alert.id !== Number(alertId))
    } catch (error) {
      alertsError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    }
  }

  async function checkStockAlerts() {
    alertsChecking.value = true
    alertsError.value = null
    try {
      const response = await stockApi.checkStockAlerts()
      await listStockAlerts()
      return response
    } catch (error) {
      alertsError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      alertsChecking.value = false
    }
  }

  function isItemSyncing(id) {
    return syncingItemIds.value.includes(Number(id))
  }

  async function syncWatchlistItem(id) {
    const numericId = Number(id)
    if (!Number.isFinite(numericId) || isItemSyncing(numericId)) {
      return null
    }
    syncingItemIds.value.push(numericId)
    watchlistError.value = null
    try {
      const response = await stockApi.syncWatchlistItem(numericId)
      const normalized = normalizeWatchlistItem(response)
      if (normalized) {
        watchlist.value = watchlist.value.map((item) => (item.id === normalized.id ? normalized : item))
        await fetchDashboard(normalized.stock_code)
        await fetchStockIndicators(normalized.id)
      }
      return normalized || response
    } catch (error) {
      watchlistError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      syncingItemIds.value = syncingItemIds.value.filter((itemId) => itemId !== numericId)
    }
  }

  function isAnalyzing(id) {
    return analyzingIds.value.includes(Number(id))
  }

  async function analyzeWatchlistItem(id) {
    const numericId = Number(id)
    if (!Number.isFinite(numericId) || isAnalyzing(numericId)) {
      return null
    }
    analyzingIds.value.push(numericId)
    aiAnalysisError.value = null
    try {
      const response = await stockApi.analyzeWatchlistItem(numericId)
      const normalized = normalizeStockAiAnalysis(response)
      if (normalized) {
        aiAnalysisById.value = { ...aiAnalysisById.value, [numericId]: normalized }
        await fetchDashboard(normalized.stock_code)
      }
      return normalized || response
    } catch (error) {
      aiAnalysisError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      analyzingIds.value = analyzingIds.value.filter((itemId) => itemId !== numericId)
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
      filterResults.value = []
      filterMetadata.value = null
      filterError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
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
      fundamentalsError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      fundamentalsSyncing.value = false
    }
  }

  function isSingleFundamentalsSyncing(stockCode) {
    return syncingFundamentalsCodes.value.includes(String(stockCode || '').toUpperCase())
  }

  async function syncSingleFundamentals(stockCode, { force = false } = {}) {
    const normalizedCode = String(stockCode || '').toUpperCase()
    if (!normalizedCode || isSingleFundamentalsSyncing(normalizedCode)) {
      return null
    }

    syncingFundamentalsCodes.value.push(normalizedCode)
    fundamentalsError.value = null
    try {
      const response = await stockApi.syncSingleFundamentals(normalizedCode, { force })
      await Promise.all([
        fetchDashboard(normalizedCode),
        fetchFilterResults()
      ])
      return response
    } catch (error) {
      fundamentalsError.value = toErrorMessage(error, i18n.global.t('common.unknownError'))
      throw error
    } finally {
      syncingFundamentalsCodes.value = syncingFundamentalsCodes.value.filter((code) => code !== normalizedCode)
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
    dashboard,
    fundamentalsSyncing,
    fundamentalsError,
    syncingFundamentalsCodes,
    aiAnalysisById,
    aiAnalysisError,
    analyzingIds,
    watchlistLoading,
    filterLoading,
    dashboardLoading,
    syncAllLoading,
    syncingCodes,
    syncingItemIds,
    deleting,
    watchlistError,
    filterError,
    passedStocks,
    failedStocks,
    selectedStockCode,
    selectedWatchlistItem,
    selectedIndicators,
    indicatorsByItemId,
    indicatorsLoadingIds,
    indicatorsError,
    alerts,
    alertsLoading,
    alertsChecking,
    alertsError,
    holdings,
    portfolio,
    holdingsLoading,
    holdingsSaving,
    holdingsDeletingIds,
    portfolioLoading,
    holdingsError,
    fetchWatchlist,
    fetchHoldings,
    fetchPortfolio,
    refreshPortfolioWorkspace,
    fetchDashboard,
    fetchFilterResults,
    fetchStockIndicators,
    refreshIndicatorsForWatchlist,
    listStockAlerts,
    createStockAlert,
    updateStockAlert,
    deleteStockAlert,
    createHolding,
    updateHolding,
    deleteHolding,
    checkStockAlerts,
    syncFundamentals,
    syncSingleFundamentals,
    addToWatchlist,
    deleteFromWatchlist,
    syncAllPrices,
    syncSinglePrice,
    syncWatchlistItem,
    analyzeWatchlistItem,
    isSingleFundamentalsSyncing,
    isSingleSyncing,
    isItemSyncing,
    isHoldingDeleting,
    isIndicatorLoading,
    isAnalyzing,
    evaluateStock,
    getAiStockExplain
  }
})
