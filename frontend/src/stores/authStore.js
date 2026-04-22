import { defineStore } from 'pinia'
import { getMe, login as loginRequest, register as registerRequest } from '@/api/auth'
import { normalizeEmail, normalizeUser } from '@/api/contracts'
import { toErrorMessage } from '@/stores/storeUtils'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: normalizeUser(JSON.parse(localStorage.getItem('user') || 'null')),
    token: localStorage.getItem('token') || null,
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
      if (this.token) {
        localStorage.setItem('token', this.token)
      } else {
        localStorage.removeItem('token')
      }

      if (this.user) {
        localStorage.setItem('user', JSON.stringify(this.user))
      } else {
        localStorage.removeItem('user')
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
