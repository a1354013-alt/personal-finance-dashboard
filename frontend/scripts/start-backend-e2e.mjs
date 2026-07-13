import { spawn, spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const repoRoot = path.dirname(frontendDir)
const backendDir = path.join(repoRoot, 'backend')
const venvPython = process.platform === 'win32'
  ? path.join(backendDir, '.venv', 'Scripts', 'python.exe')
  : path.join(backendDir, '.venv', 'bin', 'python')
const python = existsSync(venvPython) ? venvPython : 'python'

const env = {
  ...process.env,
  ENV: 'development',
  SECRET_KEY: process.env.SECRET_KEY || 'playwright-e2e-secret-key',
  DATABASE_URL: process.env.DATABASE_URL || 'sqlite:///./finance_app.db'
}

const seed = spawnSync(python, ['seed_data.py', '--reset'], {
  cwd: backendDir,
  env,
  stdio: 'inherit'
})

if (seed.status !== 0) {
  process.exit(seed.status ?? 1)
}

const server = spawn(
  python,
  ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000'],
  {
    cwd: backendDir,
    env,
    stdio: 'inherit'
  }
)

const stop = () => {
  if (!server.killed) {
    server.kill()
  }
}

process.on('SIGINT', stop)
process.on('SIGTERM', stop)
server.on('exit', (code) => process.exit(code ?? 0))
