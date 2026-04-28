"""
Integration tests для RedisGameStore.
Запускаються тільки якщо Redis доступний (REDIS_URL або localhost:6379).
"""
import os
from datetime import datetime

import pytest
import pytest_asyncio

from app.models import Cell, Color, Piece, PieceType
from app.models.game import Player
from app.models.timer import TimerConfig, TimerType
from app.services.game_service import apply_move, create_game, start_game
from app.services.redis_store import RedisGameStore

NOW = datetime(2024, 1, 1, 12, 0, 0)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")  # DB 1 для тестів


@pytest_asyncio.fixture
async def store():
    s = RedisGameStore(redis_url=REDIS_URL, ttl=60)
    try:
        await s._redis.ping()
    except Exception:
        pytest.skip("Redis not available")
    yield s
    await s._redis.flushdb()
    await s.close()


@pytest_asyncio.fixture
async def saved_game(store):
    p1 = Player("p1", "Alice", Color.WHITE)
    p2 = Player("p2", "Bob", Color.BLACK)
    config = TimerConfig(TimerType.MOVE, 60)
    g = create_game("g-test", p1, p2, "ukrainian", config)
    start_game(g, NOW)
    await store.save(g)
    return g


# --- save / load ---

async def test_save_and_load(store, saved_game):
    loaded = await store.load(saved_game.id)
    assert loaded is not None
    assert loaded.id == saved_game.id


async def test_load_restores_pieces(store, saved_game):
    loaded = await store.load(saved_game.id)
    assert len(loaded.pieces) == len(saved_game.pieces)
    assert set(loaded.pieces.keys()) == set(saved_game.pieces.keys())


async def test_load_restores_rules(store, saved_game):
    loaded = await store.load(saved_game.id)
    assert loaded.rules.name == "ukrainian"


async def test_load_restores_timer_remaining(store, saved_game):
    loaded = await store.load(saved_game.id)
    assert loaded.timer.clocks[Color.WHITE].remaining_seconds == pytest.approx(60.0)


async def test_load_returns_none_for_missing_game(store):
    assert await store.load("nonexistent") is None


async def test_exists_true(store, saved_game):
    assert await store.exists(saved_game.id) is True


async def test_exists_false(store):
    assert await store.exists("nonexistent") is False


async def test_delete(store, saved_game):
    await store.delete(saved_game.id)
    assert await store.exists(saved_game.id) is False


# --- відновлення після ходу ---

async def test_load_restores_move_history(store):
    p1 = Player("p1", "Alice", Color.WHITE)
    p2 = Player("p2", "Bob", Color.BLACK)
    config = TimerConfig(TimerType.MOVE, 60)
    g = create_game("g-hist", p1, p2, "ukrainian", config)
    g.pieces = {
        Cell(2, 2): Piece(Color.WHITE, PieceType.MAN),
        Cell(5, 5): Piece(Color.BLACK, PieceType.MAN),
    }
    start_game(g, NOW)
    apply_move(g, "p1", Cell(2, 2), Cell(3, 3), NOW)
    await store.save(g)

    loaded = await store.load("g-hist")
    assert len(loaded.history.moves) == 1
    assert loaded.history.moves[0].from_cell == Cell(2, 2)


async def test_load_restores_pending_capture(store):
    from app.models.move import CaptureChain, CaptureInProgress

    p1 = Player("p1", "Alice", Color.WHITE)
    p2 = Player("p2", "Bob", Color.BLACK)
    config = TimerConfig(TimerType.MOVE, 60)
    g = create_game("g-cap", p1, p2, "ukrainian", config)
    g.pieces = {
        Cell(0, 0): Piece(Color.WHITE, PieceType.MAN),
        Cell(1, 1): Piece(Color.BLACK, PieceType.MAN),
        Cell(3, 3): Piece(Color.BLACK, PieceType.MAN),
    }
    start_game(g, NOW)
    apply_move(g, "p1", Cell(0, 0), Cell(2, 2), NOW)  # перший стрибок → pending
    await store.save(g)

    loaded = await store.load("g-cap")
    assert loaded.pending_capture is not None
    assert loaded.pending_capture.piece_cell == Cell(2, 2)


# --- session / player keys ---

async def test_session_save_and_get(store):
    data = {"player_id": "p-1", "game_id": "game-1"}
    await store.save_session_data("sess-1", data)
    assert await store.get_session_data("sess-1") == data


async def test_player_game_save_and_get(store):
    await store.save_player_game("player-1", "game-1")
    assert await store.get_player_game("player-1") == "game-1"
