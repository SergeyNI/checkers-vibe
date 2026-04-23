import { useGameStore } from '../stores/useGameStore'
import { useSessionStore } from '../stores/useSessionStore'

function resolveWsBase(): string {
  const env = import.meta.env.VITE_WS_URL
  if (env) return env
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${location.host}`
}
const WS_BASE = resolveWsBase()
const MAX_RECONNECT = 6

export function useWebSocket() {
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let attempts = 0

  const gameStore = useGameStore()
  const session = useSessionStore()

  function connect(sessionId: string) {
    const url = `${WS_BASE}/ws/${sessionId}`
    ws = new WebSocket(url)

    ws.onopen = () => {
      session.connected = true
      session.reconnecting = false
      attempts = 0
    }

    ws.onmessage = ({ data }) => {
      const msg = JSON.parse(data as string)
      _dispatch(msg)
    }

    ws.onclose = () => {
      session.connected = false
      _scheduleReconnect(sessionId)
    }

    ws.onerror = () => ws?.close()
  }

  function send(message: Record<string, unknown>) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
    }
  }

  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    ws?.close()
    session.connected = false
    session.reconnecting = false
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
    if (attempts >= MAX_RECONNECT) return
    session.reconnecting = true
    const delay = Math.min(500 * 2 ** attempts, 16000)
    reconnectTimer = setTimeout(() => {
      attempts++
      connect(sessionId)
    }, delay)
  }

  return { connect, disconnect, makeMove, offerDraw, respondDraw, resign }
}
