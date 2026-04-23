import { ref, watch, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import type { Color, GameSnapshot } from '../types'

export function useTimer(game: Ref<GameSnapshot | null>) {
  const displaySeconds = ref<Record<Color, number>>({ white: 0, black: 0 })
  let interval: ReturnType<typeof setInterval> | null = null

  // Синхронізуємо з сервером при кожному оновленні snapshot
  watch(
    game,
    (g) => {
      if (!g) return
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
        displaySeconds.value[active] = +(displaySeconds.value[active] - 0.1).toFixed(1)
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
