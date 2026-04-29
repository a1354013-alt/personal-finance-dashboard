<template>
  <section class="card onboarding-card">
    <div>
      <p class="eyebrow">{{ t('dashboard.onboarding.eyebrow') }}</p>
      <h2>{{ title }}</h2>
      <p class="onboarding-copy">{{ description }}</p>
    </div>
    <ol class="steps">
      <li v-for="step in steps" :key="step">{{ step }}</li>
    </ol>
  </section>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
  steps: { type: Array, default: () => [] }
})
</script>

<style scoped>
.onboarding-card {
  display: grid;
  gap: 18px;
  background:
    radial-gradient(circle at top right, rgba(228, 164, 93, 0.18), transparent 34%),
    linear-gradient(135deg, #102b44 0%, #1f4765 100%);
  color: #f8fbff;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(255, 233, 203, 0.92);
}

.onboarding-copy {
  margin: 0;
  color: rgba(235, 243, 251, 0.92);
  line-height: 1.6;
}

.steps {
  margin: 0;
  padding-left: 20px;
  display: grid;
  gap: 8px;
}
</style>
