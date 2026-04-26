import { ref, watch, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import type { Color, GameSnapshot } from '../types'

export function useTimer(game: Ref<GameSnapshot | null>, onExpired?: (color: Color) => void) {
  const displaySeconds = ref<Record<Color, number>>({ white: 0, black: 0 })
  let interval: ReturnType<typeof setInterval> | null = null
  // guard: fire onExpired only once per turn (reset on each snapshot)
  const _expiredFired = new Set<Color>()

  watch(
    game,
    (g) => {
      if (!g) return
      _expiredFired.clear()
      displaySeconds.value = {
        white: g.timer.clocks.white?.remaining_seconds ?? 0,
        black: g.timer.clocks.black?.remaining_seconds ?? 0,
      }
    },
    { deep: true },
  )

  function startCountdown() {
    if (interval) clearInterval(interval)
    interval = setInterval(() => {
      const g = game.value
      if (!g || g.state !== 'active') return
      const active = g.current_turn
      if (displaySeconds.value[active] > 0) {
        displaySeconds.value[active] = Math.max(0, +(displaySeconds.value[active] - 0.1).toFixed(1))
      } else if (onExpired && !_expiredFired.has(active)) {
        _expiredFired.add(active)
        onExpired(active)
      }
    }, 100)
  }

  function stopCountdown() {
    if (interval) {
      clearInterval(interval)
      interval = null
    }
  }

  onUnmounted(stopCountdown)

  function format(seconds: number): string {
    const s = Math.max(0, Math.ceil(seconds))
    const m = Math.floor(s / 60)
    const rem = s % 60
    return `${m}:${String(rem).padStart(2, '0')}`
  }

  return { displaySeconds, format, startCountdown, stopCountdown }
}
