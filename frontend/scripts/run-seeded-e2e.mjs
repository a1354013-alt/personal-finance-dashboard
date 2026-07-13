import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { cleanupE2eDatabase } from './e2e-database.mjs'

const frontendDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const backendDir = path.join(path.dirname(frontendDir), 'backend')
const playwrightCommand = process.platform === 'win32' ? 'playwright.cmd' : 'playwright'

const result = spawnSync(playwrightCommand, ['test'], {
  cwd: frontendDir,
  stdio: 'inherit',
  shell: process.platform === 'win32'
})

try {
  cleanupE2eDatabase({ backendDir })
} catch (error) {
  console.error(error)
  process.exit(1)
}

process.exit(result.status ?? 1)
