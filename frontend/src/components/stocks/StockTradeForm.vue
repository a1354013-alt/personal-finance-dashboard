<template>
  <section class="card trade-form-card">
    <div class="section-header">
      <div>
        <h2>{{ editingTradeId ? t('stocks.trades.editTitle') : t('stocks.trades.formTitle') }}</h2>
        <p class="helper-text">{{ t('stocks.trades.formSubtitle') }}</p>
      </div>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <form class="form-row trade-form" @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="trade-stock-code">{{ t('stocks.trades.stockCode') }}</label>
        <input id="trade-stock-code" v-model.trim="localForm.stock_code" type="text" placeholder="2330 or AAPL" required />
      </div>
      <div class="form-group">
        <label for="trade-type">{{ t('stocks.trades.tradeType') }}</label>
        <select id="trade-type" v-model="localForm.trade_type">
          <option value="BUY">{{ t('stocks.trades.types.BUY') }}</option>
          <option value="SELL">{{ t('stocks.trades.types.SELL') }}</option>
        </select>
      </div>
      <div class="form-group">
        <label for="trade-date">{{ t('stocks.trades.tradeDate') }}</label>
        <input id="trade-date" v-model="localForm.trade_date" type="date" required />
      </div>
      <div class="form-group">
        <label for="trade-shares">{{ t('stocks.trades.shares') }}</label>
        <input id="trade-shares" v-model.number="localForm.shares" type="number" min="0.000001" step="0.000001" required />
      </div>
      <div class="form-group">
        <label for="trade-price">{{ t('stocks.trades.price') }}</label>
        <input id="trade-price" v-model.number="localForm.price" type="number" min="0" step="0.0001" required />
      </div>
      <div class="form-group">
        <label for="trade-fee">{{ t('stocks.trades.fee') }}</label>
        <input id="trade-fee" v-model.number="localForm.fee" type="number" min="0" step="0.0001" />
      </div>
      <div class="form-group">
        <label for="trade-tax">{{ t('stocks.trades.tax') }}</label>
        <input id="trade-tax" v-model.number="localForm.tax" type="number" min="0" step="0.0001" />
      </div>
      <div class="form-group">
        <label for="trade-note">{{ t('stocks.trades.note') }}</label>
        <input id="trade-note" v-model.trim="localForm.note" type="text" :placeholder="t('stocks.trades.notePlaceholder')" />
      </div>
      <div class="holding-form-actions">
        <button type="submit" class="btn btn-primary" :disabled="saving">
          {{ saving ? t('stocks.trades.saving') : editingTradeId ? t('stocks.trades.update') : t('stocks.trades.create') }}
        </button>
        <button v-if="editingTradeId" type="button" class="btn btn-secondary" @click="$emit('cancel')">
          {{ t('common.cancel') }}
        </button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  saving: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  editingTradeId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['submit', 'cancel'])
const { t } = useI18n()
const localForm = ref({ ...props.modelValue })

watch(
  () => props.modelValue,
  (value) => {
    localForm.value = { ...value }
  },
  { deep: true }
)

function handleSubmit() {
  emit('submit', { ...localForm.value })
}
</script>

<style scoped>
.trade-form-card,
.trade-form {
  display: grid;
  gap: 16px;
}

.trade-form {
  align-items: end;
}
</style>
