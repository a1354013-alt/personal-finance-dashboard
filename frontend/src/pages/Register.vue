<template>
  <div class="auth-container">
    <div class="card auth-card">
      <h2>{{ t('auth.createAccount') }}</h2>
      <p class="auth-subtitle">{{ t('auth.registerSubtitle') }}</p>

      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="register-email">{{ t('auth.email') }}</label>
          <input id="register-email" v-model.trim="form.email" type="email" required placeholder="you@example.com" />
        </div>

        <div class="form-group">
          <label for="register-password">{{ t('auth.password') }}</label>
          <input id="register-password" v-model="form.password" type="password" required :placeholder="t('auth.passwordHint')" />
        </div>

        <div class="form-group">
          <label for="register-confirm-password">{{ t('auth.confirmPassword') }}</label>
          <input id="register-confirm-password" v-model="form.confirmPassword" type="password" required :placeholder="t('auth.confirmPassword')" />
        </div>

        <div v-if="formError || authStore.error" class="error-msg">{{ formError || authStore.error }}</div>

        <button class="btn btn-primary auth-submit" :disabled="authStore.loading">
          {{ authStore.loading ? t('auth.registerLoading') : t('auth.registerAction') }}
        </button>
      </form>

      <div class="auth-footer">
        <span>{{ t('auth.alreadyHaveAccount') }}</span>
        <router-link to="/login">{{ t('auth.signIn') }}</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const authStore = useAuthStore()
const formError = ref('')
const { t } = useI18n()

const form = ref({
  email: '',
  password: '',
  confirmPassword: ''
})

async function handleRegister() {
  formError.value = ''

  if (form.value.password !== form.value.confirmPassword) {
    formError.value = t('auth.passwordsDoNotMatch')
    return
  }

  const success = await authStore.register(form.value.email, form.value.password)
  if (success) {
    router.push({ path: '/login', query: { registered: '1' } })
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
