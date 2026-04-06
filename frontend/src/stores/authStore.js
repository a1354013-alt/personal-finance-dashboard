/**
 * 認證狀態管理 (v0.4.1)
 */
import { defineStore } from 'pinia'
import authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('token') || null,
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token
  },

  actions: {
    /**
     * 登入
     */
    async login(email, password) {
      this.loading = true
      this.error = null
      try {
        const res = await authApi.login(email, password)
        // 點 4: 統一由 api instance 回傳資料 (axios 攔截器已處理 .data)
        this.token = res.access_token
        this.user = res.user
        
        localStorage.setItem('token', this.token)
        localStorage.setItem('user', JSON.stringify(this.user))
        return true
      } catch (err) {
        this.error = err.message || '登入失敗'
        return false
      } finally {
        this.loading = false
      }
    },

    /**
     * 註冊
     */
    async register(email, password) {
      this.loading = true
      this.error = null
      try {
        await authApi.register(email, password)
        return true
      } catch (err) {
        this.error = err.message || '註冊失敗'
        return false
      } finally {
        this.loading = false
      }
    },

    /**
     * 登出
     */
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },

    /**
     * 同步當前使用者狀態 (點 6)
     */
    async fetchMe() {
      if (!this.token) return
      try {
        const res = await authApi.me()
        this.user = res
        localStorage.setItem('user', JSON.stringify(this.user))
        return true
      } catch (err) {
        // 點 6: 若驗證失敗則清除狀態
        this.logout()
        return false
      }
    }
  }
})
