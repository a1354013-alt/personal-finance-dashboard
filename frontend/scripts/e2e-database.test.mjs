import assert from 'node:assert/strict'
import { mkdirSync, mkdtempSync, rmSync, symlinkSync } from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import test from 'node:test'

import { resolveSafeE2eDatabase } from './e2e-database.mjs'

test('uses the default SQLite database inside backend', () => {
  const backendDir = path.join(os.tmpdir(), 'repo', 'backend')
  const result = resolveSafeE2eDatabase({ backendDir, databaseUrl: undefined })

  assert.equal(result.databaseUrl, 'sqlite:///.e2e/playwright-e2e.db')
  assert.equal(result.databasePath, path.resolve(backendDir, '.e2e', 'playwright-e2e.db'))
})

test('accepts an explicit safe E2E_DATABASE_URL inside backend/.e2e', () => {
  const backendDir = path.join(os.tmpdir(), 'repo', 'backend')
  const result = resolveSafeE2eDatabase({ backendDir, databaseUrl: 'sqlite:///.e2e/playwright-e2e-local.db' })

  assert.equal(result.databaseUrl, 'sqlite:///.e2e/playwright-e2e-local.db')
  assert.equal(result.databasePath, path.resolve(backendDir, '.e2e', 'playwright-e2e-local.db'))
})

test('rejects normal production-style database URLs', () => {
  assert.throws(
    () => resolveSafeE2eDatabase({ backendDir: path.join(os.tmpdir(), 'repo', 'backend'), databaseUrl: 'postgresql://example/prod' }),
    /sqlite/
  )
})

test('rejects normal application database names', () => {
  const backendDir = path.join(os.tmpdir(), 'repo', 'backend')

  for (const databaseName of ['finance.db', 'test_smoke.db']) {
    assert.throws(
      () => resolveSafeE2eDatabase({ backendDir, databaseUrl: `sqlite:///${databaseName}` }),
      /backend\/\.e2e/
    )
  }

  for (const databaseName of ['finance.db', 'test_smoke.db', 'production.db', 'audit.db', 'custom.db']) {
    assert.throws(
      () => resolveSafeE2eDatabase({ backendDir, databaseUrl: `sqlite:///.e2e/${databaseName}` }),
      /playwright-e2e/
    )
  }
})

test('rejects SQLite paths outside backend', () => {
  const backendDir = path.join(os.tmpdir(), 'repo', 'backend')
  assert.throws(
    () => resolveSafeE2eDatabase({ backendDir, databaseUrl: 'sqlite:///../.e2e/playwright-e2e.db' }),
    /backend\/\.e2e/
  )
})

test('rejects in-memory SQLite URLs', () => {
  assert.throws(
    () => resolveSafeE2eDatabase({ backendDir: path.join(os.tmpdir(), 'repo', 'backend'), databaseUrl: 'sqlite:///:memory:' }),
    /real SQLite file/
  )
})

test('rejects existing symbolic-link database files where supported', (t) => {
  const tempDir = mkdtempSync(path.join(os.tmpdir(), 'pfd-e2e-db-'))
  const backendDir = path.join(tempDir, 'backend')
  const target = path.join(tempDir, 'outside.db')
  const link = path.join(backendDir, '.e2e', 'playwright-e2e-link.db')

  try {
    resolveSafeE2eDatabase({ backendDir })
    symlinkSync(target, link)
  } catch (error) {
    rmSync(tempDir, { recursive: true, force: true })
    t.skip(`Symbolic links are not supported in this environment: ${error.message}`)
    return
  }

  try {
    assert.throws(
      () => resolveSafeE2eDatabase({ backendDir, databaseUrl: 'sqlite:///.e2e/playwright-e2e-link.db' }),
      /symbolic link/
    )
  } finally {
    rmSync(tempDir, { recursive: true, force: true })
  }
})

test('rejects .e2e directory symbolic-link escapes where supported', (t) => {
  const tempDir = mkdtempSync(path.join(os.tmpdir(), 'pfd-e2e-dir-'))
  const backendDir = path.join(tempDir, 'backend')
  const outsideDir = path.join(tempDir, 'outside-e2e')
  const e2eLink = path.join(backendDir, '.e2e')

  try {
    resolveSafeE2eDatabase({ backendDir })
    rmSync(e2eLink, { recursive: true, force: true })
    mkdirSync(outsideDir, { recursive: true })
    symlinkSync(outsideDir, e2eLink, 'dir')
  } catch (error) {
    rmSync(tempDir, { recursive: true, force: true })
    t.skip(`Directory symbolic links are not supported in this environment: ${error.message}`)
    return
  }

  try {
    assert.throws(
      () => resolveSafeE2eDatabase({ backendDir }),
      /real backend\/\.e2e/
    )
  } finally {
    rmSync(tempDir, { recursive: true, force: true })
  }
})
