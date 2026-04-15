import { describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/auth', () => ({
  login: vi.fn(async () => ({ access_token: 'token-123', user: { id: 1, email: 'a@example.com' } })),
  register: vi.fn(async () => ({})),
  getMe: vi.fn(async () => ({ id: 1, email: 'a@example.com' }))
}))

import { useAuthStore } from '@/stores/authStore'
import { login as loginRequest } from '@/api/auth'

describe('authStore', () => {
  it('login persists token and user', async () => {
    setActivePinia(createPinia())
    const store = useAuthStore()

    const ok = await store.login('a@example.com', 'password123')
    expect(ok).toBe(true)
    expect(loginRequest).toHaveBeenCalled()
    expect(store.isAuthenticated).toBe(true)
    expect(localStorage.getItem('token')).toBe('token-123')
    expect(JSON.parse(localStorage.getItem('user'))).toMatchObject({ email: 'a@example.com' })
  })

  it('clearSession clears persisted data', () => {
    setActivePinia(createPinia())
    const store = useAuthStore()
    store.token = 'x'
    store.user = { id: 1, email: 'x@example.com' }
    store.persistSession()

    store.clearSession()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
  })
})

