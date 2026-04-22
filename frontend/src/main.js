import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { setUnauthorizedHandler } from '@/api/index'
import { useAuthStore } from '@/stores/authStore'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

setUnauthorizedHandler(({ redirect }) => {
  const authStore = useAuthStore(pinia)
  authStore.clearSession()

  if (router.currentRoute.value.path.startsWith('/login')) {
    return
  }
  router.replace({ path: '/login', query: { redirect } })
})

app.mount('#app')
