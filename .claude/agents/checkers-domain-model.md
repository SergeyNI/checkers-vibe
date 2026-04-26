---
name: checkers-domain-model
description: "Domain model manifest for online checkers game. Reference this agent when creating models, services, controllers, or Redis persistence. Covers board types 8x8 and 10x10, multiple rule sets, diagonal line geometry, timers, draw logic, and WebSocket session recovery."
---

# Checkers Game — Domain Model

Мова реалізації: Python (бекенд) + Vue.js (фронтенд).
Черга/кеш: Redis.
Транспорт: WebSocket.

---

## Моделі (від простого до складного)

### Рівень 1 — базові примітиви

```
Cell(row: int, col: int)
  — незмінний value object, координата темної клітинки на дошці
  — реалізується як @dataclass(frozen=True): дає __eq__ і __hash__ автоматично
  — __hash__ обов'язковий: Cell використовується як ключ dict[Cell, Piece]
  — Cell1 == Cell2 якщо row1 == row2 та col1 == col2

PieceType: enum
  — MAN    # звичайна шашка
  — QUEEN  # дамка

Color: enum
  — WHITE | BLACK
```

### Рівень 2 — геометрія дошки

```
DiagonalDirection: enum
  — ASCENDING   # зліва направо вгору (головна дорога: A1→H8)
  — DESCENDING  # зліва направо вниз  (лінії-двійники тощо)

DiagonalLine
  — cells: list[Cell]              # завжди впорядковані по зростанню row (канонічний порядок)
  — direction: DiagonalDirection
  — name: str | None               # наприклад "main_road" для головної діагоналі

  # Напрямок обходу — відповідальність MoveService, не DiagonalLine:
  #   WHITE рухається вперед:  cells[current_index + 1:]
  #   BLACK рухається назад:   cells[:current_index][::-1]
  #   QUEEN рухається в обидва боки від поточної позиції

Board(size: Literal[8, 10])
  — valid_cells: set[Cell]                      # всі темні клітинки (32 або 50)
  — dark_cells_count: int                       # обчислюється з size
  — ascending_diagonals: list[DiagonalLine]     # ініціалізуються в __init__
  — descending_diagonals: list[DiagonalLine]    # ініціалізуються в __init__

  методи:
  — get_diagonal(cell, direction) -> DiagonalLine | None
      # повертає лінію заданого напрямку для клітинки, або None якщо не існує
  — get_diagonals(cell) -> list[DiagonalLine]
      # повертає 1 або 2 лінії залежно від позиції клітинки
      # кутові клітинки (напр. A1, H8 на головній дорозі) мають лише 1 лінію
      # враховуються тільки лінії з 2+ клітинок

# Board — незмінна геометрія. Ініціалізується один раз як модульні константи:
#   BOARD_8  = Board(size=8)
#   BOARD_10 = Board(size=10)
# RulesFactory повертає відповідну константу. Board є @dataclass(frozen=True).
```

### Рівень 3 — фігури

```
Piece
  — color: Color
  — type: PieceType   # MAN або QUEEN (дамка)
```

### Рівень 4 — ходи і серії захоплень

```
Move
  — from_cell: Cell
  — to_cell: Cell
  — captured: list[Cell]   # порожньо якщо не захоплення; порядок гарантований валідацією
  — is_capture: bool

CaptureChain
  — piece_cell: Cell          # початкова позиція фігури
  — path: list[Cell]          # впорядкована послідовність клітинок куди стрибає
  — captured: list[Cell]      # відповідно впорядковані захоплені фігури

  # Логіка взаємодії бек ↔ фронт:
  # 1. MoveService обчислює всі валідні CaptureChain для фігури
  # 2. Бекенд відправляє фронту list[CaptureChain] — дерево дозволених кліків
  # 3. Фронт показує гравцю лише дозволені клітинки на кожному кроці
  # 4. Фронт збирає послідовність і відправляє на бек
  # 5. Бекенд звіряє отриману послідовність із pre-computed CaptureChain

CaptureInProgress
  — piece_cell: Cell               # поточна позиція фігури після останнього стрибка
  — chain: CaptureChain            # обрана комбінація захоплень
  — completed_steps: int           # скільки стрибків вже зроблено
  — tentatively_captured: list[Cell]
      # захоплені але ще не зняті з дошки (міжнародні правила)
      # потрібно щоб не дозволити захопити одну фігуру двічі

  # Таймер під час серії захоплень:
  # — іде поки гравець обирає наступний стрибок
  # — зупиняється коли з поточної позиції більше немає обов'язкових захоплень
  # MoveService після кожного стрибка:
  #   if get_valid_capture_chains(..., new_cell):
  #       оновити CaptureInProgress, таймер продовжує йти
  #   else:
  #       timer.stop_turn(), pending_capture = None, передати хід

MoveHistory
  — moves: list[Move]
  — методи: push(), pop(), to_json(), from_json()
```

### Рівень 5 — правила (Strategy pattern)

