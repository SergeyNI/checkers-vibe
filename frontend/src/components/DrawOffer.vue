<template>
  <div v-if="visible" class="draw-offer">
    <p class="message">
      <strong>{{ offererName }}</strong> пропонує нічию
    </p>
    <div class="actions">
      <button class="btn btn-accept" @click="$emit('respond', true)">Прийняти</button>
      <button class="btn btn-decline" @click="$emit('respond', false)">Відхилити</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useGameStore } from '../stores/useGameStore'
import { useSessionStore } from '../stores/useSessionStore'

defineEmits<{
  respond: [accepted: boolean]
}>()

const gameStore = useGameStore()
const session = useSessionStore()

const visible = computed(() => {
  const offer = gameStore.game?.draw_offer
  return (
    offer?.status === 'pending' && offer.offered_by !== session.playerColor
  )
})

const offererName = computed(() => {
  const offer = gameStore.game?.draw_offer
  if (!offer) return ''
  return gameStore.game?.players.find((p) => p.color === offer.offered_by)?.name ?? offer.offered_by
})
</script>

<style scoped>
.draw-offer {
  background: #2a3a2a;
  border: 2px solid #4a8a4a;
  border-radius: 10px;
  padding: 16px 20px;
  text-align: center;
}

.message {
  color: #ccc;
  margin: 0 0 12px;
  font-size: 0.95em;
}

.actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn:hover {
  opacity: 0.8;
}

.btn-accept {
  background: #4a8a4a;
  color: #fff;
}

.btn-decline {
  background: #6a3a3a;
  color: #fff;
}
</style>
