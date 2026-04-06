/**
 * Axios 基礎設定 (v0.4.0: JWT 攔截器)
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// 點 10: 請求攔截器，自動夾帶 JWT Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 回應攔截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 點 10: 處理 401 登入失效 (可由 router 處理或此處清除 localStorage)
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
    const msg = error.response?.data?.detail || error.message || '請求失敗'
    console.error('[API Error]', msg)
    return Promise.reject(new Error(msg))
  }
)

export default api
