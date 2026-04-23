import { test, expect } from '@playwright/test'

test.describe('Reconnect overlay', () => {
  test('shows overlay when WebSocket is offline', async ({ page }) => {
    // Intercept WebSocket upgrade so connection never succeeds
    await page.routeWebSocket(/\/ws\//, (ws) => {
      ws.onopen = () => {
        // Immediately close to simulate disconnect
        ws.close()
      }
    })

    await page.goto('/')
    await page.fill("input[placeholder=\"Введіть ім'я\"]", 'Alice')
    await page.click('button:has-text("Створити кімнату")')
    await page.waitForURL(/\/game\//)

    // Overlay should appear because WS closed
    await expect(page.locator('.overlay')).toBeVisible({ timeout: 8_000 })
    await expect(page.getByText(/з'єднання/i)).toBeVisible()
  })

  test('overlay disappears when connection is restored', async ({ page }) => {
    let closeHandler: (() => void) | null = null

    await page.routeWebSocket(/\/ws\//, (ws) => {
      ws.onopen = () => {
        // Store close function to call later
        closeHandler = () => ws.close()
        // Let messages through
        ws.onmessage = (msg) => ws.send(msg)
      }
    })

    await page.goto('/')
    await page.fill("input[placeholder=\"Введіть ім'я\"]", 'Alice')
    await page.click('button:has-text("Створити кімнату")')
    await page.waitForURL(/\/game\//)

    // Wait initial load (no overlay yet if WS connected)
    await page.waitForTimeout(500)

    // Simulate disconnect
    if (closeHandler) closeHandler()
    await expect(page.locator('.overlay')).toBeVisible({ timeout: 5_000 })

    // Reconnect happens automatically — remove the intercept
    await page.unrouteWebSocket(/\/ws\//)
    await expect(page.locator('.overlay')).not.toBeVisible({ timeout: 20_000 })
  })

  test('paused banner shows when opponent disconnects', async ({ browser }) => {
    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const alice = await ctx1.newPage()
    const bob = await ctx2.newPage()

    await alice.goto('/')
    await alice.fill("input[placeholder=\"Введіть ім'я\"]", 'Alice')
    await alice.click('button:has-text("Створити кімнату")')
    await alice.waitForURL(/\/game\//)

    await bob.goto('/')
    await bob.fill("input[placeholder=\"Введіть ім'я\"]", 'Bob')
    await bob.click('button:has-text("↻ Оновити")')
    await bob.waitForSelector('button:has-text("Приєднатись")')
    await bob.click('button:has-text("Приєднатись")')
    await bob.waitForURL(/\/game\//)
    await alice.waitForSelector('.board')

    // Bob closes tab
    await ctx2.close()

    // Alice should see the paused banner
    await expect(alice.locator('.paused-banner')).toBeVisible({ timeout: 10_000 })

    await ctx1.close()
  })
})
