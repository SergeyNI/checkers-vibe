import { createRouter, createWebHistory } from 'vue-router'
import LobbyView from './views/LobbyView.vue'
import GameView from './views/GameView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: LobbyView },
    { path: '/game/:gameId', component: GameView },
  ],
})

export default router
