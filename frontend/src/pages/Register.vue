<template>
  <div class="auth-container">
    <div class="card auth-card">
      <h2>Create Account</h2>
      <p class="auth-subtitle">Passwords must be at least 8 characters long.</p>

      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="register-email">Email</label>
          <input id="register-email" v-model.trim="form.email" type="email" required placeholder="you@example.com" />
        </div>

        <div class="form-group">
          <label for="register-password">Password</label>
          <input id="register-password" v-model="form.password" type="password" required placeholder="At least 8 characters" />
        </div>

        <div class="form-group">
          <label for="register-confirm-password">Confirm Password</label>
          <input id="register-confirm-password" v-model="form.confirmPassword" type="password" required placeholder="Repeat your password" />
        </div>

        <div v-if="successMsg" class="success-msg">{{ successMsg }}</div>
        <div v-if="authStore.error" class="error-msg">{{ authStore.error }}</div>

        <button class="btn btn-primary auth-submit" :disabled="authStore.loading">
          {{ authStore.loading ? 'Creating account...' : 'Register' }}
        </button>
      </form>

      <div class="auth-footer">
        <span>Already have an account?</span>
        <router-link to="/login">Sign In</router-link>
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
    authStore.error = 'Passwords do not match.'
    return
  }

  const success = await authStore.register(form.value.email, form.value.password)
  if (success) {
    successMsg.value = 'Account created. Redirecting to sign in...'
    setTimeout(() => {
      router.push('/login')
    }, 1200)
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
  max-width: 420px;
  padding: 30px;
}

.auth-subtitle {
  margin-bottom: 20px;
  color: #666;
  font-size: 14px;
}

.auth-submit {
  width: 100%;
  margin-top: 20px;
}

.auth-footer {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
}

.success-msg {
  color: #166534;
  font-size: 13px;
  padding: 8px 12px;
  background: #dcfce7;
  border-radius: 6px;
  margin-bottom: 12px;
}
</style>
