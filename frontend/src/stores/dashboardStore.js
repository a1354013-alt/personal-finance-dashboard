import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAiSummary, getBudgetAdvice, getDashboardSummary } from '@/api/dashboard'
import { normalizeDashboardSummary } from '@/api/contracts'

export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref(null)
  const aiSummary = ref('')
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
      error.value = err.message || 'Unable to load dashboard summary.'
    } finally {
      loading.value = false
    }
  }

  async function fetchAiSummary() {
    try {
      const result = await getAiSummary()
      aiSummary.value = result.summary
    } catch (_error) {
      aiSummary.value = 'Unable to generate the AI summary right now.'
    }
  }

  async function fetchBudgetAdvice() {
    budgetAdviceLoading.value = true
    budgetAdviceError.value = null
    try {
      const result = await getBudgetAdvice()
      budgetAdvice.value = result.advice
    } catch (e) {
      budgetAdvice.value = ''
      budgetAdviceError.value = e.message || 'Unable to load budget advice.'
    } finally {
      budgetAdviceLoading.value = false
    }
  }

  return {
    summary,
    aiSummary,
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
