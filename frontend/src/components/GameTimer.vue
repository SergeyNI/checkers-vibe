<template>
  <div class="timers">
    <div class="timer-mode">{{ timerModeLabel }}</div>

    <template v-if="isMoveTimer">
      <!-- MOVE: показуємо тільки активного гравця -->
      <div
        v-for="color in (['black', 'white'] as const)"
        v-show="isActive(color)"
        :key="color"
        class="clock active"
        :class="{ low: isLow(color), me: color === myColor }"
      >
        <span class="player-name">{{ playerName(color) }}</span>
        <span class="time">{{ format(displaySeconds[color]) }}</span>
      </div>
    </template>

    <template v-else>
      <!-- GAME_CLOCK: показуємо обох гравців -->
      <div
        v-for="color in (['black', 'white'] as const)"
        :key="color"
        class="clock"
        :class="{
          active: isActive(color),
          low: isLow(color),
          me: color === myColor,
        }"
      >
        <span class="player-name">{{ playerName(color) }}</span>
        <span class="time">{{ format(displaySeconds[color]) }}</span>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, onUnmounted } from 'vue'
import { useGameStore } from '../stores/useGameStore'
import { useSessionStore } from '../stores/useSessionStore'
import { useTimer } from '../composables/useTimer'
import { useWebSocket } from '../composables/useWebSocket'

const gameStore = useGameStore()
const session = useSessionStore()
const ws = useWebSocket()

const game = computed(() => gameStore.game)
const { displaySeconds, format, startCountdown, stopCountdown } = useTimer(game, (color) => {
  ws.checkTimer(color)
})

const myColor = computed(() => session.playerColor)

const isMoveTimer = computed(() => game.value?.timer?.config?.type === 'move')

const timerModeLabel = computed(() => {
  const type = game.value?.timer?.config?.type
  if (type === 'move') return 'На хід'
  if (type === 'game_clock') return 'На гру'
  return ''
})

function isActive(color: 'white' | 'black') {
  return game.value?.state === 'active' && game.value.current_turn === color
}

function isLow(color: 'white' | 'black') {
  const initial = game.value?.timer?.config?.duration_seconds ?? 0
  if (initial <= 0) return false
  return displaySeconds.value[color] <= initial / 10
}

function playerName(color: 'white' | 'black') {
  return game.value?.players.find((p) => p.color === color)?.name ?? color
}

watch(
  () => game.value?.state,
  (state) => {
    if (state === 'active') startCountdown()
    else stopCountdown()
  },
  { immediate: true },
)

onUnmounted(stopCountdown)
</script>

<style scoped>
.timers {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.timer-mode {
  font-size: 0.7em;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #888;
  text-align: center;
}

.clock {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-radius: 8px;
  background: #2a2a2a;
  border: 2px solid #444;
  transition: background 0.2s, border-color 0.2s;
  min-width: 200px;
}

.clock.active {
  background: #3a3010;
  border-color: #c8a020;
  box-shadow: 0 0 8px rgba(200, 160, 32, 0.4);
}

.clock.low .time {
  color: #e05050;
}

.clock.me {
  border-left: 4px solid #5090e0;
}

.player-name {
  color: #ccc;
  font-size: 0.9em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 120px;
}

.time {
  font-size: 1.6em;
  font-weight: bold;
  font-family: monospace;
  color: #eee;
  letter-spacing: 2px;
}
</style>
