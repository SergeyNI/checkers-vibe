<template>
  <div class="board-container">
    <div class="corner" />
    <div class="col-labels">
      <span v-for="col in displayCols" :key="col" class="label">{{ colLabel(col) }}</span>
    </div>

    <div class="row-label-col">
      <span v-for="row in displayRows" :key="row" class="label">{{ rowLabel(row) }}</span>
    </div>

    <div class="board" :style="boardStyle">
      <template v-for="row in displayRows" :key="row">
        <Cell
          v-for="col in displayCols"
          :key="`${row}-${col}`"
          :row="row"
          :col="col"
          :is-dark="isDark(row, col)"
          :piece="gameStore.pieceAt(row, col)"
          :is-selected="isSelected(row, col)"
          :is-capture-target="isCaptureTarget(row, col)"
          :is-move-target="isMoveTarget(row, col)"
          :is-pending-capture="isPendingCapture(row, col)"
          :can-move="canMove(row, col)"
          @click="handleCellClick"
        />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Cell from './Cell.vue'
import { useGameStore } from '../stores/useGameStore'
import { useSessionStore } from '../stores/useSessionStore'
import { useCaptureTree } from '../composables/useCaptureTree'
import type { Cell as CellType } from '../types'

const emit = defineEmits<{
  move: [from: CellType, to: CellType]
}>()

const gameStore = useGameStore()
const session = useSessionStore()
const captureTree = useCaptureTree(computed(() => gameStore.captureChains))

const boardSize = computed(() => gameStore.boardSize)

// Дані: row 0 = верх, WHITE на rows 0-2, BLACK на rows 5-7.
// Щоб власні шашки були внизу і a1→h8 ішло знизу-ліворуч вгору-праворуч:
//   WHITE: перевертаємо тільки РЯДКИ (row 7 вгорі, row 0 внизу), колонки без змін
//   BLACK: перевертаємо тільки КОЛОНКИ (col 7 ліворуч), рядки без змін
const flipRows = computed(() => session.playerColor === 'white')
const flipCols = computed(() => session.playerColor === 'black')

function range(n: number) {
  return Array.from({ length: n }, (_, i) => i)
}

const displayRows = computed(() =>
  flipRows.value ? range(boardSize.value).reverse() : range(boardSize.value),
)
const displayCols = computed(() =>
  flipCols.value ? range(boardSize.value).reverse() : range(boardSize.value),
)

const cellPx = computed(() => (boardSize.value === 10 ? 54 : 62))

const boardStyle = computed(() => {
  const size = boardSize.value * cellPx.value
  return {
    width: `${size}px`,
    height: `${size}px`,
    gridTemplateColumns: `repeat(${boardSize.value}, 1fr)`,
  }
})

// Для білих (перевернута дошка): row 0 = ряд 1 (внизу), row 7 = ряд 8 (вгорі)
// Для чорних: row 0 = ряд 8 (вгорі), row 7 = ряд 1 (внизу)
function rowLabel(row: number): string {
  return String(flipRows.value ? row + 1 : boardSize.value - row)
}

function colLabel(col: number): string {
  return String.fromCharCode(flipCols.value ? 97 + (boardSize.value - 1 - col) : 97 + col)
}

function isDark(row: number, col: number) {
  return (row + col) % 2 === 0
}

const pendingPiece = computed(() => gameStore.game?.pending_capture?.piece_cell ?? null)

const myTurn = computed(
  () =>
    gameStore.game?.state === 'active' &&
    gameStore.game.current_turn === session.playerColor,
)

// Підсвічувати шашки які мають доступні ходи
function canMove(row: number, col: number): boolean {
  if (!myTurn.value || !isDark(row, col)) return false
  const piece = gameStore.pieceAt(row, col)
  if (!piece || piece.color !== session.playerColor) return false
  if (gameStore.hasCapturesAvailable) return gameStore.captureTargetsFor(row, col).length > 0
  return gameStore.moveTargetsFor(row, col).length > 0
}

function isSelected(row: number, col: number): boolean {
  const sel = gameStore.selectedCell
  if (sel) return sel.row === row && sel.col === col
  const pp = pendingPiece.value
  if (pp) return pp.row === row && pp.col === col
  return false
}

function isCaptureTarget(row: number, col: number): boolean {
  if (!myTurn.value) return false
  const pp = pendingPiece.value
  if (pp) {
    return captureTree
      .getFirstStepTargets(pp.row, pp.col)
      .some((t) => t.row === row && t.col === col)
  }
  const sel = gameStore.selectedCell
  if (!sel || !gameStore.hasCapturesAvailable) return false
  return gameStore.captureTargetsFor(sel.row, sel.col).some((t) => t.row === row && t.col === col)
}

function isMoveTarget(row: number, col: number): boolean {
  if (!myTurn.value || gameStore.hasCapturesAvailable) return false
  const sel = gameStore.selectedCell
  if (!sel) return false
  return gameStore.moveTargetsFor(sel.row, sel.col).some((t) => t.row === row && t.col === col)
}

function isPendingCapture(row: number, col: number): boolean {
  const pp = pendingPiece.value
  return !!pp && pp.row === row && pp.col === col
}

function handleCellClick(row: number, col: number) {
  if (!myTurn.value) return

  const pp = pendingPiece.value
  if (pp) {
    const targets = captureTree.getFirstStepTargets(pp.row, pp.col)
    if (targets.some((t) => t.row === row && t.col === col)) {
      emit('move', pp, { row, col })
    }
    return
  }

  const sel = gameStore.selectedCell

  if (sel) {
    if (isCaptureTarget(row, col) || isMoveTarget(row, col)) {
      emit('move', sel, { row, col })
      gameStore.selectCell(null)
      return
    }
  }

  if (!isDark(row, col)) return

  const piece = gameStore.pieceAt(row, col)
  if (piece && piece.color === session.playerColor) {
    if (canMove(row, col)) {
      gameStore.selectCell({ row, col })
    } else {
      gameStore.selectCell(null)
    }
  } else {
    gameStore.selectCell(null)
  }
}
</script>

<style scoped>
.board-container {
  display: inline-grid;
  grid-template-areas:
    'corner col-labels'
    'row-labels board';
  grid-template-columns: 20px 1fr;
  grid-template-rows: 20px 1fr;
  gap: 2px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.corner {
  grid-area: corner;
}

.col-labels {
  grid-area: col-labels;
  display: flex;
}

.row-label-col {
  grid-area: row-labels;
  display: flex;
  flex-direction: column;
}

.label {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  font-size: 0.7em;
  font-family: monospace;
  flex: 1;
  user-select: none;
}

.board {
  grid-area: board;
  display: grid;
  border: 3px solid #5a3010;
  border-radius: 2px;
}
</style>
