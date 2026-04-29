import api from './index'

export function login(data) {
  return api.post('/auth/login', data)
}

export function register(data) {
  return api.post('/auth/register', data)
}

export function getMe() {
  return api.get('/auth/me')
}

export function refreshToken(refresh_token) {
  return api.post('/auth/refresh', { refresh_token })
}

export function logout(refresh_token) {
  return api.post('/auth/logout', { refresh_token })
}
