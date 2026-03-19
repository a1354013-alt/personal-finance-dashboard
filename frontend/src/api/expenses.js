import api from './index'

/**
 * 取得記帳列表
 * @param {Object} params - 可選篩選參數 { type, category }
 */
export function getExpenses(params = {}) {
  return api.get('/expenses', { params })
}

/**
 * 新增記帳記錄
 * @param {Object} data - { amount, category, type, date, note }
 */
export function createExpense(data) {
  return api.post('/expenses', data)
}

/**
 * 刪除記帳記錄
 * @param {number} id
 */
export function deleteExpense(id) {
  return api.delete(`/expenses/${id}`)
}
