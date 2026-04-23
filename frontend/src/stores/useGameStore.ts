import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { Cell, CaptureChain, GameSnapshot, PieceOnBoard } from '../types'

export const useGameStore = defineStore('game', () => {
  const game = ref<GameSnapshot | null>(null)
  const captureChains = ref<Record<string, CaptureChain[]>>({})
  const validMoves = ref<Record<string, Cell[]>>({})
  const selectedCell = ref<Cell | null>(null)

  function updateFromSnapshot(
    snapshot: GameSnapshot,
    chains: Record<string, CaptureChain[]>,
    moves: Record<string, Cell[]>,
  ) {
    game.value = snapshot
    captureChains.value = chains
    validMoves.value = moves
    selectedCell.value = null
  }

  function selectCell(cell: Cell | null) {
    selectedCell.value = cell
  }

  function $reset() {
    game.value = null
    captureChains.value = {}
    validMoves.value = {}
    selectedCell.value = null
  }

  const pieces = computed((): PieceOnBoard[] => game.value?.pieces ?? [])

  const boardSize = computed(() => game.value?.board_size ?? 8)

  const currentTurn = computed(() => game.value?.current_turn ?? null)

  const isMyTurn = (myColor: string) =>
    game.value?.state === 'active' && game.value.current_turn === myColor

  const pieceAt = (row: number, col: number): PieceOnBoard | undefined =>
    pieces.value.find(p => p.row === row && p.col === col)

  const captureTargetsFor = (row: number, col: number): Cell[] => {
    const key = `${row},${col}`
    return (captureChains.value[key] ?? []).map(c => c.path[0]).filter(Boolean)
  }

  const moveTargetsFor = (row: number, col: number): Cell[] =>
    validMoves.value[`${row},${col}`] ?? []

  const hasCapturesAvailable = computed(() => Object.keys(captureChains.value).length > 0)

  return {
    game,
    captureChains,
    validMoves,
    selectedCell,
    pieces,
    boardSize,
    currentTurn,
    isMyTurn,
    pieceAt,
    captureTargetsFor,
    moveTargetsFor,
    hasCapturesAvailable,
    updateFromSnapshot,
    selectCell,
    $reset,
  }
})
