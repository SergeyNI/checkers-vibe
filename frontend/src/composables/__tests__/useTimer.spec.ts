import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useTimer } from '../useTimer'
import type { GameSnapshot } from '../../types'

function gameRef(overrides: Partial<GameSnapshot> = {}) {
  return ref<GameSnapshot | null>({
    id: 'g1',
    board_size: 8,
    rules_name: 'ukrainian',
    pieces: [],
    players: [],
    current_turn: 'white',
    state: 'active',
    timer: {
      config: { type: 'game_clock', duration_seconds: 300 },
      clocks: {
        white: { remaining_seconds: 120, is_running: true },
        black: { remaining_seconds: 90, is_running: false },
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
  } as GameSnapshot)
}

describe('useTimer', () => {
  describe('format', () => {
    const { format } = useTimer(ref(null))

    it('formats 0 as 0:00', () => expect(format(0)).toBe('0:00'))
    it('formats 65 as 1:05', () => expect(format(65)).toBe('1:05'))
    it('formats 600 as 10:00', () => expect(format(600)).toBe('10:00'))
    it('formats 3599 as 59:59', () => expect(format(3599)).toBe('59:59'))
    it('rounds up fractional seconds', () => expect(format(59.1)).toBe('1:00'))
    it('pads single-digit seconds', () => expect(format(61)).toBe('1:01'))
    it('clamps negative values to 0:00', () => expect(format(-5)).toBe('0:00'))
  })

  describe('snapshot sync', () => {
    it('syncs displaySeconds when game ref changes', async () => {
      const game = ref<GameSnapshot | null>(null)
      const { displaySeconds } = useTimer(game)

      game.value = gameRef().value
      await nextTick()

      expect(displaySeconds.value.white).toBe(120)
      expect(displaySeconds.value.black).toBe(90)
    })

    it('updates when snapshot changes', async () => {
      const game = gameRef()
      const { displaySeconds } = useTimer(game)
      await nextTick()

      game.value!.timer.clocks.white.remaining_seconds = 50
      game.value = { ...game.value! }
      await nextTick()

      expect(displaySeconds.value.white).toBe(50)
    })
  })

  describe('countdown', () => {
    beforeEach(() => vi.useFakeTimers())
    afterEach(() => vi.useRealTimers())

    it('decrements active player every 100ms', () => {
      const game = gameRef()
      const { displaySeconds, startCountdown } = useTimer(game)
      displaySeconds.value = { white: 10, black: 10 }
      startCountdown()

      vi.advanceTimersByTime(500)
      expect(displaySeconds.value.white).toBeCloseTo(9.5, 1)
      expect(displaySeconds.value.black).toBe(10)
    })

    it('does not decrement inactive player', () => {
      const game = gameRef({ current_turn: 'black' } as never)
      const { displaySeconds, startCountdown } = useTimer(game)
      displaySeconds.value = { white: 10, black: 10 }
      startCountdown()

      vi.advanceTimersByTime(300)
      expect(displaySeconds.value.white).toBe(10)
      expect(displaySeconds.value.black).toBeCloseTo(9.7, 1)
    })

    it('does not go below 0', () => {
      const game = gameRef()
      const { displaySeconds, startCountdown } = useTimer(game)
      displaySeconds.value = { white: 0.05, black: 10 }
      startCountdown()

      vi.advanceTimersByTime(500)
      expect(displaySeconds.value.white).toBeGreaterThanOrEqual(0)
    })

    it('pauses when game state is not active', () => {
      const game = gameRef({ state: 'paused' } as never)
      const { displaySeconds, startCountdown } = useTimer(game)
      displaySeconds.value = { white: 10, black: 10 }
      startCountdown()

      vi.advanceTimersByTime(500)
      expect(displaySeconds.value.white).toBe(10) // no change — game paused
    })

    it('stopCountdown halts decrement', () => {
      const game = gameRef()
      const { displaySeconds, startCountdown, stopCountdown } = useTimer(game)
      displaySeconds.value = { white: 10, black: 10 }
      startCountdown()
      vi.advanceTimersByTime(200)
      const after200 = displaySeconds.value.white
      stopCountdown()
      vi.advanceTimersByTime(1000)
      expect(displaySeconds.value.white).toBe(after200)
    })

    it('calling startCountdown twice does not double-decrement', () => {
      const game = gameRef()
      const { displaySeconds, startCountdown } = useTimer(game)
      displaySeconds.value = { white: 10, black: 10 }
      startCountdown()
      startCountdown()

      vi.advanceTimersByTime(1000)
      // Should decrement by ~1s, not ~2s
      expect(displaySeconds.value.white).toBeGreaterThan(8.5)
    })
  })
})
