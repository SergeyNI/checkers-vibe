---
name: checkers-tests
description: "Testing manifest for online checkers game. Reference this agent when writing or running tests for backend (pytest) or frontend (Vitest, Playwright). Covers unit, integration, and E2E tests."
applyTo:
  - "**/test_*.py"
  - "**/*_test.py"
  - "**/*.spec.ts"
  - "**/*.test.ts"
  - "**/tests/**/*"
  - "**/e2e/**/*"
---

# Checkers Game — Testing

Бекенд: pytest + pytest-asyncio.
Фронтенд: Vitest + Vue Test Utils.
E2E: Playwright.

---

## Структура тестів

```
checkers-vibe/
├── backend/
│   └── tests/
│       ├── unit/
│       │   ├── test_cell.py
│       │   ├── test_board.py
│       │   ├── test_piece.py
│       │   ├── test_diagonal_line.py
│       │   ├── test_move.py
│       │   ├── test_capture_chain.py
│       │   ├── test_rules_ukrainian.py
│       │   ├── test_rules_brazilian.py
│       │   ├── test_rules_international.py
│       │   ├── test_move_service.py
│       │   ├── test_game_service.py
│       │   └── test_game_timer.py
│       ├── integration/
│       │   ├── test_redis_game_store.py
│       │   └── test_websocket_session.py
│       └── conftest.py
└── frontend/
    └── tests/
        ├── unit/
        │   ├── stores/
        │   │   ├── useGameStore.spec.ts
        │   │   ├── useSessionStore.spec.ts
        │   │   └── useLobbyStore.spec.ts
        │   ├── composables/
        │   │   ├── useWebSocket.spec.ts
        │   │   ├── useCaptureTree.spec.ts
        │   │   └── useTimer.spec.ts
        │   └── components/
        │       ├── Board.spec.ts
        │       ├── Cell.spec.ts
        │       └── GameTimer.spec.ts
        └── e2e/
            ├── lobby.spec.ts
            ├── game-flow.spec.ts
            └── reconnect.spec.ts
```

---

## Бекенд — unit тести

### Cell, Board, DiagonalLine

```python
# test_cell.py
def test_cell_equality():        # Cell(1,2) == Cell(1,2)
def test_cell_hashable():        # використовується як ключ dict
def test_cell_immutable():       # frozen=True, не можна змінити поля

# test_board.py
def test_board_8_dark_cells():   # 32 темні клітинки
def test_board_10_dark_cells():  # 50 темніх клітинок
def test_board_constants():      # BOARD_8 і BOARD_10 є singleton
def test_diagonals_initialized_on_creation()
def test_main_road_exists():     # головна дорога A1→H8
def test_get_diagonals_corner_cell_returns_one()   # кутова клітинка = 1 лінія
def test_get_diagonals_middle_cell_returns_two()   # середня клітинка = 2 лінії
def test_diagonal_cells_ordered_by_ascending_row()
```

### Правила

```python
# test_rules_ukrainian.py
def test_man_moves_forward_only()
def test_man_cannot_move_backward()
def test_queen_moves_unlimited_distance()
def test_capture_is_mandatory()
def test_capture_can_go_backward()
def test_promotion_stops_capture_chain()
def test_promotion_on_last_row()

# test_rules_international.py
def test_10x10_board_size()
def test_queen_moves_unlimited_distance()
def test_no_promotion_during_capture_chain()   # ключова відмінність
def test_captured_pieces_removed_after_chain() # не під час

# test_rules_brazilian.py
def test_queen_moves_one_cell_only()
def test_8x8_board_size()
```

### MoveService

```python
def test_valid_moves_returned_for_man()
def test_valid_moves_returned_for_queen()
def test_capture_chain_computed_correctly()
def test_cannot_capture_same_piece_twice()      # tentatively_captured
def test_timer_stops_after_last_mandatory_capture()
def test_timer_continues_during_capture_chain()
def test_pending_capture_updated_after_each_jump()
def test_move_validated_against_capture_chains()
```

### GameService

