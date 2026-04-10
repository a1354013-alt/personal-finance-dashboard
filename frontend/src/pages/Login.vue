<template>
  <div class="auth-container">
    <div class="card auth-card">
      <h2>Sign In</h2>
      <p class="auth-subtitle">Use the demo account or your own registered account to continue.</p>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="login-email">Email</label>
          <input id="login-email" v-model.trim="form.email" type="email" required placeholder="demo@example.com" />
        </div>

        <div class="form-group">
          <label for="login-password">Password</label>
          <input id="login-password" v-model="form.password" type="password" required placeholder="At least 8 characters" />
        </div>

        <div v-if="authStore.error" class="error-msg">{{ authStore.error }}</div>

        <button class="btn btn-primary auth-submit" :disabled="authStore.loading">
          {{ authStore.loading ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>

      <div class="auth-footer">
        <span>Need an account?</span>
        <router-link to="/register">Register</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  email: '',
  password: ''
})

async function handleLogin() {
  const success = await authStore.login(form.value.email, form.value.password)
  if (success) {
    router.push(route.query.redirect || '/')
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
</style>
