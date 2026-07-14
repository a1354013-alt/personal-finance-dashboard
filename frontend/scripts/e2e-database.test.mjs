import assert from 'node:assert/strict'
import { existsSync, linkSync, mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import test from 'node:test'

import { resolveSafeE2eDatabase } from './e2e-database.mjs'

function removeTempDir(tempDir) {
  rmSync(tempDir, { recursive: true, force: true })
}

function makeTempBackend(prefix = 'pfd-e2e-db-') {
  const tempDir = mkdtempSync(path.join(os.tmpdir(), prefix))
  const backendDir = path.join(tempDir, 'backend')
  const e2eDir = path.join(backendDir, '.e2e')
  mkdirSync(e2eDir, { recursive: true })
  return { tempDir, backendDir, e2eDir }
}

function skipUnsupportedLink(t, tempDir, linkType, error) {
  removeTempDir(tempDir)
  t.skip(`${linkType} links are not supported in this environment: ${error.message}`)
}

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

test('rejects dangling symbolic-link database files before SQLite can create an external target', (t) => {
  const { tempDir, backendDir, e2eDir } = makeTempBackend()
  const target = path.join(tempDir, 'outside-created.db')
  const link = path.join(e2eDir, 'playwright-e2e-link.db')

  try {
    symlinkSync(target, link)
  } catch (error) {
    skipUnsupportedLink(t, tempDir, 'Symbolic', error)
    return
  }

  try {
    assert.throws(
      () => resolveSafeE2eDatabase({ backendDir, databaseUrl: 'sqlite:///.e2e/playwright-e2e-link.db' }),
      /symbolic link/
    )
    assert.equal(existsSync(target), false)
  } finally {
    removeTempDir(tempDir)
  }
})

test('rejects symbolic-link database files whose external target already exists', (t) => {
  const { tempDir, backendDir, e2eDir } = makeTempBackend()
  const target = path.join(tempDir, 'outside.db')
  const link = path.join(e2eDir, 'playwright-e2e-link.db')
  writeFileSync(target, '')

  try {
    symlinkSync(target, link)
  } catch (error) {
    skipUnsupportedLink(t, tempDir, 'Symbolic', error)
    return
  }

  try {
    assert.throws(
      () => resolveSafeE2eDatabase({ backendDir, databaseUrl: 'sqlite:///.e2e/playwright-e2e-link.db' }),
      /symbolic link/
    )
  } finally {
    removeTempDir(tempDir)
  }
})

test('rejects symbolic-link database files pointing to another file inside backend/.e2e', (t) => {
  const { tempDir, backendDir, e2eDir } = makeTempBackend()
  const target = path.join(e2eDir, 'playwright-e2e-target.db')
  const link = path.join(e2eDir, 'playwright-e2e-link.db')
  writeFileSync(target, '')

  try {
    symlinkSync(target, link)
  } catch (error) {
    skipUnsupportedLink(t, tempDir, 'Symbolic', error)
    return
  }

  try {
    assert.throws(
      () => resolveSafeE2eDatabase({ backendDir, databaseUrl: 'sqlite:///.e2e/playwright-e2e-link.db' }),
      /symbolic link/
    )
  } finally {
    removeTempDir(tempDir)
  }
})

test('accepts a safe E2E database filename that does not exist yet', () => {
  const { tempDir, backendDir, e2eDir } = makeTempBackend()

  try {
    const result = resolveSafeE2eDatabase({ backendDir, databaseUrl: 'sqlite:///.e2e/playwright-e2e-new.db' })

    assert.equal(result.databaseUrl, 'sqlite:///.e2e/playwright-e2e-new.db')
    assert.equal(result.databasePath, path.join(e2eDir, 'playwright-e2e-new.db'))
    assert.equal(existsSync(result.databasePath), false)
  } finally {
    removeTempDir(tempDir)
  }
})

test('accepts an existing regular E2E database file inside backend/.e2e', () => {
  const { tempDir, backendDir, e2eDir } = makeTempBackend()
  const databasePath = path.join(e2eDir, 'playwright-e2e-existing.db')
  writeFileSync(databasePath, '')

  try {
    const result = resolveSafeE2eDatabase({ backendDir, databaseUrl: 'sqlite:///.e2e/playwright-e2e-existing.db' })

    assert.equal(result.databaseUrl, 'sqlite:///.e2e/playwright-e2e-existing.db')
    assert.equal(result.databasePath, databasePath)
  } finally {
    removeTempDir(tempDir)
  }
})

test('rejects non-regular E2E database filesystem entries', () => {
  const { tempDir, backendDir, e2eDir } = makeTempBackend()
  mkdirSync(path.join(e2eDir, 'playwright-e2e-directory.db'))

  try {
    assert.throws(
      () => resolveSafeE2eDatabase({ backendDir, databaseUrl: 'sqlite:///.e2e/playwright-e2e-directory.db' }),
      /regular SQLite file/
    )
  } finally {
    removeTempDir(tempDir)
  }
})

test('rejects .e2e directory symbolic-link escapes where supported', (t) => {
  const tempDir = mkdtempSync(path.join(os.tmpdir(), 'pfd-e2e-dir-'))
  const backendDir = path.join(tempDir, 'backend')
  const outsideDir = path.join(tempDir, 'outside-e2e')
  const e2eLink = path.join(backendDir, '.e2e')
  mkdirSync(backendDir, { recursive: true })
  mkdirSync(outsideDir, { recursive: true })

  try {
    symlinkSync(outsideDir, e2eLink, 'dir')
  } catch (error) {
    skipUnsupportedLink(t, tempDir, 'Directory symbolic', error)
    return
  }

  try {
    assert.throws(
      () => resolveSafeE2eDatabase({ backendDir }),
      /real backend\/\.e2e/
    )
  } finally {
    removeTempDir(tempDir)
  }
})

test('rejects dangling .e2e directory symbolic links where supported', (t) => {
  const tempDir = mkdtempSync(path.join(os.tmpdir(), 'pfd-e2e-dir-'))
  const backendDir = path.join(tempDir, 'backend')
  const missingTarget = path.join(tempDir, 'missing-e2e')
  const e2eLink = path.join(backendDir, '.e2e')
  mkdirSync(backendDir, { recursive: true })

  try {
    symlinkSync(missingTarget, e2eLink, 'dir')
  } catch (error) {
    skipUnsupportedLink(t, tempDir, 'Directory symbolic', error)
    return
  }

  try {
    assert.throws(
      () => resolveSafeE2eDatabase({ backendDir }),
      /real backend\/\.e2e/
    )
    assert.equal(existsSync(missingTarget), false)
  } finally {
    removeTempDir(tempDir)
  }
})

test('rejects existing E2E database files with multiple hard links where supported', (t) => {
  const { tempDir, backendDir, e2eDir } = makeTempBackend()
  const target = path.join(tempDir, 'outside-hardlink.db')
  const hardLink = path.join(e2eDir, 'playwright-e2e-hardlink.db')
  writeFileSync(target, '')

  try {
    linkSync(target, hardLink)
  } catch (error) {
    skipUnsupportedLink(t, tempDir, 'Hard', error)
    return
  }

  try {
    assert.throws(
      () => resolveSafeE2eDatabase({ backendDir, databaseUrl: 'sqlite:///.e2e/playwright-e2e-hardlink.db' }),
      /multiple hard links/
    )
  } finally {
    removeTempDir(tempDir)
  }
})
