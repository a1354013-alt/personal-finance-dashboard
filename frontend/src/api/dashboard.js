import api from './index'

/** 取得 Dashboard 彙整資料 */
export function getDashboardSummary() {
  return api.get('/dashboard/summary')
}

/** 取得 AI 財務摘要 */
export function getAiSummary() {
  return api.get('/ai/summary')
}
