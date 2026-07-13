import { spawn, spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { cleanupE2eDatabase, resolveSafeE2eDatabase } from './e2e-database.mjs'

const frontendDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const repoRoot = path.dirname(frontendDir)
const backendDir = path.join(repoRoot, 'backend')
const venvPython = process.platform === 'win32'
  ? path.join(backendDir, '.venv', 'Scripts', 'python.exe')
  : path.join(backendDir, '.venv', 'bin', 'python')
const python = existsSync(venvPython) ? venvPython : 'python'
const e2eDatabase = resolveSafeE2eDatabase({ backendDir })

const env = {
  ...process.env,
  ENV: 'development',
  SECRET_KEY: process.env.SECRET_KEY || 'playwright-e2e-secret-key',
  DATABASE_URL: e2eDatabase.databaseUrl,
  E2E_DATABASE_URL: e2eDatabase.databaseUrl
}

console.log(`Using isolated Playwright database: ${e2eDatabase.databasePath}`)

const cleanupDatabase = () => {
  try {
    cleanupE2eDatabase({ backendDir, databaseUrl: e2eDatabase.databaseUrl })
  } catch {
    // Cleanup is best effort after the safe path has already been validated.
  }
}

cleanupDatabase()

const seed = spawnSync(python, ['seed_data.py', '--reset'], {
  cwd: backendDir,
  env,
  stdio: 'inherit'
})

if (seed.status !== 0) {
  cleanupDatabase()
  process.exit(seed.status ?? 1)
}

const server = spawn(
  python,
  ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8001'],
  {
    cwd: backendDir,
    env,
    stdio: 'inherit'
  }
)

let stopping = false

const stop = () => {
  if (stopping) return
  stopping = true
  if (!server.killed) {
    server.kill()
  }
  cleanupDatabase()
}

process.on('SIGINT', stop)
process.on('SIGTERM', stop)
process.on('exit', cleanupDatabase)
server.on('exit', (code) => {
  cleanupDatabase()
  process.exit(code ?? 0)
})
