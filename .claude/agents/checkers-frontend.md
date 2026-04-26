---
name: checkers-frontend
description: "Frontend architecture manifest for online checkers game. Reference this agent when creating Vue.js components, Pinia stores, composables, or WebSocket client logic."
---

# Checkers Game — Frontend Architecture

Стек: Vue.js 3, Composition API, Pinia, TypeScript.
Транспорт: WebSocket.

---

## Pinia Stores

```
useGameStore
  — board: BoardState             # розмір, valid_cells
  — pieces: Map<string, Piece>    # ключ: "row:col"
  — currentTurn: Color
  — state: GameState
  — pendingCapture: CaptureInProgress | null
  — captureChains: CaptureChain[] # pre-computed від бекенду
  — drawOffer: DrawOffer | null
  — winner: Color | null
  — drawReason: DrawReason | null
  — history: Move[]

useSessionStore
  — sessionId: string | null       # персистується в localStorage (ключ checkers_session)
  — playerId: string               # персистується в localStorage
  — playerColor: Color | null      # персистується в localStorage
  — playerName: string             # персистується в localStorage; НЕ скидається при reset()
  — connected: boolean             # НЕ персистується — завжди false при старті
  — reconnecting: boolean          # НЕ персистується — завжди false при старті

  # Persistence: watch([sessionId, playerId, playerColor, playerName]) → localStorage
  # При ініціалізації стору читає збережені дані з localStorage
  # reset() скидає sessionId/playerId/playerColor до null; playerName залишається навмисно

useLobbyStore
  — rooms: GameRoom[]
  — loading: boolean
```

---

## Компоненти

```
Board.vue
  — props: size (8 | 10)
  — рендерить сітку Cell компонентів
  — передає події кліку до батьківського компонента

Cell.vue
  — props: cell, isHighlighted, isSelected, hasPiece
  — підсвічується якщо входить до дозволених кліків (captureChains або valid moves)
  — емітить click(cell)

Piece.vue
  — props: color, type (MAN | QUEEN)
  — різний вигляд для шашки та дамки

CaptureHint.vue
  — відображає дозволені наступні клітинки під час серії захоплень
  — отримує дані з useGameStore.captureChains

GameTimer.vue
  — клієнтський відлік між WebSocket-оновленнями (useTimer composable)
  — візуально попереджає коли залишилось ≤ 1/10 початкового часу;
    поріг динамічний: displaySeconds[color] <= game.timer.config.duration_seconds / 10
  — по закінченню часу викликає ws.checkTimer(color) через onExpired callback переданий в useTimer
  — використовує useWebSocket для надсилання check_timer; бекенд авторитетно завершує гру

MoveHistory.vue
  — відображає список ходів з useGameStore.history

DrawOffer.vue
  — показується коли useGameStore.drawOffer не null
  — кнопки: прийняти / відхилити

GameControls.vue
  — кнопки: запропонувати нічию, здатися

Lobby.vue
  — список доступних ігор з useLobbyStore.rooms
  — форма створення нової гри (вибір правил, таймера)

ReconnectOverlay.vue
  — показується поки useSessionStore.reconnecting = true
```

---

## Composables

```
useWebSocket(sessionId)
  — singleton: _ws, _reconnectTimer, _attempts живуть на рівні модуля — одне з'єднання на застосунок
  — встановлює WebSocket з'єднання
  — автоматичний reconnect з exponential backoff
  — надсилає {type: "reconnect", session_id} після відновлення
  — оновлює useSessionStore.connected / reconnecting
  — диспетчеризує вхідні повідомлення до відповідних stores
  — disconnect() обнуляє _ws = null
  — checkTimer(color: Color) — надсилає {type: "check_timer", color} на бекенд

useCaptureTree(captureChains)
  — будує дерево дозволених кліків з list[CaptureChain]
  — getNextAllowedCells(currentCell) -> Cell[]
  — повертає null якщо серія завершена

useTimer(game, onExpired?: (color: Color) => void)
  — локальний відлік часу між WebSocket-оновленнями
  — синхронізується з сервером при кожному game_snapshot; _expiredFired.clear() при оновленні
  — emits warning(color) коли залишилось ≤ 1/10 від початкового часу (один раз за хід/гру)
  — викликає onExpired(color) коли час вийшов локально (один раз за хід: guard _expiredFired)
  — після onExpired бекенд є авторитетним: гравець програє, приходить game_finished
```

---

## WebSocket повідомлення

### Від бекенду до фронту

```
game_snapshot     — повний стан гри (при підключенні / reconnect)
move_made         — хід зроблено: оновлення pieces, currentTurn, history
capture_chains    — list[CaptureChain] для поточної фігури
timer_update      — оновлення залишків часу
draw_offered      — гравець запропонував нічию
game_finished     — гра завершена: winner або draw_reason
```

### Від фронту до бекенду

```
make_move         — {from_cell, to_cell}
select_capture    — {piece_cell, path} — крок у серії захоплень
offer_draw        — {}
respond_draw      — {accepted: bool}
resign            — {}
reconnect         — {session_id}
check_timer       — {color} — фронт повідомляє бекенд що час гравця вийшов локально; бекенд перевіряє і завершує гру
```

---

## Правила перевірки коду (чекліст)

- [ ] Board рендериться динамічно залежно від розміру (8×8 або 10×10)
- [ ] Клітинки підсвічуються тільки з `captureChains` або `valid_moves` від бекенду
- [ ] Фронт не обчислює валідність ходів самостійно — тільки відображає дозволені
- [ ] `useWebSocket` є singleton — `_ws`, `_reconnectTimer`, `_attempts` на рівні модуля
- [ ] `useWebSocket` має автоматичний reconnect
- [ ] Після reconnect надсилається `{type: "reconnect", session_id}`
- [ ] `ReconnectOverlay` блокує взаємодію під час відновлення
- [ ] Таймер синхронізується з сервером, не обчислюється локально автономно
- [ ] `GameTimer` показує візуальне попередження коли залишилось ≤ 1/10 початкового часу (поріг: `duration_seconds / 10`, не захардкоджені 30 с)
- [ ] По закінченню часу фронт надсилає `check_timer` — логіка завершення тільки на бекенді, фронт чекає `game_finished`
- [ ] `onExpired` callback у `useTimer` спрацьовує лише раз за хід (guard `_expiredFired`, скидається при новому snapshot)
- [ ] `CaptureHint` показує тільки дозволені наступні клітинки серії
- [ ] `useSessionStore` персистує `sessionId`, `playerId`, `playerColor`, `playerName` у localStorage (ключ `checkers_session`)
- [ ] `connected` та `reconnecting` НЕ персистуються — завжди `false` при старті сторінки
- [ ] `reset()` скидає `sessionId`/`playerId`/`playerColor` до `null`; `playerName` навмисно залишається
- [ ] `LobbyView` ініціалізує `playerName` зі стору і синхронізує зміни назад через `watch`
- [ ] Після hard refresh: `sessionId` з localStorage → `GameView` підключається до тієї ж гри автоматично
- [ ] Після навігації (кнопка / back button): `onUnmounted` → `session.reset()` → `sessionId = null` → reconnect не відбувається
