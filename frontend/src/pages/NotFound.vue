<template>
  <div class="auth-container">
    <div class="card auth-card">
      <h2>{{ t('notFound.title') }}</h2>
      <p class="auth-subtitle">{{ t('notFound.subtitle') }}</p>
      <router-link class="btn btn-primary auth-submit" to="/">{{ t('common.backToDashboard') }}</router-link>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
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
  max-width: 520px;
  padding: 30px;
  text-align: center;
}

.auth-subtitle {
  margin-bottom: 20px;
  color: #666;
  font-size: 14px;
}

.auth-submit {
  text-decoration: none;
}
</style>
