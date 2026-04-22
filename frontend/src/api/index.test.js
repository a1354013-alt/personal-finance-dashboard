import { describe, expect, it, vi, beforeEach } from 'vitest'

import api, { currentFullPath, isAuthRoute, setUnauthorizedHandler } from '@/api'

function getResponseRejectedHandler() {
  const handler = api?.interceptors?.response?.handlers?.[0]?.rejected
  if (typeof handler !== 'function') {
    throw new Error('Axios response rejected interceptor not found.')
  }
  return handler
}

describe('api/index (401 flow)', () => {
  beforeEach(() => {
    setUnauthorizedHandler(null)
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('isAuthRoute matches login/register only', () => {
    expect(isAuthRoute('/auth/login')).toBe(true)
    expect(isAuthRoute('/auth/register')).toBe(true)
    expect(isAuthRoute('/auth/me')).toBe(false)
    expect(isAuthRoute('/expenses')).toBe(false)
  })

  it('currentFullPath returns a stable string in browser env', () => {
    window.history.pushState({}, '', '/stocks?x=1#hash')
    expect(currentFullPath()).toBe('/stocks?x=1#hash')
  })

  it('triggers unauthorized handler once for non-auth 401 responses', async () => {
    const onUnauthorized = vi.fn()
    setUnauthorizedHandler(onUnauthorized)

    const rejected = getResponseRejectedHandler()

    window.history.pushState({}, '', '/expenses')
    const error = { response: { status: 401, data: { detail: 'nope' } }, config: { url: '/expenses' } }

    await rejected(error).catch(() => null)
    await rejected(error).catch(() => null)

    expect(onUnauthorized).toHaveBeenCalledTimes(1)
    expect(onUnauthorized).toHaveBeenCalledWith({ redirect: '/expenses' })
  })

  it('does not trigger unauthorized handler for /auth/login 401', async () => {
    const onUnauthorized = vi.fn()
    setUnauthorizedHandler(onUnauthorized)

    const rejected = getResponseRejectedHandler()

    const error = { response: { status: 401, data: { detail: 'bad credentials' } }, config: { url: '/auth/login' } }
    await rejected(error).catch(() => null)

    expect(onUnauthorized).not.toHaveBeenCalled()
  })
})
