export type Color = 'white' | 'black'
export type PieceType = 'man' | 'queen'
export type GameState = 'waiting' | 'active' | 'paused' | 'finished'
export type TimerType = 'move' | 'game_clock'
export type DrawReason = 'agreement' | 'repetition' | 'move_limit'
export type OfferStatus = 'pending' | 'accepted' | 'declined'

export interface Cell {
  row: number
  col: number
}

export interface PieceOnBoard {
  row: number
  col: number
  color: Color
  type: PieceType
}

export interface PlayerInfo {
  id: string
  name: string
  color: Color
}

export interface PlayerClock {
  remaining_seconds: number
  is_running: boolean
}

export interface GameTimer {
  config: { type: TimerType; duration_seconds: number }
  clocks: Record<Color, PlayerClock>
  move_deadline: string | null
}

export interface DrawOffer {
  offered_by: Color
  offered_at: string
  status: OfferStatus
}

export interface PendingCapture {
  piece_cell: Cell
  completed_steps: number
}

export interface GameSnapshot {
  id: string
  board_size: 8 | 10
  rules_name: string
  pieces: PieceOnBoard[]
  players: PlayerInfo[]
  current_turn: Color
  state: GameState
  timer: GameTimer
  pending_capture: PendingCapture | null
  draw_offer: DrawOffer | null
  draw_reason: DrawReason | null
  winner: Color | null
  moves_since_capture: number
  history: HistoryMove[]
}

export interface HistoryMove {
  from_cell: Cell
  to_cell: Cell
  captured: Cell[]
}

export interface CaptureChain {
  path: Cell[]
  captured: Cell[]
}

export interface RoomInfo {
  room_id: string
  creator_name: string
  rules: string
  timer_type: string
  timer_duration: number
}
