import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import { createI18nInstance } from '@/i18n'
import TransactionImport from '@/pages/TransactionImport.vue'

const previewTransactionImportMock = vi.fn()
const confirmTransactionImportMock = vi.fn()
const listTransactionImportsMock = vi.fn()
const getTransactionImportMock = vi.fn()

vi.mock('@/api/imports', () => ({
  previewTransactionImport: (...args) => previewTransactionImportMock(...args),
  confirmTransactionImport: (...args) => confirmTransactionImportMock(...args),
  listTransactionImports: (...args) => listTransactionImportsMock(...args),
  getTransactionImport: (...args) => getTransactionImportMock(...args)
}))

const previewPayload = {
  batch: {
    id: 'batch-1',
    file_name: 'transactions.csv',
    file_type: 'csv',
    status: 'previewed',
    created_at: '2026-07-08T00:00:00Z',
    summary: {
      total_rows: 3,
      valid_rows: 1,
      invalid_rows: 1,
      duplicate_rows: 1,
      rows_to_import: 1
    }
  },
  requires_mapping: false,
  rows: [
    {
      id: 1,
      source_row_number: 2,
      status: 'valid',
      validation_errors: [],
      warnings: [],
      duplicate_reasons: [],
      normalized: {
        transaction_date: '2026-07-01',
        amount: 120,
        type: 'expense',
        category: 'Food',
        description: 'Lunch'
      }
    },
    {
      id: 2,
      source_row_number: 3,
      status: 'invalid',
      validation_errors: ['Invalid amount.'],
      warnings: [],
      duplicate_reasons: [],
      normalized: {
        transaction_date: '2026-07-02',
        amount: null,
        type: 'expense',
        category: 'Food',
        description: 'Bad row'
      }
    },
    {
      id: 3,
      source_row_number: 4,
      status: 'duplicate',
      validation_errors: [],
      warnings: [],
      duplicate_reasons: ['duplicate_in_database'],
      normalized: {
        transaction_date: '2026-07-03',
        amount: 88,
        type: 'expense',
        category: 'Transport',
        description: 'Taxi'
      }
    }
  ]
}

const mappingRequiredPayload = {
  batch: {
    id: 'batch-map',
    file_name: 'transactions.csv',
    file_type: 'csv',
    status: 'mapping_required',
    created_at: '2026-07-08T00:00:00Z',
    summary: {
      total_rows: 0,
      valid_rows: 0,
      invalid_rows: 0,
      duplicate_rows: 0,
      rows_to_import: 0
    }
  },
  requires_mapping: true,
  available_columns: ['Txn Date', 'Money', 'Memo'],
  suggested_mapping: { note: 'Memo' },
  applied_mapping: { note: 'Memo' },
  missing_required_fields: ['date', 'amount'],
  rows: []
}

describe('Transaction import page', () => {
  beforeEach(() => {
    const pinia = createPinia()
    setActivePinia(pinia)
    previewTransactionImportMock.mockReset()
    confirmTransactionImportMock.mockReset()
    listTransactionImportsMock.mockReset()
    getTransactionImportMock.mockReset()
    listTransactionImportsMock.mockResolvedValue([])
    previewTransactionImportMock.mockResolvedValue(previewPayload)
    getTransactionImportMock.mockResolvedValue(previewPayload)
    confirmTransactionImportMock.mockResolvedValue({
      batch_id: 'batch-1',
      created_count: 1,
      skipped_count: 2,
      duplicate_count: 1,
      error_count: 1,
      created_transaction_ids: [42]
    })
  })

  function mountPage() {
    const pinia = createPinia()
    const i18n = createI18nInstance()
    i18n.global.locale.value = 'en'
    setActivePinia(pinia)
    return mount(TransactionImport, { global: { plugins: [pinia, i18n] } })
  }

  async function attachFile(wrapper, file) {
    const input = wrapper.find('#transaction-import-file')
    Object.defineProperty(input.element, 'files', {
      value: [file],
      configurable: true
    })
    await input.trigger('change')
  }

  it('renders upload control', async () => {
    const wrapper = mountPage()
    expect(wrapper.find('#transaction-import-file').exists()).toBe(true)
    await vi.waitFor(() => {
      expect(listTransactionImportsMock).toHaveBeenCalled()
    })
  })

  it('displays preview rows, invalid rows, duplicate rows, and summary counts', async () => {
    const wrapper = mountPage()
    const file = new File(['csv'], 'transactions.csv', { type: 'text/csv' })
    await attachFile(wrapper, file)
    await wrapper.find('button.btn.btn-primary').trigger('click')

    await vi.waitFor(() => {
      expect(previewTransactionImportMock).toHaveBeenCalled()
      expect(wrapper.text()).toContain('Lunch')
      expect(wrapper.text()).toContain('Invalid amount.')
      expect(wrapper.text()).toContain('duplicate_in_database')
      expect(wrapper.text()).toContain('3')
      expect(wrapper.text()).toContain('1')
    })
  })

  it('shows the mapping UI when required fields are missing and can re-preview with mapping', async () => {
    previewTransactionImportMock
      .mockResolvedValueOnce(mappingRequiredPayload)
      .mockResolvedValueOnce(previewPayload)

    const wrapper = mountPage()
    const file = new File(['csv'], 'transactions.csv', { type: 'text/csv' })
    await attachFile(wrapper, file)
    await wrapper.find('button.btn.btn-primary').trigger('click')

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Map Columns')
      expect(wrapper.text()).toContain('date, amount')
    })

    await wrapper.find('#mapping-date').setValue('Txn Date')
    await wrapper.find('#mapping-amount').setValue('Money')
    await wrapper.findAll('button.btn.btn-primary')[1].trigger('click')

    await vi.waitFor(() => {
      expect(previewTransactionImportMock).toHaveBeenLastCalledWith(
        expect.any(File),
        expect.objectContaining({ date: 'Txn Date', amount: 'Money', note: 'Memo' })
      )
      expect(wrapper.text()).toContain('Lunch')
    })
  })

  it('calls confirm import and renders result', async () => {
    const wrapper = mountPage()
    const file = new File(['csv'], 'transactions.csv', { type: 'text/csv' })
    await attachFile(wrapper, file)
    await wrapper.find('button.btn.btn-primary').trigger('click')

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('Lunch')
    })

    await wrapper.find('button.btn.btn-success').trigger('click')

    await vi.waitFor(() => {
      expect(confirmTransactionImportMock).toHaveBeenCalledWith('batch-1', [2])
      expect(wrapper.text()).toContain('Created 1 rows')
    })
  })

  it('disables row checkboxes for invalid and duplicate rows', async () => {
    const wrapper = mountPage()
    const file = new File(['csv'], 'transactions.csv', { type: 'text/csv' })
    await attachFile(wrapper, file)
    await wrapper.find('button.btn.btn-primary').trigger('click')

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('duplicate_in_database')
    })

    const rowCheckboxes = wrapper.findAll('tbody input[type="checkbox"]')
    expect(rowCheckboxes).toHaveLength(3)
    expect(rowCheckboxes[0].element.disabled).toBe(false)
    expect(rowCheckboxes[1].element.disabled).toBe(true)
    expect(rowCheckboxes[2].element.disabled).toBe(true)
  })
})
