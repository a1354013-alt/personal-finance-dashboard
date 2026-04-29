<template>
  <div class="auth-container">
    <div class="card auth-card">
      <h2>{{ t('auth.signIn') }}</h2>
      <p class="auth-subtitle">{{ t('auth.signInSubtitle') }}</p>
      <div v-if="registered" class="success-msg">{{ t('auth.registeredSuccess') }}</div>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="login-email">{{ t('auth.email') }}</label>
          <input id="login-email" v-model.trim="form.email" type="email" required placeholder="demo@example.com" />
        </div>

        <div class="form-group">
          <label for="login-password">{{ t('auth.password') }}</label>
          <input id="login-password" v-model="form.password" type="password" required :placeholder="t('auth.passwordHint')" />
        </div>

        <div v-if="authStore.error" class="error-msg">{{ authStore.error }}</div>

        <button class="btn btn-primary auth-submit" :disabled="authStore.loading">
          {{ authStore.loading ? t('auth.signInLoading') : t('auth.signInAction') }}
        </button>
      </form>

      <div class="auth-footer">
        <span>{{ t('auth.needAccount') }}</span>
        <router-link to="/register">{{ t('auth.register') }}</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()

const registered = computed(() => route.query.registered === '1')

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

.success-msg {
  color: #166534;
  font-size: 13px;
  padding: 8px 12px;
  background: #dcfce7;
  border-radius: 6px;
  margin-bottom: 12px;
}
</style>
