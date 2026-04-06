<template>
  <div class="auth-container">
    <div class="card auth-card">
      <h2>🔐 使用者登入</h2>
      <p style="font-size:13px; color:#888; margin-bottom:20px;">歡迎回來！請輸入您的帳號密碼。</p>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>Email</label>
          <input v-model="form.email" type="email" required placeholder="example@mail.com" />
        </div>
        <div class="form-group">
          <label>密碼</label>
          <input v-model="form.password" type="password" required placeholder="請輸入密碼" />
        </div>
        
        <div v-if="authStore.error" class="error-msg" style="margin-top:10px;">{{ authStore.error }}</div>
        
        <button class="btn btn-primary" style="width:100%; margin-top:20px;" :disabled="authStore.loading">
          {{ authStore.loading ? '登入中...' : '登入' }}
        </button>
      </form>

      <div style="margin-top:20px; text-align:center; font-size:14px;">
        尚未有帳號？ <router-link to="/register">立即註冊</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  email: '',
  password: ''
})

async function handleLogin() {
  const success = await authStore.login(form.value.email, form.value.password)
  if (success) {
    router.push('/')
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 70vh;
}
.auth-card {
  width: 100%;
  max-width: 400px;
  padding: 30px;
}
</style>
