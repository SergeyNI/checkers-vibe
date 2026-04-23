<template>
  <div
    class="cell"
    :class="{
      dark: isDark,
      light: !isDark,
      selected: isSelected,
      'capture-target': isCaptureTarget,
      'move-target': isMoveTarget,
      'pending-capture': isPendingCapture,
      'can-move': canMove && !isSelected,
    }"
    @click="$emit('click', row, col)"
  >
    <Piece v-if="piece" :color="piece.color" :type="piece.type" />
    <span v-else-if="isCaptureTarget || isMoveTarget" class="target-dot" />
  </div>
</template>

<script setup lang="ts">
import Piece from './Piece.vue'
import type { PieceOnBoard } from '../types'

defineProps<{
  row: number
  col: number
  isDark: boolean
  piece?: PieceOnBoard
  isSelected: boolean
  isCaptureTarget: boolean
  isMoveTarget: boolean
  isPendingCapture: boolean
  canMove: boolean
}>()

defineEmits<{
  click: [row: number, col: number]
}>()
</script>

<style scoped>
.cell {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: default;
}

.cell.light {
  background: #f0d9b5;
}

.cell.dark {
  background: #8b5e3c;
}

.cell.dark.can-move {
  background: #7a5232;
  cursor: pointer;
}

.cell.dark.selected {
  background: #cfa84a;
}

.cell.dark.capture-target {
  background: #a03030;
  cursor: pointer;
}

.cell.dark.move-target {
  background: #4a9a4a;
  cursor: pointer;
}

.cell.dark.pending-capture {
  background: #c08020;
}

.target-dot {
  width: 30%;
  height: 30%;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.5);
  pointer-events: none;
}

.cell.capture-target .target-dot {
  background: rgba(255, 200, 200, 0.7);
}

.cell.move-target .target-dot {
  background: rgba(200, 255, 200, 0.7);
}
</style>
