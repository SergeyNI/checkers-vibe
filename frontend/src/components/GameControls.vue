<template>
  <div class="controls">
    <button
      class="btn btn-draw"
      :disabled="!canAct || drawPending"
      @click="$emit('offer-draw')"
    >
      {{ drawPending ? 'Нічия запропонована' : 'Запропонувати нічию' }}
    </button>
    <button class="btn btn-resign" :disabled="!canAct" @click="confirmResign">Здатись</button>
    <button class="btn btn-lobby" @click="$emit('go-lobby')">← До списку ігор</button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useGameStore } from '../stores/useGameStore'
import { useSessionStore } from '../stores/useSessionStore'

const emit = defineEmits<{
  'offer-draw': []
  resign: []
  'go-lobby': []
}>()

const gameStore = useGameStore()
const session = useSessionStore()

const canAct = computed(
  () =>
    gameStore.game?.state === 'active' || gameStore.game?.state === 'paused',
)

const drawPending = computed(
  () =>
    gameStore.game?.draw_offer?.status === 'pending' &&
    gameStore.game.draw_offer.offered_by === session.playerColor,
)

function confirmResign() {
  if (confirm('Ви впевнені, що хочете здатися?')) {
    emit('resign')
  }
}
</script>

<style scoped>
.controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.btn {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn:not(:disabled):hover {
  opacity: 0.85;
  transform: translateY(-1px);
}

.btn-draw {
  background: #4a7a4a;
  color: #fff;
}

.btn-resign {
  background: #7a2a2a;
  color: #fff;
}

.btn-lobby {
  background: #2a2a2a;
  color: #888;
  border: 1px solid #444;
  font-size: 0.8em;
  margin-top: 4px;
}
</style>
