import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useLobbyStore } from '../useLobbyStore'
import { useSessionStore } from '../useSessionStore'

function mockFetch(data: unknown, ok = true) {
  return vi.spyOn(global, 'fetch').mockResolvedValueOnce({
    ok,
    json: async () => data,
    text: async () => String(data),
  } as Response)
}

describe('useLobbyStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.resetAllMocks()
  })

  afterEach(() => vi.restoreAllMocks())

  // --- fetchRooms ---

  it('fetchRooms populates rooms on success', async () => {
    const rooms = [
      { room_id: 'r1', creator_name: 'Alice', rules: 'ukrainian', timer_type: 'game_clock', timer_duration: 600 },
    ]
    mockFetch(rooms)
    const store = useLobbyStore()
    await store.fetchRooms()
    expect(store.rooms).toEqual(rooms)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchRooms sets error on network failure', async () => {
    vi.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('network'))
    const store = useLobbyStore()
    await store.fetchRooms()
    expect(store.rooms).toEqual([])
    expect(store.error).toBeTruthy()
    expect(store.loading).toBe(false)
  })

  it('fetchRooms sets loading during request', async () => {
    let resolve!: (v: Response) => void
    vi.spyOn(global, 'fetch').mockReturnValueOnce(
      new Promise((r) => (resolve = r)),
    )
    const store = useLobbyStore()
    const promise = store.fetchRooms()
    expect(store.loading).toBe(true)
    resolve({ ok: true, json: async () => [] } as Response)
    await promise
    expect(store.loading).toBe(false)
  })

  // --- createRoom ---

  it('createRoom returns roomId and inits session as white', async () => {
    mockFetch({ room_id: 'r1', session_id: 's1', player_id: 'p1' })
    const store = useLobbyStore()
    const result = await store.createRoom('Alice', 'ukrainian', 'game_clock', 600)
    expect(result).toBe('r1')

    const session = useSessionStore()
    expect(session.sessionId).toBe('s1')
    expect(session.playerId).toBe('p1')
    expect(session.playerColor).toBe('white')
    expect(session.playerName).toBe('Alice')
  })

  it('createRoom returns null and sets error on http failure', async () => {
    mockFetch('Room not found', false)
    const store = useLobbyStore()
    const result = await store.createRoom('Alice', 'ukrainian', 'game_clock', 600)
    expect(result).toBeNull()
    expect(store.error).toBeTruthy()
  })

  it('createRoom sends correct request body', async () => {
    const spy = mockFetch({ room_id: 'r1', session_id: 's1', player_id: 'p1' })
    const store = useLobbyStore()
    await store.createRoom('Alice', 'brazilian', 'move', 30)
    const body = JSON.parse(spy.mock.calls[0][1]?.body as string)
    expect(body.player_name).toBe('Alice')
    expect(body.rules).toBe('brazilian')
    expect(body.timer_type).toBe('move')
    expect(body.timer_duration).toBe(30)
  })

  // --- joinRoom ---

  it('joinRoom returns gameId and inits session as black', async () => {
    mockFetch({ game_id: 'g1', session_id: 's2', player_id: 'p2' })
    const store = useLobbyStore()
    const result = await store.joinRoom('r1', 'Bob')
    expect(result).toBe('g1')

    const session = useSessionStore()
    expect(session.playerColor).toBe('black')
    expect(session.playerName).toBe('Bob')
  })

  it('joinRoom returns null and sets error on failure', async () => {
    mockFetch('Room full', false)
    const store = useLobbyStore()
    const result = await store.joinRoom('r1', 'Bob')
    expect(result).toBeNull()
    expect(store.error).toBeTruthy()
  })

  it('joinRoom sends correct URL and body', async () => {
    const spy = mockFetch({ game_id: 'g1', session_id: 's2', player_id: 'p2' })
    const store = useLobbyStore()
    await store.joinRoom('room-abc', 'Bob')
    expect(spy.mock.calls[0][0]).toContain('room-abc')
    const body = JSON.parse(spy.mock.calls[0][1]?.body as string)
    expect(body.player_name).toBe('Bob')
  })
})
