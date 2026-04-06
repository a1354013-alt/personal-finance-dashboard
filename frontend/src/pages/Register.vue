<template>
  <div class="auth-container">
    <div class="card auth-card">
      <h2>🆕 使用者註冊</h2>
      <p style="font-size:13px; color:#888; margin-bottom:20px;">歡迎加入！請填寫以下資訊建立帳號。</p>

      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>Email</label>
          <input v-model="form.email" type="email" required placeholder="example@mail.com" />
        </div>
        <div class="form-group">
          <label>密碼</label>
          <input v-model="form.password" type="password" required placeholder="請輸入密碼" />
        </div>
        <div class="form-group">
          <label>確認密碼</label>
          <input v-model="form.confirmPassword" type="password" required placeholder="再次輸入密碼" />
        </div>
        
        <!-- 註冊狀態提示 -->
        <div v-if="successMsg" class="success-msg" style="margin-top:10px;">{{ successMsg }}</div>
        <div v-if="authStore.error" class="error-msg" style="margin-top:10px;">{{ authStore.error }}</div>
        
        <button class="btn btn-primary" style="width:100%; margin-top:20px;" :disabled="authStore.loading">
          {{ authStore.loading ? '註冊中...' : '註冊' }}
        </button>
      </form>

      <div style="margin-top:20px; text-align:center; font-size:14px;">
        已有帳號？ <router-link to="/login">登入</router-link>
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
  password: '',
  confirmPassword: ''
})

const successMsg = ref('')

async function handleRegister() {

  authStore.error = null
  successMsg.value = ''

  if (form.value.password !== form.value.confirmPassword) {
    authStore.error = '兩次密碼輸入不一致'
    return
  }
  
  const success = await authStore.register(form.value.email, form.value.password)
  if (success) {

    successMsg.value = '註冊成功！即將為您跳轉至登入頁面...'
    setTimeout(() => {
      router.push('/login')
    }, 2000)
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
.success-msg {
  background: #dcfce7;
  color: #166534;
  padding: 10px;
  border-radius: 6px;
  font-size: 13px;
}
</style>
