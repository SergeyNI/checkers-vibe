<template>
  <div class="game-page">
    <ReconnectOverlay />

    <!-- Loading state -->
    <div v-if="!game" class="waiting">
      <div class="spinner" />
      <p>Очікування гри...</p>
    </div>

    <template v-else>
      <!-- Game finished banner -->
      <div v-if="game.state === 'finished'" class="result-banner" :class="resultClass">
        <span>{{ resultText }}</span>
        <button class="btn-lobby" @click="goToLobby">← До списку ігор</button>
      </div>

      <!-- Paused banner -->
      <div v-if="game.state === 'paused'" class="paused-banner">
        Суперник відключився. Очікування...
      </div>

      <div class="game-layout">
        <!-- Left sidebar -->
        <aside class="sidebar left">
          <GameTimer />
          <div class="game-meta">
            <span class="rules-badge">{{ game.rules_name }}</span>
            <span class="size-badge">{{ game.board_size }}×{{ game.board_size }}</span>
          </div>
          <GameControls @offer-draw="ws.offerDraw()" @resign="ws.resign()" @go-lobby="goToLobby" />
          <DrawOffer @respond="ws.respondDraw($event)" />
        </aside>

        <!-- Board -->
        <main class="board-area">
          <Board @move="handleMove" />
        </main>

        <!-- Right sidebar -->
        <aside class="sidebar right">
          <MoveHistory />
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/useGameStore'
import { useSessionStore } from '../stores/useSessionStore'
import { useWebSocket } from '../composables/useWebSocket'
import Board from '../components/Board.vue'
import GameTimer from '../components/GameTimer.vue'
import GameControls from '../components/GameControls.vue'
import DrawOffer from '../components/DrawOffer.vue'
import MoveHistory from '../components/MoveHistory.vue'
import ReconnectOverlay from '../components/ReconnectOverlay.vue'
import type { Cell } from '../types'

const router = useRouter()
const gameStore = useGameStore()
const session = useSessionStore()
const ws = useWebSocket()

const game = computed(() => gameStore.game)

const resultClass = computed(() => {
  if (!game.value || game.value.state !== 'finished') return ''
  if (game.value.winner === null) return 'draw'
  return game.value.winner === session.playerColor ? 'win' : 'loss'
})

const resultText = computed(() => {
  if (!game.value) return ''
  if (game.value.winner === null) {
    const reasons: Record<string, string> = {
      agreement: 'Нічия за згодою',
      repetition: 'Нічия — повторення позиції',
      move_limit: 'Нічия — ліміт ходів',
    }
    return reasons[game.value.draw_reason ?? ''] ?? 'Нічия'
  }
  return game.value.winner === session.playerColor ? 'Ви перемогли!' : 'Ви програли'
})

function handleMove(from: Cell, to: Cell) {
  ws.makeMove(from, to)
}

function goToLobby() {
  ws.disconnect()
  gameStore.$reset()
  session.reset()
  router.push('/')
}

onMounted(() => {
  const sessionId = session.sessionId
  if (!sessionId) {
    router.push('/')
    return
  }
  ws.connect(sessionId)
})

onUnmounted(() => {
  ws.disconnect()
  gameStore.$reset()
  session.reset()
})
</script>

<style scoped>
.game-page {
  min-height: 100vh;
  background: #121212;
  color: #eee;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.waiting {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  gap: 16px;
  color: #888;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #333;
  border-top-color: #c8a020;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.result-banner {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 14px 24px;
  font-size: 1.3em;
  font-weight: bold;
}

.btn-lobby {
  font-size: 0.65em;
  font-weight: 600;
  padding: 6px 16px;
  border: none;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.15);
  color: inherit;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}

.btn-lobby:hover {
  background: rgba(255, 255, 255, 0.28);
}

.result-banner.win {
  background: #1e4a1e;
  color: #6de86d;
}

.result-banner.loss {
  background: #4a1e1e;
  color: #e86d6d;
}

.result-banner.draw {
  background: #3a3a1e;
  color: #e8e06d;
}

.paused-banner {
  width: 100%;
  text-align: center;
  padding: 10px;
  background: #2a2a1a;
  color: #c8a020;
  font-size: 0.95em;
}

.game-layout {
  display: flex;
  gap: 24px;
  padding: 24px 16px;
  align-items: flex-start;
  justify-content: center;
  flex-wrap: wrap;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 200px;
  max-width: 220px;
}

.game-meta {
  display: flex;
  gap: 6px;
}

.rules-badge,
.size-badge {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 0.75em;
  color: #aaa;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.board-area {
  flex-shrink: 0;
}
</style>