```python
def test_game_starts_in_waiting_state()
def test_turn_switches_after_move()
def test_winner_determined_when_no_pieces()
def test_winner_determined_when_no_moves()
def test_draw_by_agreement()
def test_draw_by_repetition()                  # position_history
def test_draw_by_move_limit()                  # moves_since_capture
def test_moves_since_capture_resets_on_capture()
def test_game_paused_when_both_offline()

# GameTimer
def test_move_timer_resets_on_new_turn()
def test_game_clock_decrements_only_active_player()
def test_timer_stops_after_last_capture_in_chain()
def test_expired_timer_ends_game()
```

---

## Бекенд — integration тести

```python
# test_redis_game_store.py
def test_save_and_load_game()
def test_load_restores_pieces_correctly()
def test_load_restores_timer_correctly()        # час не скидається
def test_load_restores_pending_capture()        # серія захоплень відновлюється
def test_ttl_set_on_save()
def test_load_returns_none_for_missing_game()
def test_game_deleted_correctly()

# test_websocket_session.py
@pytest.mark.asyncio
async def test_reconnect_restores_game_state()
async def test_player_marked_disconnected_on_ws_close()
async def test_game_paused_when_both_players_disconnect()
async def test_timer_preserved_after_reconnect()
```

### conftest.py — спільні fixtures

```python
@pytest.fixture
def board_8() -> Board       # BOARD_8 константа
@pytest.fixture
def board_10() -> Board      # BOARD_10 константа
@pytest.fixture
def ukrainian_rules()
@pytest.fixture
def sample_game()            # гра з кількома фігурами для тестів
@pytest.fixture
def redis_client()           # тестовий Redis (окрема DB)
```

---

## Фронтенд — unit тести

```typescript
// useGameStore.spec.ts
it('updates pieces on move_made message')
it('sets pendingCapture on capture start')
it('clears pendingCapture after last capture')
it('sets winner on game_finished message')

// useCaptureTree.spec.ts
it('returns allowed next cells from current position')
it('returns empty array when chain complete')
it('handles multiple branching capture paths')

// useTimer.spec.ts
it('counts down locally between ws updates')
it('syncs with server on game_snapshot')
it('emits expired when time runs out')

// Board.spec.ts
it('renders 32 cells for 8x8 board')
it('renders 50 cells for 10x10 board')
it('highlights valid cells from captureChains')
it('does not highlight cells not in captureChains')
```

---

## E2E тести (Playwright)

```typescript
// game-flow.spec.ts
test('two players complete a full game')
test('capture chain: player must complete all mandatory captures')
test('promotion: man becomes queen on last row')
test('draw offer: player1 offers, player2 accepts')
test('timer expires: game ends with correct winner')

// reconnect.spec.ts
test('player reconnects and game state is restored')
test('timer is preserved after reconnect')
test('pending capture chain is restored after reconnect')
test('game pauses when both players disconnect')

// lobby.spec.ts
test('player creates a room with Ukrainian rules 8x8')
test('second player joins and game starts')
```

---

## Запуск тестів

```bash
# Бекенд — всі тести
docker compose exec backend pytest

# Бекенд — тільки unit
docker compose exec backend pytest tests/unit

# Бекенд — з покриттям
docker compose exec backend pytest --cov=. --cov-report=term-missing

# Фронтенд — unit
docker compose exec frontend npm run test

# Фронтенд — з покриттям
docker compose exec frontend npm run test:coverage

# E2E (потребує запущеного стеку)
docker compose exec frontend npx playwright test
```

---

## Правила написання тестів (чекліст)

- [ ] Кожне правило гри покрите окремим тестом для кожного варіанту (Ukrainian / Brazilian / International)
- [ ] `tentatively_captured` перевіряється — не можна захопити фігуру двічі
- [ ] Promotion під час серії захоплень тестується окремо для Ukrainian і International rules
- [ ] Таймер після reconnect не скидається — є окремий тест
- [ ] `pending_capture` відновлюється з Redis — є окремий integration тест
- [ ] Redis тести використовують окрему тестову базу (DB index 1)
- [ ] WebSocket тести використовують `pytest-asyncio`
- [ ] Фронтенд не тестує логіку валідності ходів — це відповідальність бекенду
