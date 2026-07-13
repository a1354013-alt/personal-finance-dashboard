import { spawnSync } from 'node:child_process'
import net from 'node:net'

const PORT_CHECK_TIMEOUT_MS = 500
const PORT_RELEASE_ATTEMPTS = 20
const PORT_RELEASE_RETRY_MS = 250

export function terminateProcessTree(childProcess) {
  if (!childProcess || childProcess.exitCode !== null) {
    return
  }

  if (process.platform === 'win32' && childProcess.pid) {
    spawnSync('taskkill.exe', ['/PID', String(childProcess.pid), '/T', '/F'], {
      stdio: 'ignore'
    })
    return
  }

  if (!childProcess.killed) {
    childProcess.kill('SIGTERM')
  }
}

function isPortOpen(port, host) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ port, host })
    const finish = (open) => {
      socket.removeAllListeners()
      socket.destroy()
      resolve(open)
    }

    socket.setTimeout(PORT_CHECK_TIMEOUT_MS)
    socket.once('connect', () => finish(true))
    socket.once('timeout', () => finish(false))
    socket.once('error', () => finish(false))
  })
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function assertPortsReleased(ports, host = '127.0.0.1') {
  let occupiedPorts = []

  for (let attempt = 0; attempt < PORT_RELEASE_ATTEMPTS; attempt += 1) {
    occupiedPorts = []
    for (const port of ports) {
      if (await isPortOpen(port, host)) {
        occupiedPorts.push(port)
      }
    }

    if (occupiedPorts.length === 0) {
      return
    }

    if (attempt < PORT_RELEASE_ATTEMPTS - 1) {
      await delay(PORT_RELEASE_RETRY_MS)
    }
  }

  throw new Error(`E2E cleanup left port(s) occupied: ${occupiedPorts.join(', ')}.`)
}
