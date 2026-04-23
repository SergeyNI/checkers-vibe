import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useGameStore } from '../useGameStore'
import type { GameSnapshot, CaptureChain } from '../../types'

function snap(overrides: Partial<GameSnapshot> = {}): GameSnapshot {
  return {
    id: 'g1',
    board_size: 8,
    rules_name: 'ukrainian',
    pieces: [],
    players: [
      { id: 'p1', name: 'Alice', color: 'white' },
      { id: 'p2', name: 'Bob', color: 'black' },
    ],
    current_turn: 'white',
    state: 'active',
    timer: {
      config: { type: 'game_clock', duration_seconds: 300 },
      clocks: {
        white: { remaining_seconds: 300, is_running: true },
        black: { remaining_seconds: 300, is_running: false },
      },
      move_deadline: null,
    },
    pending_capture: null,
    draw_offer: null,
    draw_reason: null,
    winner: null,
    moves_since_capture: 0,
    history: [],
    ...overrides,
  }
}

describe('useGameStore', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('initializes with null game', () => {
    expect(useGameStore().game).toBeNull()
  })

  it('updateFromSnapshot sets game, chains, moves and clears selection', () => {
    const store = useGameStore()
    store.selectCell({ row: 2, col: 2 })
    const chains = { '2,2': [{ path: [{ row: 4, col: 4 }], captured: [{ row: 3, col: 3 }] }] }
    const moves = { '5,1': [{ row: 6, col: 0 }] }
    store.updateFromSnapshot(snap(), chains, moves)
    expect(store.game?.id).toBe('g1')
    expect(store.captureChains).toEqual(chains)
    expect(store.validMoves).toEqual(moves)
    expect(store.selectedCell).toBeNull()
  })

  it('pieces computed returns snapshot pieces array', () => {
    const store = useGameStore()
    store.updateFromSnapshot(
      snap({ pieces: [{ row: 2, col: 2, color: 'white', type: 'man' }] }),
      {},
      {},
    )
    expect(store.pieces).toHaveLength(1)
    expect(store.pieces[0].color).toBe('white')
  })

  it('boardSize returns 8 by default', () => {
    const store = useGameStore()
    store.updateFromSnapshot(snap(), {}, {})
    expect(store.boardSize).toBe(8)
  })

  it('boardSize returns 10 for 10x10 game', () => {
    const store = useGameStore()
    store.updateFromSnapshot(snap({ board_size: 10 }), {}, {})
    expect(store.boardSize).toBe(10)
  })

  it('isMyTurn returns true only for active game and correct color', () => {
    const store = useGameStore()
    store.updateFromSnapshot(snap({ state: 'active', current_turn: 'white' }), {}, {})
    expect(store.isMyTurn('white')).toBe(true)
    expect(store.isMyTurn('black')).toBe(false)
  })

  it('isMyTurn returns false when game is paused', () => {
    const store = useGameStore()
    store.updateFromSnapshot(snap({ state: 'paused' }), {}, {})
    expect(store.isMyTurn('white')).toBe(false)
  })

  it('pieceAt finds piece by row/col', () => {
    const store = useGameStore()
    store.updateFromSnapshot(
      snap({ pieces: [{ row: 3, col: 5, color: 'black', type: 'queen' }] }),
      {},
      {},
    )
    expect(store.pieceAt(3, 5)?.type).toBe('queen')
    expect(store.pieceAt(0, 0)).toBeUndefined()
  })

  it('hasCapturesAvailable is true when captureChains non-empty', () => {
    const store = useGameStore()
    const chains: Record<string, CaptureChain[]> = {
      '2,2': [{ path: [{ row: 4, col: 4 }], captured: [{ row: 3, col: 3 }] }],
    }
    store.updateFromSnapshot(snap(), chains, {})
    expect(store.hasCapturesAvailable).toBe(true)
  })

  it('hasCapturesAvailable is false when no chains', () => {
    const store = useGameStore()
    store.updateFromSnapshot(snap(), {}, {})
    expect(store.hasCapturesAvailable).toBe(false)
  })

  it('captureTargetsFor returns first path cell of each chain', () => {
    const store = useGameStore()
    store.updateFromSnapshot(
      snap(),
      {
        '2,2': [
          { path: [{ row: 4, col: 4 }], captured: [{ row: 3, col: 3 }] },
          { path: [{ row: 4, col: 0 }], captured: [{ row: 3, col: 1 }] },
        ],
      },
      {},
    )
    const targets = store.captureTargetsFor(2, 2)
    expect(targets).toHaveLength(2)
    expect(targets).toContainEqual({ row: 4, col: 4 })
    expect(targets).toContainEqual({ row: 4, col: 0 })
  })

  it('moveTargetsFor returns cells from validMoves', () => {
    const store = useGameStore()
    store.updateFromSnapshot(snap(), {}, { '5,1': [{ row: 6, col: 0 }, { row: 6, col: 2 }] })
    expect(store.moveTargetsFor(5, 1)).toHaveLength(2)
    expect(store.moveTargetsFor(0, 0)).toEqual([])
  })

  it('selectCell sets selected cell', () => {
    const store = useGameStore()
    store.selectCell({ row: 2, col: 4 })
    expect(store.selectedCell).toEqual({ row: 2, col: 4 })
  })

  it('selectCell with null clears selection', () => {
    const store = useGameStore()
    store.selectCell({ row: 2, col: 4 })
    store.selectCell(null)
    expect(store.selectedCell).toBeNull()
  })

  it('$reset clears all state', () => {
    const store = useGameStore()
    store.updateFromSnapshot(snap(), { '2,2': [] }, { '3,3': [] })
    store.selectCell({ row: 1, col: 1 })
    store.$reset()
    expect(store.game).toBeNull()
    expect(store.captureChains).toEqual({})
    expect(store.validMoves).toEqual({})
    expect(store.selectedCell).toBeNull()
  })
})
