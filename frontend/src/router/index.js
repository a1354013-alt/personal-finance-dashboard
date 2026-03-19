import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/pages/Dashboard.vue'
import Expenses from '@/pages/Expenses.vue'
import Stocks from '@/pages/Stocks.vue'

const routes = [
  { path: '/',          name: 'Dashboard', component: Dashboard },
  { path: '/expenses',  name: 'Expenses',  component: Expenses },
  { path: '/stocks',    name: 'Stocks',    component: Stocks },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
