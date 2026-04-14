import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})

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

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')

      const currentPath = `${window.location.pathname}${window.location.search}${window.location.hash}`
      const encodedRedirect = encodeURIComponent(currentPath || '/')
      if (!window.location.pathname.startsWith('/login')) {
        window.location.replace(`/login?redirect=${encodedRedirect}`)
      }
    }

    const message = error.response?.data?.detail || error.message || 'Request failed.'
    console.error('[API Error]', message)
    return Promise.reject(new Error(message))
  }
)

export default api
