import { test, expect, type Page } from '@playwright/test'

async function createRoom(page: Page, name: string, rules = 'ukrainian') {
  await page.goto('/')
  await page.fill("input[placeholder=\"Введіть ім'я\"]", name)
  await page.selectOption('select', { value: rules })
  await page.click('button:has-text("Створити кімнату")')
  await page.waitForURL(/\/game\//)
  return page.url().split('/game/')[1]
}

async function joinRoom(page: Page, name: string, roomId: string) {
  await page.goto('/')
  await page.fill("input[placeholder=\"Введіть ім'я\"]", name)
  const joinBtn = page.locator(`.room-card:has-text("${roomId}") button, button:has-text("Приєднатись")`).first()
  // join via API directly for reliability
  const res = await page.request.post(`/api/lobby/rooms/${roomId}/join`, {
    data: { player_name: name },
  })
  const { session_id, game_id } = await res.json()
  // Navigate with session context set by injecting into the page store
  await page.goto('/')
  await page.evaluate(
    ({ sid, pid, gid }) => {
      const store = (window as any).__pinia?.state?.value
      if (store?.session) {
        store.session.sessionId = sid
        store.session.playerId = pid
        store.session.playerColor = 'black'
      }
    },
    { sid: session_id, pid: 'p2', gid: game_id },
  )
  await page.goto(`/game/${game_id}`)
  return game_id
}

test.describe('Game flow', () => {
  test('board renders after both players join', async ({ browser }) => {
    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const alice = await ctx1.newPage()
    const bob = await ctx2.newPage()

    const roomId = await createRoom(alice, 'Alice')

    // Bob joins via the lobby
    await bob.goto('/')
    await bob.fill("input[placeholder=\"Введіть ім'я\"]", 'Bob')
    await bob.click('button:has-text("↻ Оновити")')
    await bob.waitForSelector('button:has-text("Приєднатись")')
    await bob.click('button:has-text("Приєднатись")')
    await bob.waitForURL(/\/game\//)

    // Alice's board should now be visible
    await expect(alice.locator('.board')).toBeVisible({ timeout: 10_000 })
    await expect(bob.locator('.board')).toBeVisible({ timeout: 10_000 })

    await ctx1.close()
    await ctx2.close()
  })

  test('white player can make a move', async ({ browser }) => {
    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const alice = await ctx1.newPage()
    const bob = await ctx2.newPage()

    await createRoom(alice, 'Alice')

    await bob.goto('/')
    await bob.fill("input[placeholder=\"Введіть ім'я\"]", 'Bob')
    await bob.click('button:has-text("↻ Оновити")')
    await bob.waitForSelector('button:has-text("Приєднатись")')
    await bob.click('button:has-text("Приєднатись")')
    await bob.waitForURL(/\/game\//)

    await alice.waitForSelector('.board')

    // Click a white piece (row 5, which is one of the starting rows for white)
    // Dark cells have class 'dark' and are clickable
    const darkCells = alice.locator('.cell.dark')
    const cellCount = await darkCells.count()
    expect(cellCount).toBeGreaterThan(0)

    // Alice clicks a piece that has valid moves — first dark cell in row 5
    // We look for a cell with a white piece
    const whitePiece = alice.locator('.piece.white').first()
    await whitePiece.click()

    // Some cells should now be highlighted as targets
    const targets = alice.locator('.cell.move-target, .cell.capture-target')
    await expect(targets.first()).toBeVisible({ timeout: 3_000 })

    await ctx1.close()
    await ctx2.close()
  })

  test('resign ends the game', async ({ browser }) => {
    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const alice = await ctx1.newPage()
    const bob = await ctx2.newPage()

    await createRoom(alice, 'Alice')
    await bob.goto('/')
    await bob.fill("input[placeholder=\"Введіть ім'я\"]", 'Bob')
    await bob.click('button:has-text("↻ Оновити")')
    await bob.waitForSelector('button:has-text("Приєднатись")')
    await bob.click('button:has-text("Приєднатись")')
    await bob.waitForURL(/\/game\//)
    await alice.waitForSelector('.board')

    // Alice resigns (mock confirm dialog)
    alice.on('dialog', (dialog) => dialog.accept())
    await alice.click('button:has-text("Здатись")')

    await expect(alice.locator('.result-banner')).toBeVisible({ timeout: 5_000 })
    await expect(alice.locator('.result-banner.loss')).toBeVisible()
    await expect(bob.locator('.result-banner.win')).toBeVisible({ timeout: 5_000 })

    await ctx1.close()
    await ctx2.close()
  })

  test('draw by agreement', async ({ browser }) => {
    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const alice = await ctx1.newPage()
    const bob = await ctx2.newPage()

    await createRoom(alice, 'Alice')
    await bob.goto('/')
    await bob.fill("input[placeholder=\"Введіть ім'я\"]", 'Bob')
    await bob.click('button:has-text("↻ Оновити")')
    await bob.waitForSelector('button:has-text("Приєднатись")')
    await bob.click('button:has-text("Приєднатись")')
    await bob.waitForURL(/\/game\//)
    await alice.waitForSelector('.board')

    await alice.click('button:has-text("Запропонувати нічию")')
    await expect(bob.locator('.draw-offer')).toBeVisible({ timeout: 5_000 })
    await bob.click('button:has-text("Прийняти")')

    await expect(alice.locator('.result-banner.draw')).toBeVisible({ timeout: 5_000 })
    await expect(bob.locator('.result-banner.draw')).toBeVisible()

    await ctx1.close()
    await ctx2.close()
  })
})
