import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { Color, RoomInfo } from '../types'
import { useSessionStore } from './useSessionStore'

export const useLobbyStore = defineStore('lobby', () => {
  const rooms = ref<RoomInfo[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchRooms() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch('/api/lobby/rooms')
      rooms.value = await res.json()
    } catch (e) {
      error.value = 'Не вдалось завантажити список кімнат'
    } finally {
      loading.value = false
    }
  }

  async function createRoom(
    playerName: string,
    rules: string,
    timerType: string,
    timerDuration: number,
  ): Promise<string | null> {
    error.value = null
    try {
      const res = await fetch('/api/lobby/rooms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_name: playerName,
          rules,
          timer_type: timerType,
          timer_duration: timerDuration,
        }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()

      const session = useSessionStore()
      session.init(data.session_id, data.player_id, 'white' as Color, playerName)
      session.gameRoute = `/game/${data.room_id}`
      return data.room_id
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Помилка створення кімнати'
      return null
    }
  }

  async function joinRoom(roomId: string, playerName: string): Promise<string | null> {
    error.value = null
    try {
      const res = await fetch(`/api/lobby/rooms/${roomId}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_name: playerName }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()

      const session = useSessionStore()
      session.init(data.session_id, data.player_id, 'black' as Color, playerName)
      session.gameRoute = `/game/${data.game_id}`
      return data.game_id
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Помилка приєднання'
      return null
    }
  }

  return { rooms, loading, error, fetchRooms, createRoom, joinRoom }
})
