import { beforeEach, describe, expect, it, vi } from 'vitest'

function createAxiosClient() {
  const client = vi.fn()
  client.post = vi.fn()
  client.interceptors = {
    request: {
      use: vi.fn()
    },
    response: {
      handlers: [],
      use(fulfilled, rejected) {
        this.handlers.push({ fulfilled, rejected })
      }
    }
  }
  return client
}

describe('api/index refresh flow', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
  })

  it('retries /auth/me after a successful refresh instead of treating it as a terminal auth route', async () => {
    const clients = []

    vi.doMock('axios', () => {
      const create = vi.fn(() => {
        const client = createAxiosClient()
        clients.push(client)
        return client
      })

      return {
        default: { create, __clients: clients },
        create
      }
    })

    localStorage.setItem('token', 'expired-token')
    localStorage.setItem('refresh_token', 'refresh-token')
    localStorage.setItem('user', JSON.stringify({ id: 1, email: 'demo@example.com' }))

    const apiModule = await import('@/api/index.js')
    const api = apiModule.default
    const onUnauthorized = vi.fn()
    apiModule.setUnauthorizedHandler(onUnauthorized)

    const [apiClient, refreshClient] = clients
    refreshClient.post.mockResolvedValue({
      data: {
        access_token: 'fresh-token',
        refresh_token: 'fresh-refresh-token',
        user: { id: 1, email: 'demo@example.com' }
      }
    })
    apiClient.mockResolvedValue({
      data: { id: 1, email: 'demo@example.com' }
    })

    const rejected = api.interceptors.response.handlers[0].rejected
    const result = await rejected({
      response: { status: 401, data: { detail: 'expired' } },
      config: { url: '/auth/me', headers: { Authorization: 'Bearer expired-token' } }
    })

    expect(refreshClient.post).toHaveBeenCalledWith('/auth/refresh', { refresh_token: 'refresh-token' })
    expect(apiClient).toHaveBeenCalledWith(expect.objectContaining({
      url: '/auth/me',
      _retriedAfterRefresh: true,
      headers: expect.objectContaining({
        Authorization: 'Bearer fresh-token'
      })
    }))
    expect(result).toEqual({ data: { id: 1, email: 'demo@example.com' } })
    expect(localStorage.getItem('token')).toBe('fresh-token')
    expect(localStorage.getItem('refresh_token')).toBe('fresh-refresh-token')
    expect(onUnauthorized).not.toHaveBeenCalled()
  })
})
