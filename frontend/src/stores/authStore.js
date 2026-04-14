import { defineStore } from 'pinia'
import { getMe, login as loginRequest, register as registerRequest } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user') || 'null'),
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
        const response = await loginRequest({ email, password })
        this.token = response.access_token
        this.user = response.user
        this.persistSession()
        return true
      } catch (error) {
        this.error = error.message || 'Login failed.'
        return false
      } finally {
        this.loading = false
      }
    },

    async register(email, password) {
      this.loading = true
      this.error = null

      try {
        await registerRequest({ email, password })
        return true
      } catch (error) {
        this.error = error.message || 'Registration failed.'
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
        this.user = user
        this.persistSession()
        return true
      } catch (error) {
        this.clearSession()
        this.error = error.message || 'Session expired. Please sign in again.'
        return false
      } finally {
        this.loading = false
      }
    }
  }
})
