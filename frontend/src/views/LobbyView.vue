<template>
  <div class="lobby">
    <header class="lobby-header">
      <h1>Шашки онлайн</h1>
    </header>

    <div class="lobby-body">
      <!-- Create room -->
      <section class="panel create-panel">
        <h2>Нова гра</h2>
        <form @submit.prevent="handleCreate">
          <div class="field">
            <label>Ваше ім'я</label>
            <input v-model="playerName" type="text" placeholder="Введіть ім'я" maxlength="30" required />
          </div>
          <div class="field">
            <label>Правила</label>
            <select v-model="rules">
              <option value="ukrainian">Українські (8×8)</option>
              <option value="brazilian">Бразильські (8×8)</option>
              <option value="international">Міжнародні (10×10)</option>
            </select>
          </div>
          <div class="field">
            <label>Таймер</label>
            <select v-model="timerType">
              <option value="game_clock">На гру</option>
              <option value="move">На хід</option>
            </select>
          </div>
          <div class="field">
            <label>Час (хв)</label>
            <input v-model.number="timerMinutes" type="number" min="1" max="60" />
          </div>
          <button type="submit" class="btn btn-primary" :disabled="lobbyStore.loading">
            Створити кімнату
          </button>
        </form>
        <p v-if="lobbyStore.error" class="error">{{ lobbyStore.error }}</p>
      </section>

      <!-- Room list -->
      <section class="panel rooms-panel">
        <div class="rooms-header">
          <h2>Відкриті кімнати</h2>
          <button class="btn btn-sm" @click="lobbyStore.fetchRooms()">↻ Оновити</button>
        </div>

        <div v-if="lobbyStore.loading" class="loading">Завантаження...</div>

        <div v-else-if="lobbyStore.rooms.length === 0" class="empty">
          Немає доступних кімнат
        </div>

        <div v-else class="rooms-list">
          <div v-for="room in lobbyStore.rooms" :key="room.room_id" class="room-card">
            <div class="room-info">
              <span class="room-creator">{{ room.creator_name }}</span>
              <span class="room-meta">{{ rulesLabel(room.rules) }} · {{ room.timer_duration / 60 }} хв</span>
            </div>
            <button class="btn btn-join" @click="handleJoin(room.room_id)">Приєднатись</button>
          </div>
        </div>

        <div v-if="joinError" class="error">{{ joinError }}</div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLobbyStore } from '../stores/useLobbyStore'

const router = useRouter()
const lobbyStore = useLobbyStore()

const playerName = ref('')
const rules = ref('ukrainian')
const timerType = ref('game_clock')
const timerMinutes = ref(10)
const joinError = ref<string | null>(null)

onMounted(() => lobbyStore.fetchRooms())

function rulesLabel(r: string) {
  const map: Record<string, string> = {
    ukrainian: 'Українські',
    brazilian: 'Бразильські',
    international: 'Міжнародні',
  }
  return map[r] ?? r
}

async function handleCreate() {
  const roomId = await lobbyStore.createRoom(
    playerName.value,
    rules.value,
    timerType.value,
    timerMinutes.value * 60,
  )
  if (roomId) {
    router.push(`/game/${roomId}`)
  }
}

async function handleJoin(roomId: string) {
  joinError.value = null
  if (!playerName.value.trim()) {
    joinError.value = 'Введіть ваше ім\'я перед тим як приєднатись'
    return
  }
  const gameId = await lobbyStore.joinRoom(roomId, playerName.value)
  if (gameId) {
    router.push(`/game/${gameId}`)
  } else {
    joinError.value = lobbyStore.error ?? 'Помилка приєднання'
  }
}
</script>

<style scoped>
.lobby {
  min-height: 100vh;
  background: #121212;
  color: #eee;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.lobby-header {
  padding: 32px 0 16px;
}

.lobby-header h1 {
  color: #c8a020;
  font-size: 2.2em;
  margin: 0;
}

.lobby-body {
  display: flex;
  gap: 32px;
  padding: 24px 16px;
  width: 100%;
  max-width: 860px;
  flex-wrap: wrap;
}

.panel {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
  flex: 1;
  min-width: 280px;
}

.panel h2 {
  color: #c8a020;
  margin: 0 0 20px;
  font-size: 1.1em;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 14px;
}

.field label {
  font-size: 0.8em;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.field input,
.field select {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  color: #eee;
  padding: 8px 10px;
  font-size: 0.95em;
}

.field input:focus,
.field select:focus {
  outline: none;
  border-color: #c8a020;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn:hover {
  opacity: 0.85;
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-primary {
  background: #c8a020;
  color: #111;
  width: 100%;
  margin-top: 8px;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 0.85em;
  background: #333;
  color: #ccc;
}

.btn-join {
  background: #3a6a3a;
  color: #fff;
  padding: 6px 14px;
  font-size: 0.85em;
}

.rooms-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.rooms-header h2 {
  margin: 0;
}

.rooms-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.room-card {
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.room-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.room-creator {
  font-weight: 600;
  color: #eee;
}

.room-meta {
  font-size: 0.8em;
  color: #888;
}

.loading,
.empty {
  color: #666;
  text-align: center;
  padding: 24px;
  font-size: 0.9em;
}

.error {
  color: #e05050;
  font-size: 0.85em;
  margin-top: 10px;
}
</style>
