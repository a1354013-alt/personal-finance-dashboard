import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { cleanupE2eDatabase } from './e2e-database.mjs'
import { assertPortsReleased } from './e2e-process.mjs'

const frontendDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const backendDir = path.join(path.dirname(frontendDir), 'backend')
const playwrightCommand = process.platform === 'win32' ? 'playwright.cmd' : 'playwright'

const result = spawnSync(playwrightCommand, ['test', ...process.argv.slice(2)], {
  cwd: frontendDir,
  stdio: 'inherit',
  shell: process.platform === 'win32'
})

let cleanupFailed = false

try {
  cleanupE2eDatabase({ backendDir })
} catch (error) {
  console.error(error)
  cleanupFailed = true
}

try {
  await assertPortsReleased([8001, 5174])
} catch (error) {
  console.error(error)
  cleanupFailed = true
}

process.exit(cleanupFailed ? 1 : result.status ?? 1)
