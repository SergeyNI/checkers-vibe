<template>
  <Teleport to="body">
    <div v-if="visible" class="overlay">
      <div class="modal">
        <div class="spinner" />
        <p class="status">{{ message }}</p>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSessionStore } from '../stores/useSessionStore'

const session = useSessionStore()

const visible = computed(() => !session.connected)

const message = computed(() =>
  session.reconnecting ? 'Відновлення з\'єднання...' : 'З\'єднання втрачено',
)
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #1e1e1e;
  border: 2px solid #444;
  border-radius: 12px;
  padding: 32px 48px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #444;
  border-top-color: #c8a020;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.status {
  color: #ccc;
  font-size: 1.1em;
  margin: 0;
}
</style>
