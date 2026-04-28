import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import type { Color } from '../types'

const STORAGE_KEY = 'checkers_session'

function load() {
  try { return JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? 'null') } catch { return null }
}

export const useSessionStore = defineStore('session', () => {
  const s = load()

  const sessionId = ref<string | null>(s?.sessionId ?? null)
  const playerId = ref<string | null>(s?.playerId ?? null)
  const playerColor = ref<Color | null>(s?.playerColor ?? null)
  const playerName = ref<string>(s?.playerName ?? '')
  const gameRoute = ref<string | null>(s?.gameRoute ?? null)
  const connected = ref(false)
  const reconnecting = ref(false)

  // persist to sessionStorage on any change (tab-isolated: two tabs = two sessions)
  watch([sessionId, playerId, playerColor, playerName, gameRoute], () => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
      sessionId: sessionId.value,
      playerId: playerId.value,
      playerColor: playerColor.value,
      playerName: playerName.value,
      gameRoute: gameRoute.value,
    }))
  })

  function init(sid: string, pid: string, color: Color, name: string) {
    sessionId.value = sid
    playerId.value = pid
    playerColor.value = color
    playerName.value = name
  }

  function reset() {
    sessionId.value = null
    playerId.value = null
    playerColor.value = null
    gameRoute.value = null
    connected.value = false
    reconnecting.value = false
    // playerName intentionally kept — user doesn't re-enter name after each game
  }

  return { sessionId, playerId, playerColor, playerName, gameRoute, connected, reconnecting, init, reset }
})
