import { existsSync, rmSync } from 'node:fs'
import path from 'node:path'

export const DEFAULT_E2E_DATABASE_URL = 'sqlite:///./playwright-e2e.db'

function sqlitePathFromUrl(databaseUrl) {
  if (!databaseUrl.startsWith('sqlite:///')) {
    throw new Error('E2E_DATABASE_URL must use a sqlite:/// URL.')
  }
  const rawPath = databaseUrl.slice('sqlite:///'.length)
  if (!rawPath || rawPath === ':memory:') {
    throw new Error('E2E_DATABASE_URL must point to a real SQLite file.')
  }
  return rawPath
}

export function resolveSafeE2eDatabase({ backendDir, databaseUrl = process.env.E2E_DATABASE_URL } = {}) {
  if (!backendDir) {
    throw new Error('backendDir is required for E2E database validation.')
  }

  const selectedUrl = databaseUrl || DEFAULT_E2E_DATABASE_URL
  const sqlitePath = sqlitePathFromUrl(selectedUrl)
  const normalizedPath = sqlitePath.replace(/\\/g, '/')
  const candidatePath = path.isAbsolute(normalizedPath) || /^[A-Za-z]:\//.test(normalizedPath)
    ? path.resolve(normalizedPath)
    : path.resolve(backendDir, normalizedPath)
  const resolvedBackendDir = path.resolve(backendDir)
  const relative = path.relative(resolvedBackendDir, candidatePath)

  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw new Error('E2E database must resolve inside the repository backend directory.')
  }
  if (!candidatePath.endsWith('.db')) {
    throw new Error('E2E database file must use a .db extension.')
  }

  return {
    databaseUrl: `sqlite:///${path.relative(resolvedBackendDir, candidatePath).replace(/\\/g, '/')}`,
    databasePath: candidatePath
  }
}

export function cleanupE2eDatabase({ backendDir, databaseUrl = process.env.E2E_DATABASE_URL } = {}) {
  const { databasePath } = resolveSafeE2eDatabase({ backendDir, databaseUrl })
  const paths = [
    databasePath,
    `${databasePath}-journal`,
    `${databasePath}-wal`,
    `${databasePath}-shm`
  ]

  let lastError
  for (let attempt = 0; attempt < 20; attempt += 1) {
    try {
      for (const filePath of paths) {
        rmSync(filePath, { force: true })
      }
      if (paths.every((filePath) => !existsSync(filePath))) {
        return
      }
    } catch (error) {
      lastError = error
    }
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 250)
  }

  if (lastError) {
    throw lastError
  }
  throw new Error(`Unable to remove E2E database files for ${databasePath}.`)
}
