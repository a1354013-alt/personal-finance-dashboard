import axios from 'axios'

let unauthorizedHandler = null
let lastUnauthorizedAt = 0

export function isAuthRoute(url) {
  const value = typeof url === 'string' ? url : ''
  return value.includes('/auth/login') || value.includes('/auth/register') || value.includes('/auth/me')
}

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = typeof handler === 'function' ? handler : null
  lastUnauthorizedAt = 0
}

function clearBrowserSession() {
  if (typeof localStorage === 'undefined') return
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export function currentFullPath() {
  if (typeof window === 'undefined' || !window.location) return '/'
  return `${window.location.pathname}${window.location.search}${window.location.hash}` || '/'
}

function defaultUnauthorizedHandler({ redirect }) {
  clearBrowserSession()
  const encodedRedirect = encodeURIComponent(redirect || '/')
  if (typeof window === 'undefined' || !window.location) return
  if (!window.location.pathname.startsWith('/login')) {
    window.location.assign(`/login?redirect=${encodedRedirect}`)
  }
}

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
    if (error.response?.status === 401 && !isAuthRoute(error.config?.url)) {
      const now = Date.now()
      if (now - lastUnauthorizedAt > 750) {
        lastUnauthorizedAt = now
        const handler = unauthorizedHandler || defaultUnauthorizedHandler
        handler({ redirect: currentFullPath() })
      }
    }

    const message = error.response?.data?.detail || error.message || 'Request failed.'
    console.error('[API Error]', message)
    return Promise.reject(new Error(message))
  }
)

export default api
