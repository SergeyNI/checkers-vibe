import { test, expect } from '@playwright/test'

test.describe('Lobby', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('shows page title', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('Шашки онлайн')
  })

  test('shows create room form', async ({ page }) => {
    await expect(page.getByText('Нова гра')).toBeVisible()
    await expect(page.getByPlaceholder("Введіть ім'я")).toBeVisible()
    await expect(page.getByLabel('Правила')).toBeVisible()
    await expect(page.getByLabel('Таймер')).toBeVisible()
  })

  test('shows room list section with refresh button', async ({ page }) => {
    await expect(page.getByText('Відкриті кімнати')).toBeVisible()
    await expect(page.getByText('↻ Оновити')).toBeVisible()
  })

  test('create button is disabled without player name', async ({ page }) => {
    const btn = page.getByRole('button', { name: 'Створити кімнату' })
    await expect(btn).toBeDisabled()
  })

  test('create room navigates to game page', async ({ page }) => {
    await page.fill("input[placeholder=\"Введіть ім'я\"]", 'Alice')
    await page.click('button:has-text("Створити кімнату")')
    await expect(page).toHaveURL(/\/game\//)
  })

  test('join requires name before joining', async ({ page }) => {
    // Seed a room via API
    await page.request.post('/api/lobby/rooms', {
      data: {
        player_name: 'Seed',
        rules: 'ukrainian',
        timer_type: 'game_clock',
        timer_duration: 600,
      },
    })
    await page.reload()
    // Try to join without a name — should show error
    const joinBtn = page.locator('button:has-text("Приєднатись")').first()
    await joinBtn.click()
    await expect(page.getByText(/ім'я/i)).toBeVisible()
  })

  test('all three rule options are available', async ({ page }) => {
    const select = page.getByLabel('Правила')
    await expect(select.locator('option[value="ukrainian"]')).toHaveCount(1)
    await expect(select.locator('option[value="brazilian"]')).toHaveCount(1)
    await expect(select.locator('option[value="international"]')).toHaveCount(1)
  })
})
