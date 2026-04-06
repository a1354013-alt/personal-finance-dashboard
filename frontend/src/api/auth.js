import api from './index'

/**
 * 認證模組 API (v0.6.1)
 */

export const login = (data) => api.post('/auth/login', data)
export const register = (data) => api.post('/auth/register', data)
export const getMe = () => api.get('/auth/me')
