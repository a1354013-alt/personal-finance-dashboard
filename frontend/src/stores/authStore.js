import { defineStore } from 'pinia'
import { getMe, login as loginRequest, register as registerRequest } from '@/api/auth'
import { normalizeEmail, normalizeUser } from '@/api/contracts'
import { toErrorMessage } from '@/stores/storeUtils'

function safeLocalStorageGetItem(key) {
  if (typeof window === 'undefined' || typeof localStorage === 'undefined') return null
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function safeJsonParse(value) {
  if (!value) return null
  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: normalizeUser(safeJsonParse(safeLocalStorageGetItem('user'))),
    token: safeLocalStorageGetItem('token') || null,
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.token)
  },

  actions: {
    clearSession() {
      this.token = null
      this.user = null
      this.error = null
      this.persistSession()
    },

    persistSession() {
      if (typeof window === 'undefined' || typeof localStorage === 'undefined') return
      if (this.token) {
        try {
          localStorage.setItem('token', this.token)
        } catch {
          // ignore storage failures (private mode / quota / blocked)
        }
      } else {
        try {
          localStorage.removeItem('token')
        } catch {
          // ignore
        }
      }

      if (this.user) {
        try {
          localStorage.setItem('user', JSON.stringify(this.user))
        } catch {
          // ignore
        }
      } else {
        try {
          localStorage.removeItem('user')
        } catch {
          // ignore
        }
      }
    },

    async login(email, password) {
      this.loading = true
      this.error = null

      try {
        const response = await loginRequest({ email: normalizeEmail(email), password })
        this.token = response.access_token
        this.user = normalizeUser(response.user)
        this.persistSession()
        return true
      } catch (error) {
        this.error = toErrorMessage(error, 'Login failed.')
        return false
      } finally {
        this.loading = false
      }
    },

    async register(email, password) {
      this.loading = true
      this.error = null

      try {
        await registerRequest({ email: normalizeEmail(email), password })
        return true
      } catch (error) {
        this.error = toErrorMessage(error, 'Registration failed.')
        return false
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.clearSession()
    },

    async fetchMe() {
      if (!this.token) {
        this.clearSession()
        return false
      }

      this.loading = true
      this.error = null
      try {
        const user = await getMe()
        this.user = normalizeUser(user)
        this.persistSession()
        return true
      } catch (error) {
        this.clearSession()
        this.error = toErrorMessage(error, 'Session expired. Please sign in again.')
        return false
      } finally {
        this.loading = false
      }
    }
  }
})
