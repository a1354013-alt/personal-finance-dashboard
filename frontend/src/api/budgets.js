import api from './index'

/**
 * Budgets API.
 */
export const getBudgets = () => api.get('/budgets')
export const createBudget = (data) => api.post('/budgets', data)
export const deleteBudget = (id) => api.delete(`/budgets/${id}`)
