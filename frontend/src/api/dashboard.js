import api from './index'

export function getDashboardSummary() {
  return api.get('/dashboard/summary')
}

export function getDashboardCharts() {
  return api.get('/dashboard/charts')
}

export function getAiSummary() {
  return api.get('/ai/summary')
}

export function getBudgetAdvice() {
  return api.get('/ai/budget-advice')
}
