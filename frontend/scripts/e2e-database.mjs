import { existsSync, lstatSync, mkdirSync, realpathSync, rmSync } from 'node:fs'
import path from 'node:path'

export const DEFAULT_E2E_DATABASE_URL = 'sqlite:///.e2e/playwright-e2e.db'
const E2E_DATABASE_DIR = '.e2e'
const E2E_DATABASE_FILENAME_PATTERN = /^playwright-e2e.*\.db$/

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

function lstatIfPresent(filePath) {
  try {
    return lstatSync(filePath)
  } catch (error) {
    if (error?.code === 'ENOENT') {
      return null
    }
    throw error
  }
}

function assertSafeDirectory(directoryPath) {
  let stats = lstatIfPresent(directoryPath)
  if (!stats) {
    mkdirSync(directoryPath, { recursive: true })
    stats = lstatSync(directoryPath)
  }

  if (stats.isSymbolicLink() || !stats.isDirectory()) {
    throw new Error('E2E database directory must be a real backend/.e2e directory.')
  }
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
  const e2eDir = path.join(resolvedBackendDir, E2E_DATABASE_DIR)

  assertSafeDirectory(e2eDir)

  const relative = path.relative(e2eDir, candidatePath)

  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw new Error('E2E database must resolve inside the dedicated backend/.e2e directory.')
  }
  if (path.dirname(relative) !== '.') {
    throw new Error('E2E database files must be direct children of backend/.e2e.')
  }
  if (!E2E_DATABASE_FILENAME_PATTERN.test(path.basename(candidatePath))) {
    throw new Error('E2E database filename must match playwright-e2e*.db.')
  }

  const candidateStats = lstatIfPresent(candidatePath)
  if (candidateStats?.isSymbolicLink()) {
    throw new Error('E2E database file must not be a symbolic link.')
  }
  if (candidateStats && !candidateStats.isFile()) {
    throw new Error('E2E database path must be a regular SQLite file.')
  }
  if (candidateStats?.nlink > 1) {
    throw new Error('E2E database file must not have multiple hard links.')
  }

  const realE2eDir = realpathSync(e2eDir)
  const parentDir = path.dirname(candidatePath)
  if (existsSync(parentDir)) {
    const realParentDir = realpathSync(parentDir)
    if (realParentDir !== realE2eDir) {
      throw new Error('E2E database parent directory must not resolve outside backend/.e2e.')
    }
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
