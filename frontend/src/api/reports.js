import api from './index'

export function exportMonthlyReport(month, format) {
  return api.get('/reports/monthly', {
    params: { month, format },
    responseType: 'blob'
  })
}
