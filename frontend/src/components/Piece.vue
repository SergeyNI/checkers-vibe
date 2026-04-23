<template>
  <div class="piece" :class="[color, { queen: type === 'queen' }]">
    <span v-if="type === 'queen'" class="crown">♛</span>
  </div>
</template>

<script setup lang="ts">
import type { Color, PieceType } from '../types'

defineProps<{
  color: Color
  type: PieceType
}>()
</script>

<style scoped>
.piece {
  width: 76%;
  height: 76%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.4), inset 0 -2px 4px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: transform 0.1s ease;
  user-select: none;
}

.piece:hover {
  transform: scale(1.05);
}

.piece.white {
  background: radial-gradient(circle at 35% 35%, #fff8f0, #d4c4a0);
  border: 2px solid #8b6914;
}

.piece.black {
  background: radial-gradient(circle at 35% 35%, #5a4a3a, #1a120a);
  border: 2px solid #6b4f2a;
}

.crown {
  font-size: 1.1em;
  line-height: 1;
  color: #ffd700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
}

.piece.white .crown {
  color: #8b6914;
}
</style>
