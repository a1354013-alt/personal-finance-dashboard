import api from './index'

/**
 * Budgets API.
 */
export const getBudgets = (month) => api.get('/budgets', { params: { month } })

export const getBudgetSummary = (month) => api.get('/budgets/summary', { params: { month } })

// POST /budgets is create-or-update by (user, month, category).
export const upsertBudget = (data) => api.post('/budgets', data)

export const updateBudget = (id, data) => api.put(`/budgets/${id}`, data)

export const deleteBudget = (id) => api.delete(`/budgets/${id}`)
