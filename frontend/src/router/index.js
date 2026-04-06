/**
 * 路由設定 (v0.6.0)
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import Dashboard from '@/pages/Dashboard.vue'
import Expenses from '@/pages/Expenses.vue'
import Stocks from '@/pages/Stocks.vue'
import Budgets from '@/pages/Budgets.vue'
import Login from '@/pages/Login.vue'
import Register from '@/pages/Register.vue'

const routes = [
  { path: '/',          name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/expenses',  name: 'Expenses',  component: Expenses,  meta: { requiresAuth: true } },
  { path: '/stocks',    name: 'Stocks',    component: Stocks,    meta: { requiresAuth: true } },
  { path: '/budgets',   name: 'Budgets',   component: Budgets,   meta: { requiresAuth: true } },
  { path: '/login',     name: 'Login',     component: Login },
  { path: '/register',  name: 'Register',  component: Register },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const token = localStorage.getItem('token')
  
  // 若有 token 但無 user 資訊，嘗試同步
  if (token && !authStore.user) {
    try {
      await authStore.fetchMe()
    } catch (e) {
      localStorage.removeItem('token')
      return next('/login')
    }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
