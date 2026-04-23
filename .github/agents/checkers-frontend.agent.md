---
name: checkers-frontend
description: "Frontend architecture manifest for online checkers game. Reference this agent when creating Vue.js components, Pinia stores, composables, or WebSocket client logic."
applyTo:
  - "**/*.vue"
  - "**/*.ts"
  - "frontend/**/*"
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
  — sessionId: string | null
  — playerId: string
  — playerColor: Color | null
  — connected: boolean
  — reconnecting: boolean

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
  — props: type (MOVE | GAME_CLOCK), clocks
  — клієнтський відлік між WebSocket-оновленнями (useTimer composable)
  — візуально попереджає коли час спливає

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
  — встановлює WebSocket з'єднання
  — автоматичний reconnect з exponential backoff
  — надсилає {type: "reconnect", session_id} після відновлення
  — оновлює useSessionStore.connected / reconnecting
  — диспетчеризує вхідні повідомлення до відповідних stores

useCaptureTree(captureChains)
  — будує дерево дозволених кліків з list[CaptureChain]
  — getNextAllowedCells(currentCell) -> Cell[]
  — повертає null якщо серія завершена

useTimer(config, clocks)
  — локальний відлік часу між WebSocket-оновленнями
  — синхронізується з сервером при кожному game_snapshot
  — емітить expired(color) коли час вийшов локально
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
```

---

## Правила перевірки коду (чекліст)

- [ ] Board рендериться динамічно залежно від розміру (8×8 або 10×10)
- [ ] Клітинки підсвічуються тільки з `captureChains` або `valid_moves` від бекенду
- [ ] Фронт не обчислює валідність ходів самостійно — тільки відображає дозволені
- [ ] `useWebSocket` має автоматичний reconnect
- [ ] Після reconnect надсилається `{type: "reconnect", session_id}`
- [ ] `ReconnectOverlay` блокує взаємодію під час відновлення
- [ ] Таймер синхронізується з сервером, не обчислюється локально автономно
- [ ] `CaptureHint` показує тільки дозволені наступні клітинки серії
