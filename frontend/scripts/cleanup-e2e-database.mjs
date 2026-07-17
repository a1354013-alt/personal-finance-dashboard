import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { cleanupE2eDatabase } from './e2e-database.mjs'

const frontendDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const backendDir = path.join(path.dirname(frontendDir), 'backend')

cleanupE2eDatabase({ backendDir })
