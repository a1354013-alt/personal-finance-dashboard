import api from './index'

/**
 * Budgets API.
 */
export const getBudgets = () => api.get('/budgets')
// POST /budgets is create-or-update by (user, category).
export const upsertBudget = (data) => api.post('/budgets', data)
export const deleteBudget = (id) => api.delete(`/budgets/${id}`)