```
BaseRules (абстрактний)
  — board_size: int
  — move_limit_threshold: int      # ліміт ходів без захоплення для нічиєї
  — get_valid_moves(pieces, board, piece_cell) -> list[Move]
  — get_valid_capture_chains(pieces, board, piece_cell) -> list[CaptureChain]
  — is_capture_mandatory(pieces, board, color) -> bool
  — should_promote(cell, color, board, is_capturing: bool) -> bool
      # is_capturing = game.pending_capture is not None
      # UkrainianRules:    True якщо cell на останньому ряду (незалежно від is_capturing)
      #                    але MoveService зупиняє серію після promotion
      # InternationalRules: False якщо is_capturing=True; True тільки після серії
  — queen_move_range() -> int      # 1 для бразильських, необмежено для інших

UkrainianRules(BaseRules)
  — board_size = 8
  — queen_move_range = необмежено
  — захоплення обов'язкове

BrazilianRules(BaseRules)
  — board_size = 8
  — queen_move_range = 1
  — захоплення обов'язкове

InternationalRules(BaseRules)
  — board_size = 10
  — queen_move_range = необмежено
  — захоплення обов'язкове
```

### Рівень 6 — таймер

```
TimerType: enum
  — MOVE        # фіксований час на кожен хід, скидається на початку ходу
  — GAME_CLOCK  # загальний бюджет часу гравця на всю гру (як у шахах)

TimerConfig
  — type: TimerType
  — duration_seconds: int
      # MOVE: секунд на один хід
      # GAME_CLOCK: загальний час кожного гравця

PlayerClock
  — color: Color
  — remaining_seconds: float
  — is_running: bool
  — методи:
      live_remaining(now: datetime) -> float
          # реальний залишок з урахуванням поточного відліку
          # якщо is_running: remaining_seconds - elapsed; інакше: remaining_seconds

GameTimer
  — config: TimerConfig
  — clocks: dict[Color, PlayerClock]
  — move_deadline: datetime | None   # тільки для MOVE
  — методи:
      start_turn(color)              # запускає годинник гравця;
                                     # для MOVE-типу скидає remaining_seconds до duration_seconds
      stop_turn(color)               # зупиняє, фіксує витрачений час
      is_expired(color, now: datetime) -> bool
                                     # використовує live_remaining(now) — точний live-розрахунок

# GameTimer серіалізується в Redis разом з грою — час не скидається після розриву
```

### Рівень 7 — нічия

```
DrawReason: enum
  — AGREEMENT    # обидва гравці погодились
  — REPETITION   # та сама позиція повторилась 3 рази
  — MOVE_LIMIT   # ліміт ходів без захоплення (коли лишились тільки дамки)

OfferStatus: enum
  — PENDING | ACCEPTED | DECLINED

DrawOffer
  — offered_by: Color
  — offered_at: datetime
  — status: OfferStatus
```

### Рівень 8 — гра

```
GameState: enum
  — WAITING | ACTIVE | PAUSED | FINISHED

Player
  — id: str
  — name: str
  — color: Color
  # connected відсутній — це runtime-стан, живе в GameSession.websocket_connections
  # is_connected(player_id) визначає SessionManager

Game
  — id: str
  — board: Board                         # статична геометрія (BOARD_8 або BOARD_10)
  — rules: BaseRules
  — pieces: dict[Cell, Piece]            # поточне розташування фігур
  — players: dict[Color, Player]
  — current_turn: Color
  — state: GameState
  — history: MoveHistory
  — timer: GameTimer
  — pending_capture: CaptureInProgress | None
  — draw_offer: DrawOffer | None
  — draw_reason: DrawReason | None       # заповнюється при завершенні нічиєю
  — moves_since_capture: int             # скидається до 0 після кожного захоплення
  — position_history: list[str]          # хеші позицій для визначення REPETITION
  — winner: Color | None                 # None + FINISHED = нічия
  — created_at: datetime
  — updated_at: datetime
```

### Рівень 9 — онлайн-сесія і Redis-відновлення

```
GameSession
  — session_id: str
  — game: Game
  — websocket_connections: dict[str, WebSocket]   # ключ: player_id
  — last_heartbeat: dict[str, datetime]           # ключ: player_id

  методи:
  — is_connected(player_id: str) -> bool
      # return player_id in websocket_connections

RedisGameSnapshot
  — game_id: str
  — snapshot: dict        # повна серіалізація Game включно з GameTimer
  — saved_at: datetime
  — ttl: int              # секунди, за замовчуванням 86400 (24 год)
```

---

## Сервіси / Контролери

