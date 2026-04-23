import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { Color } from '../types'

export const useSessionStore = defineStore('session', () => {
  const sessionId = ref<string | null>(null)
  const playerId = ref<string | null>(null)
  const playerColor = ref<Color | null>(null)
  const playerName = ref<string>('')
  const connected = ref(false)
  const reconnecting = ref(false)

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
    connected.value = false
    reconnecting.value = false
  }

  return { sessionId, playerId, playerColor, playerName, connected, reconnecting, init, reset }
})
