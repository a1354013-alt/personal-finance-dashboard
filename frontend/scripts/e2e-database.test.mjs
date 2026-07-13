import assert from 'node:assert/strict'
import os from 'node:os'
import path from 'node:path'
import test from 'node:test'

import { resolveSafeE2eDatabase } from './e2e-database.mjs'

test('uses the default SQLite database inside backend', () => {
  const backendDir = path.join(os.tmpdir(), 'repo', 'backend')
  const result = resolveSafeE2eDatabase({ backendDir, databaseUrl: undefined })

  assert.equal(result.databaseUrl, 'sqlite:///playwright-e2e.db')
  assert.equal(result.databasePath, path.resolve(backendDir, 'playwright-e2e.db'))
})

test('accepts an explicit safe E2E_DATABASE_URL inside backend', () => {
  const backendDir = path.join(os.tmpdir(), 'repo', 'backend')
  const result = resolveSafeE2eDatabase({ backendDir, databaseUrl: 'sqlite:///./tmp/e2e-safe.db' })

  assert.equal(result.databaseUrl, 'sqlite:///tmp/e2e-safe.db')
  assert.equal(result.databasePath, path.resolve(backendDir, 'tmp', 'e2e-safe.db'))
})

test('rejects normal production-style database URLs', () => {
  assert.throws(
    () => resolveSafeE2eDatabase({ backendDir: path.join(os.tmpdir(), 'repo', 'backend'), databaseUrl: 'postgresql://example/prod' }),
    /sqlite/
  )
})

test('rejects SQLite paths outside backend', () => {
  const backendDir = path.join(os.tmpdir(), 'repo', 'backend')
  assert.throws(
    () => resolveSafeE2eDatabase({ backendDir, databaseUrl: 'sqlite:///../prod.db' }),
    /inside/
  )
})

test('rejects in-memory SQLite URLs', () => {
  assert.throws(
    () => resolveSafeE2eDatabase({ backendDir: path.join(os.tmpdir(), 'repo', 'backend'), databaseUrl: 'sqlite:///:memory:' }),
    /real SQLite file/
  )
})
