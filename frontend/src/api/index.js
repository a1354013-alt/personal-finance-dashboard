/**
 * Axios 基礎設定
 * baseURL 指向 FastAPI 後端（Vite dev server 會透過 proxy 轉發）
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// 請求攔截器
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// 回應攔截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '請求失敗'
    console.error('[API Error]', msg)
    return Promise.reject(new Error(msg))
  }
)

export default api
