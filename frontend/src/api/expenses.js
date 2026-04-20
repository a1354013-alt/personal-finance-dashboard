import api from './index'

/**
 * Expenses API.
 * @param {Object} params - Optional filters, e.g. { type }.
 */
export function getExpenses(params = {}) {
  return api.get('/expenses', { params })
}

/**
 * Create a new expense record.
 * @param {Object} data - { amount, category, type, date, note }.
 */
export function createExpense(data) {
  return api.post('/expenses', data)
}

/**
 * Delete an expense record by id.
 * @param {number} id
 */
export function deleteExpense(id) {
  return api.delete(`/expenses/${id}`)
}
