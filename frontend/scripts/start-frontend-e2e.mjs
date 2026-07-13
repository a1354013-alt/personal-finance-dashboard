import { spawn } from 'node:child_process'

const npmCommand = process.platform === 'win32' ? 'npm.cmd' : 'npm'

const server = spawn(npmCommand, ['run', 'dev', '--', '--host', '127.0.0.1', '--port', '5174'], {
  env: {
    ...process.env,
    VITE_API_PROXY_TARGET: 'http://127.0.0.1:8001'
  },
  stdio: 'inherit',
  shell: process.platform === 'win32'
})

const stop = () => {
  if (!server.killed) {
    server.kill()
  }
}

process.on('SIGINT', stop)
process.on('SIGTERM', stop)
server.on('exit', (code) => process.exit(code ?? 0))
