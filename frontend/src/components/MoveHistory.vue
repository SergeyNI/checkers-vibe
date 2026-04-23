<template>
  <div class="history">
    <h3 class="title">Ходи</h3>
    <div ref="listEl" class="list">
      <div
        v-for="(move, i) in history"
        :key="i"
        class="move-row"
        :class="i % 2 === 0 ? 'white-move' : 'black-move'"
      >
        <span class="move-num">{{ Math.floor(i / 2) + 1 }}.</span>
        <span class="move-notation">{{ formatMove(move) }}</span>
        <span v-if="move.captured.length" class="capture-badge">×{{ move.captured.length }}</span>
      </div>
      <div v-if="history.length === 0" class="empty">Ходів ще не було</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { useGameStore } from '../stores/useGameStore'
import type { HistoryMove } from '../types'

const gameStore = useGameStore()
const listEl = ref<HTMLElement | null>(null)

const history = computed(() => gameStore.game?.history ?? [])

function formatMove(move: HistoryMove): string {
  const from = cellLabel(move.from_cell.row, move.from_cell.col)
  const to = cellLabel(move.to_cell.row, move.to_cell.col)
  const sep = move.captured.length ? ':' : '-'
  return `${from}${sep}${to}`
}

function cellLabel(row: number, col: number): string {
  const size = gameStore.boardSize
  const letter = String.fromCharCode(97 + col)
  const number = size - row
  return `${letter}${number}`
}

watch(history, async () => {
  await nextTick()
  if (listEl.value) {
    listEl.value.scrollTop = listEl.value.scrollHeight
  }
})
</script>

<style scoped>
.history {
  display: flex;
  flex-direction: column;
  min-width: 160px;
  max-width: 200px;
}

.title {
  color: #aaa;
  font-size: 0.85em;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 8px;
}

.list {
  flex: 1;
  overflow-y: auto;
  max-height: 320px;
  background: #1a1a1a;
  border-radius: 6px;
  padding: 4px 0;
}

.move-row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-size: 0.85em;
  font-family: monospace;
}

.white-move {
  background: #222;
}

.black-move {
  background: #1c1c1c;
}

.move-num {
  color: #666;
  min-width: 24px;
}

.move-notation {
  color: #ccc;
  flex: 1;
}

.capture-badge {
  color: #e06060;
  font-size: 0.8em;
}

.empty {
  color: #555;
  text-align: center;
  padding: 16px;
  font-size: 0.85em;
}
</style>
