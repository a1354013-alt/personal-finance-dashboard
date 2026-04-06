/**
 * 認證相關 API 呼叫 (v0.4.1)
 */
import api from './index'

export default {
  /**
   * 使用者登入
   * @param {string} email 
   * @param {string} password 
   */
  login(email, password) {
    return api.post('/auth/login', { email, password })
  },

  /**
   * 使用者註冊
   * @param {string} email 
   * @param {string} password 
   */
  register(email, password) {
    return api.post('/auth/register', { email, password })
  },

  /**
   * 取得當前登入使用者資訊
   */
  me() {
    return api.get('/auth/me')
  }
}
