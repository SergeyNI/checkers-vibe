import { useGameStore } from '../stores/useGameStore'
import { useSessionStore } from '../stores/useSessionStore'
import type { Color } from '../types'

function resolveWsBase(): string {
  const env = import.meta.env.VITE_WS_URL
  if (env) return env
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${location.host}`
}
const WS_BASE = resolveWsBase()
const MAX_RECONNECT = 6

// Module-level singleton so any component can call send()
let _ws: WebSocket | null = null
let _reconnectTimer: ReturnType<typeof setTimeout> | null = null
let _attempts = 0

export function useWebSocket() {

  const gameStore = useGameStore()
  const session = useSessionStore()

  function connect(sessionId: string) {
    const url = `${WS_BASE}/ws/${sessionId}`
    _ws = new WebSocket(url)

    _ws.onopen = () => {
      session.connected = true
      session.reconnecting = false
      _attempts = 0
    }

    _ws.onmessage = ({ data }) => {
      const msg = JSON.parse(data as string)
      _dispatch(msg)
    }

    _ws.onclose = () => {
      session.connected = false
      _scheduleReconnect(sessionId)
    }

    _ws.onerror = () => _ws?.close()
  }

  function send(message: Record<string, unknown>) {
    if (_ws?.readyState === WebSocket.OPEN) {
      _ws.send(JSON.stringify(message))
    }
  }

  function disconnect() {
    if (_reconnectTimer) clearTimeout(_reconnectTimer)
    _ws?.close()
    _ws = null
    session.connected = false
    session.reconnecting = false
  }

  function checkTimer(color: Color) {
    send({ type: 'check_timer', color })
  }

  function makeMove(fromCell: { row: number; col: number }, toCell: { row: number; col: number }) {
    send({ type: 'make_move', from_cell: fromCell, to_cell: toCell })
  }

  function offerDraw() {
    send({ type: 'offer_draw' })
  }

  function respondDraw(accepted: boolean) {
    send({ type: 'respond_draw', accepted })
  }

  function resign() {
    send({ type: 'resign' })
  }

  // --- internal ---

  function _dispatch(msg: Record<string, unknown>) {
    switch (msg.type) {
      case 'game_snapshot':
        gameStore.updateFromSnapshot(
          msg.game as never,
          (msg.capture_chains ?? {}) as never,
          (msg.valid_moves ?? {}) as never,
        )
        break
      case 'game_finished':
        // game snapshot буде оновлено окремим game_snapshot повідомленням
        break
      case 'draw_offered':
        // відображається через game.draw_offer у snapshot
        break
      case 'error':
        console.warn('[ws] server error:', msg.message)
        break
    }
  }

  function _scheduleReconnect(sessionId: string) {
    if (_attempts >= MAX_RECONNECT) return
    session.reconnecting = true
    const delay = Math.min(500 * 2 ** _attempts, 16000)
    _reconnectTimer = setTimeout(() => {
      _attempts++
      connect(sessionId)
    }, delay)
  }

  return { connect, disconnect, makeMove, offerDraw, respondDraw, resign, checkTimer }
}
