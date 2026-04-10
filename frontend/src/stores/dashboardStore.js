import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAiSummary, getDashboardSummary } from '@/api/dashboard'

export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref(null)
  const aiSummary = ref('')
  const loading = ref(false)
  const error = ref(null)

  async function fetchSummary() {
    loading.value = true
    error.value = null
    try {
      summary.value = await getDashboardSummary()
    } catch (error) {
      summary.value = null
      error.value = error.message || 'Unable to load dashboard summary.'
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
    fetchSummary,
    fetchAiSummary
  }
})
