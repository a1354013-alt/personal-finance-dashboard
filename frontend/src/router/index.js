import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/pages/Dashboard.vue'
import Expenses from '@/pages/Expenses.vue'
import Stocks from '@/pages/Stocks.vue'
import Budgets from '@/pages/Budgets.vue'
import Login from '@/pages/Login.vue'
import Register from '@/pages/Register.vue'
import { useAuthStore } from '@/stores/authStore'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/expenses', name: 'Expenses', component: Expenses, meta: { requiresAuth: true } },
  { path: '/stocks', name: 'Stocks', component: Stocks, meta: { requiresAuth: true } },
  { path: '/budgets', name: 'Budgets', component: Budgets, meta: { requiresAuth: true } },
  { path: '/login', name: 'Login', component: Login, meta: { guestOnly: true } },
  { path: '/register', name: 'Register', component: Register, meta: { guestOnly: true } }
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
