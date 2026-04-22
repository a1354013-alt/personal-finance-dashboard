import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAiSummary, getBudgetAdvice, getDashboardSummary } from '@/api/dashboard'
import { normalizeAiSummary, normalizeBudgetAdvice, normalizeDashboardSummary } from '@/api/contracts'
import { toErrorMessage } from '@/stores/storeUtils'

export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref(null)
  const aiSummary = ref('')
  const aiSummaryLoading = ref(false)
  const aiSummaryError = ref(null)
  const budgetAdvice = ref('')
  const budgetAdviceLoading = ref(false)
  const budgetAdviceError = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchSummary() {
    loading.value = true
    error.value = null
    try {
      const result = await getDashboardSummary()
      summary.value = normalizeDashboardSummary(result)
    } catch (err) {
      summary.value = null
      error.value = toErrorMessage(err, 'Unable to load dashboard summary.')
    } finally {
      loading.value = false
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
        aiSummaryError.value = 'Unable to load AI summary.'
      }
    } catch (error) {
      aiSummaryError.value = toErrorMessage(error, 'Unable to load AI summary.')
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
        budgetAdviceError.value = 'Unable to load budget advice.'
      }
    } catch (e) {
      budgetAdvice.value = ''
      budgetAdviceError.value = toErrorMessage(e, 'Unable to load budget advice.')
    } finally {
      budgetAdviceLoading.value = false
    }
  }

  return {
    summary,
    aiSummary,
    aiSummaryLoading,
    aiSummaryError,
    budgetAdvice,
    budgetAdviceLoading,
    budgetAdviceError,
    loading,
    error,
    fetchSummary,
    fetchAiSummary,
    fetchBudgetAdvice
  }
})
