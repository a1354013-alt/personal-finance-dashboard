import api from './index'

export const getRecurringTransactions = () => api.get('/recurring-transactions')

export const createRecurringTransaction = (data) => api.post('/recurring-transactions', data)

export const updateRecurringTransaction = (id, data) => api.put(`/recurring-transactions/${id}`, data)

export const deactivateRecurringTransaction = (id) => api.patch(`/recurring-transactions/${id}/deactivate`)

export const deleteRecurringTransaction = (id) => api.delete(`/recurring-transactions/${id}`)
