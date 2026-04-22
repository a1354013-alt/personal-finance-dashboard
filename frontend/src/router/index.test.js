import { describe, expect, it, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

describe('router auth guards', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('redirects unauthenticated users to /login with redirect query', async () => {
    const { useAuthStore } = await import('@/stores/authStore')
    const store = useAuthStore()
    store.clearSession()

    const router = (await import('@/router')).default

    await router.push('/expenses')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.redirect).toBe('/expenses')
  })

  it('redirects authenticated users away from guest-only pages', async () => {
    const { useAuthStore } = await import('@/stores/authStore')
    const store = useAuthStore()
    store.token = 'token-123'
    store.user = { id: 1, email: 'demo@example.com' }

    const router = (await import('@/router')).default

    await router.push('/login')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/')
  })

  it('calls fetchMe when token exists but user is missing', async () => {
    const { useAuthStore } = await import('@/stores/authStore')
    const store = useAuthStore()
    store.token = 'token-123'
    store.user = null
    store.fetchMe = vi.fn(async () => {
      store.clearSession()
      return false
    })

    const router = (await import('@/router')).default

    await router.push('/budgets')
    await router.isReady()

    expect(store.fetchMe).toHaveBeenCalled()
    expect(router.currentRoute.value.path).toBe('/login')
  })
})
