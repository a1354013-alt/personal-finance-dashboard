import { spawn } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { terminateProcessTree } from './e2e-process.mjs'

const frontendDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const viteBin = path.join(frontendDir, 'node_modules', 'vite', 'bin', 'vite.js')

const server = spawn(process.execPath, [viteBin, '--host', '127.0.0.1', '--port', '5174'], {
  env: {
    ...process.env,
    VITE_API_PROXY_TARGET: 'http://127.0.0.1:8001'
  },
  stdio: 'inherit',
  shell: false
})

let stopping = false

const stop = () => {
  if (stopping) return
  stopping = true
  terminateProcessTree(server)
}

process.on('SIGINT', stop)
process.on('SIGTERM', stop)
server.on('exit', (code) => process.exit(code ?? 0))
