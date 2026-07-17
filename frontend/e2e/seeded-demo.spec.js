import { expect, test } from '@playwright/test'

test('seeded demo stocks workflow', async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem('locale', 'en')
  })
  await page.goto('/stocks')
  await expect(page).toHaveURL(/\/login\?redirect=\/stocks/)

  await page.locator('#login-email').fill('demo@example.com')
  await page.locator('#login-password').fill('demo1234')
  await page.getByRole('button', { name: /sign in/i }).click()

  await expect(page).toHaveURL(/\/stocks/)
  await expect(page.getByRole('heading', { name: 'Portfolio Holdings' })).toBeVisible()
  await expect(page.locator('.portfolio-currency-section').filter({ hasText: 'TWD' })).toContainText('NT$')
  await expect(page.locator('.portfolio-currency-section').filter({ hasText: 'USD' })).toContainText('US$')

  await page.locator('#holding-stock-code').fill('MSFT')
  await page.locator('#holding-shares').fill('1')
  await page.locator('#holding-average-cost').fill('300')
  await page.locator('#holding-note').fill('E2E missing price')
  await page.getByRole('button', { name: 'Add Holding' }).click()
  await expect(page.getByText('Holding saved.')).toBeVisible()
  await expect(page.getByText('Latest price unavailable for MSFT.')).toBeVisible()
  await expect(page.getByText('Partial prices')).toBeVisible()
  await expect(page.getByText('Priced Market Value')).toBeVisible()
  await expect(page.getByText('Unpriced Cost')).toBeVisible()

  const msftCard = page.locator('.portfolio-position-card').filter({ hasText: 'MSFT' })
  await msftCard.getByRole('button', { name: 'Edit' }).click()
  await page.locator('#holding-shares').fill('2')
  await page.getByRole('button', { name: 'Update Holding' }).click()
  await expect(page.getByText('Holding updated.')).toBeVisible()
  await expect(msftCard).toContainText('2')

  await msftCard.getByRole('button', { name: 'Delete' }).click()
  await expect(page.getByText('Holding deleted.')).toBeVisible()
  await expect(page.locator('.portfolio-position-card').filter({ hasText: 'MSFT' })).toHaveCount(0)

  await page.getByRole('button', { name: 'Sign Out' }).click()
  await expect(page).toHaveURL(/\/login/)
  await page.goto('/stocks')
  await expect(page).toHaveURL(/\/login\?redirect=\/stocks/)
})
