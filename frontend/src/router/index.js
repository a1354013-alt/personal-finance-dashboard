import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('@/pages/Dashboard.vue'), meta: { requiresAuth: true } },
  { path: '/expenses', name: 'Expenses', component: () => import('@/pages/Expenses.vue'), meta: { requiresAuth: true } },
  { path: '/imports/transactions', name: 'TransactionImport', component: () => import('@/pages/TransactionImport.vue'), meta: { requiresAuth: true } },
  { path: '/stocks', name: 'Stocks', component: () => import('@/pages/Stocks.vue'), meta: { requiresAuth: true } },
  { path: '/budgets', name: 'Budgets', component: () => import('@/pages/Budgets.vue'), meta: { requiresAuth: true } },
  { path: '/login', name: 'Login', component: () => import('@/pages/Login.vue'), meta: { guestOnly: true } },
  { path: '/register', name: 'Register', component: () => import('@/pages/Register.vue'), meta: { guestOnly: true } },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/pages/NotFound.vue') }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (authStore.token && !authStore.user) {
    await authStore.fetchMe()
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return { path: '/' }
  }

  return true
})

export default router
