import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAiSummary, getBudgetAdvice, getDashboardCharts, getDashboardSummary } from '@/api/dashboard'
import { normalizeAiSummary, normalizeBudgetAdvice, normalizeDashboardCharts, normalizeDashboardSummary } from '@/api/contracts'
import i18n from '@/i18n'
import { toErrorMessage } from '@/stores/storeUtils'

export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref(null)
  const charts = ref(null)
  const aiSummary = ref('')
  const aiSummaryLoading = ref(false)
  const aiSummaryError = ref(null)
  const budgetAdvice = ref('')
  const budgetAdviceLoading = ref(false)
  const budgetAdviceError = ref(null)
  const loading = ref(false)
  const chartsLoading = ref(false)
  const error = ref(null)
  const chartsError = ref(null)

  async function fetchSummary() {
    loading.value = true
    error.value = null
    try {
      const result = await getDashboardSummary()
      summary.value = normalizeDashboardSummary(result)
    } catch (err) {
      summary.value = null
      error.value = toErrorMessage(err, i18n.global.t('dashboard.errors.summary'))
    } finally {
      loading.value = false
    }
  }

  async function fetchCharts() {
    chartsLoading.value = true
    chartsError.value = null
    try {
      const result = await getDashboardCharts()
      charts.value = normalizeDashboardCharts(result)
    } catch (err) {
      charts.value = null
      chartsError.value = toErrorMessage(err, i18n.global.t('dashboard.errors.charts'))
    } finally {
      chartsLoading.value = false
    }
  }

  async function fetchAiSummary() {
    aiSummaryLoading.value = true
    aiSummaryError.value = null
    aiSummary.value = ''
    try {
      const result = await getAiSummary()
      aiSummary.value = normalizeAiSummary(result)
      if (!aiSummary.value) {
        aiSummaryError.value = i18n.global.t('dashboard.errors.aiSummary')
      }
    } catch (error) {
      aiSummaryError.value = toErrorMessage(error, i18n.global.t('dashboard.errors.aiSummary'))
    } finally {
      aiSummaryLoading.value = false
    }
  }

  async function fetchBudgetAdvice() {
    budgetAdviceLoading.value = true
    budgetAdviceError.value = null
    budgetAdvice.value = ''
    try {
      const result = await getBudgetAdvice()
      budgetAdvice.value = normalizeBudgetAdvice(result)
      if (!budgetAdvice.value) {
        budgetAdviceError.value = i18n.global.t('dashboard.errors.budgetAdvice')
      }
    } catch (e) {
      budgetAdvice.value = ''
      budgetAdviceError.value = toErrorMessage(e, i18n.global.t('dashboard.errors.budgetAdvice'))
    } finally {
      budgetAdviceLoading.value = false
    }
  }

  return {
    summary,
    charts,
    aiSummary,
    aiSummaryLoading,
    aiSummaryError,
    budgetAdvice,
    budgetAdviceLoading,
    budgetAdviceError,
    loading,
    chartsLoading,
    error,
    chartsError,
    fetchSummary,
    fetchCharts,
    fetchAiSummary,
    fetchBudgetAdvice
  }
})
