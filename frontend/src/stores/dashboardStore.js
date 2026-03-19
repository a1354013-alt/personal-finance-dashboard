import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getDashboardSummary, getAiSummary } from '@/api/dashboard'

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
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchAiSummary() {
    try {
      const result = await getAiSummary()
      aiSummary.value = result.summary
    } catch (e) {
      aiSummary.value = '無法取得 AI 摘要'
    }
  }

  return {
    summary, aiSummary, loading, error,
    fetchSummary, fetchAiSummary,
  }
})