| Сервіс | Відповідальність |
|---|---|
| `RulesFactory` | повертає екземпляр правил + відповідну Board константу (`BOARD_8` / `BOARD_10`) |
| `BoardService` | розставляє початкові фігури згідно правил |
| `MoveService` | валідує хід, виконує захоплення, серії захоплень, просування в дамки, керує `CaptureInProgress` |
| `GameService` | старт гри, хід, зміна черги, визначення переможця, нічия, завершення; `expire_by_timeout(game, color, now)` — завершує гру програшем; `apply_move` перевіряє `is_expired` перед обробкою ходу |
| `GameSerializer` | `to_dict(game) -> dict`, `from_dict(data) -> Game` — для Redis |
| `RedisGameStore` | `save(game)`, `load(game_id) -> Game`, `delete(game_id)`, `exists(game_id) -> bool` |
| `SessionManager` | WebSocket-з'єднання, heartbeat, `is_connected()`, відновлення після розриву |
| `LobbyService` | створення кімнат, матчмейкінг, список доступних ігор |

---

## Redis — стратегія збереження

### Ключі

```
game:{game_id}           — серіалізована гра (JSON) включно з таймером, TTL 24 год
session:{session_id}     — прив'язка session → game_id, TTL 1 год
player:{player_id}:game  — поточна game_id гравця, TTL 24 год
```

### Логіка відновлення після розриву

1. Клієнт розриває WebSocket → `SessionManager` видаляє з `websocket_connections`
2. `GameService` переводить гру в `GameState.PAUSED` (якщо обидва офлайн) або продовжує таймер
3. `RedisGameStore.save(game)` — знімок зберігається при кожному ході та при паузі
4. Клієнт повертається → надсилає `{type: "reconnect", session_id: "..."}`
5. `SessionManager` знаходить `game_id` за `session:{session_id}` у Redis
6. `RedisGameStore.load(game_id)` → відновлює стан включно з таймером
7. Сервер надсилає клієнту повний стан гри (`game_snapshot`) і продовжує

# Клієнтський рівень відновлення (localStorage):
# — Фронт зберігає sessionId у localStorage: hard refresh не очищає sessionId
# — При hard refresh `onUnmounted` не спрацьовує → sessionId залишається → крок 4 виконується автоматично
# — При навігації (кнопка / back button) `onUnmounted` спрацьовує → session.reset() → sessionId = null → reconnect не відбувається
# — playerName зберігається в localStorage і не скидається між іграми

### Що серіалізується (GameSerializer)

- розмір дошки, тип правил
- позиції всіх фігур з типом (MAN / QUEEN) і кольором
- поточна черга ходу, стан гри
- `GameTimer` з залишками часу кожного гравця
- `CaptureInProgress` якщо гравець посеред серії захоплень
- `DrawOffer` якщо є активна пропозиція нічиєї
- `moves_since_capture`, `position_history`
- повна історія ходів
- id гравців і їх кольори

---

## Стек

- **Бекенд:** Python, FastAPI, WebSockets
- **Redis:** `aioredis`
- **Фронтенд:** Vue.js 3, Composition API
- **Серіалізація:** Pydantic моделі → JSON → Redis

---

## Правила перевірки коду (чекліст)

- [ ] `Cell` реалізовано як `@dataclass(frozen=True)`
- [ ] `Board` реалізовано як `@dataclass(frozen=True)`, існує як модульна константа (`BOARD_8`, `BOARD_10`)
- [ ] Розмір дошки відповідає обраним правилам (8×8 або 10×10)
- [ ] Шашки ходять лише вперед, дамки — відповідно до правил
- [ ] Захоплення обов'язкове при наявності
- [ ] Захоплення може йти назад, звичайний хід шашки — ні
- [ ] Довгий хід дамки тільки в Ukrainian / International rules
- [ ] `get_diagonals(cell)` повертає 1 або 2 лінії (не завжди 2)
- [ ] `DiagonalLine.cells` завжди впорядковані по зростанню row
- [ ] Напрямок обходу діагоналі визначає `MoveService` за кольором фігури
- [ ] Діагональні лінії ініціалізовані в `Board.__init__`
- [ ] `should_promote` отримує `is_capturing: bool`; InternationalRules повертає False під час серії
- [ ] Таймер зупиняється тільки після перевірки що обов'язкових захоплень більше немає
- [ ] `tentatively_captured` перевіряється щоб не захопити одну фігуру двічі
- [ ] `Player` не містить `connected` — стан з'єднання в `SessionManager`
- [ ] `GameTimer` серіалізується в Redis — час не скидається після розриву
- [ ] `is_expired(color, now)` приймає `now: datetime` і рахує через `live_remaining` — не покладається на кешоване `remaining_seconds`
- [ ] `start_turn` для MOVE-типу скидає `remaining_seconds` до `duration_seconds` перед запуском
- [ ] `apply_move` перевіряє `is_expired` до обробки ходу; якщо True — викликає `expire_by_timeout` і повертає без ходу
- [ ] `expire_by_timeout` встановлює `winner` на суперника і переводить гру у `FINISHED`
- [ ] `position_history` зберігає хеші (не повні стани)
- [ ] `winner: None` + `state: FINISHED` = нічия
- [ ] При кожному ході зберігається знімок у Redis
- [ ] TTL встановлено для всіх Redis-ключів
