import api from './index'

/**
 * 預算模組 API (v0.6.0)
 */

export const getBudgets = () => api.get('/budgets')
export const createBudget = (data) => api.post('/budgets', data)
export const deleteBudget = (id) => api.delete(`/budgets/${id}`)
