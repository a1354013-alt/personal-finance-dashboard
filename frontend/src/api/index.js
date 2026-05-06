import axios from 'axios'

let unauthorizedHandler = null
let lastUnauthorizedAt = 0
let refreshInFlight = null

export function isAuthRoute(url) {
  const value = typeof url === 'string' ? url : ''
  return value.includes('/auth/login') || value.includes('/auth/register') || value.includes('/auth/me') || value.includes('/auth/refresh')
}

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = typeof handler === 'function' ? handler : null
  lastUnauthorizedAt = 0
}

function safeLocalStorageGetItem(key) {
  if (typeof window === 'undefined' || typeof localStorage === 'undefined') return null
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function safeLocalStorageSetItem(key, value) {
  if (typeof window === 'undefined' || typeof localStorage === 'undefined') return
  try {
    localStorage.setItem(key, value)
  } catch {
    // ignore storage failures
  }
}

function clearBrowserSession() {
  if (typeof localStorage === 'undefined') return
  try {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  } catch {
    // ignore storage failures (private mode / quota / blocked)
  }
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

const refreshClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use(
  (config) => {
    const token = safeLocalStorageGetItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

async function tryRefreshSession() {
  const refreshToken = safeLocalStorageGetItem('refresh_token')
  if (!refreshToken) return false

  if (!refreshInFlight) {
    refreshInFlight = refreshClient
      .post('/auth/refresh', { refresh_token: refreshToken })
      .then((response) => {
        const data = response.data
        safeLocalStorageSetItem('token', data.access_token)
        safeLocalStorageSetItem('refresh_token', data.refresh_token)
        safeLocalStorageSetItem('user', JSON.stringify(data.user))
        return true
      })
      .catch(() => {
        clearBrowserSession()
        return false
      })
      .finally(() => {
        refreshInFlight = null
      })
  }

  return refreshInFlight
}

api.interceptors.response.use(
  (response) => {
    if (response.config?.responseType === 'blob') {
      return {
        data: response.data,
        headers: response.headers
      }
    }
    return response.data
  },
  async (error) => {
    const originalRequest = error.config || {}
    const isUnauthorized = error.response?.status === 401

    if (isUnauthorized && !isAuthRoute(originalRequest.url) && !originalRequest._retriedAfterRefresh) {
      originalRequest._retriedAfterRefresh = true
      const refreshed = await tryRefreshSession()
      if (refreshed) {
        const newToken = safeLocalStorageGetItem('token')
        if (newToken) {
          originalRequest.headers = originalRequest.headers || {}
          originalRequest.headers.Authorization = `Bearer ${newToken}`
        }
        return api(originalRequest)
      }
    }

    if (isUnauthorized && !isAuthRoute(originalRequest.url)) {
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
