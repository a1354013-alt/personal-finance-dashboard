import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAiSummary, getDashboardSummary } from '@/api/dashboard'

export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref(null)
  const aiSummary = ref('')
  const loading = ref(false)
  const error = ref(null)

  function normalizeDashboardSummary(payload) {
    if (!payload || typeof payload !== 'object') return null

    return {
      total_income: Number(payload.total_income ?? 0),
      total_expense: Number(payload.total_expense ?? 0),
      net_balance: Number(payload.net_balance ?? 0),
      expense_by_category: Array.isArray(payload.expense_by_category) ? payload.expense_by_category : [],
      monthly_trend: Array.isArray(payload.monthly_trend) ? payload.monthly_trend : [],
      over_budget: Array.isArray(payload.over_budget) ? payload.over_budget : [],
      summary_scope: payload.summary_scope ?? { totals: 'all_time', over_budget: 'current_month' }
    }
  }

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

  return {
    summary,
    aiSummary,
    loading,
    error,
    normalizeDashboardSummary,
    fetchSummary,
    fetchAiSummary
  }
})
