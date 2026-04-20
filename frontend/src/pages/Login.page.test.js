import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import Login from '@/pages/Login.vue'
import { useAuthStore } from '@/stores/authStore'

const pushMock = vi.fn()

vi.mock('vue-router', async () => {
  const actual = await vi.importActual('vue-router')
  return {
    ...actual,
    useRoute: () => ({ query: { redirect: '/stocks' } }),
    useRouter: () => ({ push: pushMock })
  }
})

describe('Login page', () => {
  beforeEach(() => {
    pushMock.mockReset()
  })

  it('redirects on login success', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useAuthStore()
    store.login = vi.fn(async () => true)

    const wrapper = mount(Login, {
      global: {
        plugins: [pinia],
        stubs: { RouterLink: { template: '<a />' } }
      }
    })

    await wrapper.find('#login-email').setValue('demo@example.com')
    await wrapper.find('#login-password').setValue('demo1234')
    await wrapper.find('form').trigger('submit')

    expect(store.login).toHaveBeenCalledWith('demo@example.com', 'demo1234')
    expect(pushMock).toHaveBeenCalledWith('/stocks')
  })

  it('does not redirect on login failure', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useAuthStore()
    store.login = vi.fn(async () => false)

    const wrapper = mount(Login, {
      global: {
        plugins: [pinia],
        stubs: { RouterLink: { template: '<a />' } }
      }
    })

    await wrapper.find('#login-email').setValue('demo@example.com')
    await wrapper.find('#login-password').setValue('wrong')
    await wrapper.find('form').trigger('submit')

    expect(pushMock).not.toHaveBeenCalled()
  })
})
