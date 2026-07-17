import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  expect: {
    timeout: 10_000
  },
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
  use: {
    baseURL: 'http://127.0.0.1:5174',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  webServer: [
    {
      command: 'node scripts/start-backend-e2e.mjs',
      url: 'http://127.0.0.1:8001/health',
      reuseExistingServer: false,
      timeout: 120_000
    },
    {
      command: 'node scripts/start-frontend-e2e.mjs',
      url: 'http://127.0.0.1:5174',
      reuseExistingServer: false,
      timeout: 120_000
    }
  ],
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    }
  ],
  outputDir: 'test-results'
})
