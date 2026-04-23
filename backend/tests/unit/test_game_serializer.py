from datetime import datetime

import pytest

from app.models import Cell, Color, Piece, PieceType
from app.models.game import DrawOffer, DrawReason, GameState, OfferStatus, Player
from app.models.move import CaptureChain, CaptureInProgress
from app.models.timer import TimerConfig, TimerType
from app.services.game_serializer import GameSerializer
from app.services.game_service import create_game, start_game

NOW = datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def sample_game():
    p1 = Player("p1", "Alice", Color.WHITE)
    p2 = Player("p2", "Bob", Color.BLACK)
    config = TimerConfig(TimerType.MOVE, 60)
    g = create_game("g1", p1, p2, "ukrainian", config)
    start_game(g, NOW)
    return g


def _roundtrip(game):
    return GameSerializer.from_dict(GameSerializer.to_dict(game))


# --- основні поля ---

def test_roundtrip_id(sample_game):
    assert _roundtrip(sample_game).id == sample_game.id


def test_roundtrip_rules_name(sample_game):
    restored = _roundtrip(sample_game)
    assert restored.rules.name == "ukrainian"


def test_roundtrip_board_size(sample_game):
    assert _roundtrip(sample_game).board.size == 8


def test_roundtrip_current_turn(sample_game):
    assert _roundtrip(sample_game).current_turn == Color.WHITE


def test_roundtrip_state(sample_game):
    assert _roundtrip(sample_game).state == GameState.ACTIVE


def test_roundtrip_winner_none(sample_game):
    assert _roundtrip(sample_game).winner is None


def test_roundtrip_draw_reason_none(sample_game):
    assert _roundtrip(sample_game).draw_reason is None


# --- фігури ---

def test_roundtrip_pieces_count(sample_game):
    restored = _roundtrip(sample_game)
    assert len(restored.pieces) == len(sample_game.pieces)


def test_roundtrip_pieces_positions(sample_game):
    restored = _roundtrip(sample_game)
    assert set(restored.pieces.keys()) == set(sample_game.pieces.keys())


def test_roundtrip_piece_color_and_type(sample_game):
    restored = _roundtrip(sample_game)
    for cell, piece in sample_game.pieces.items():
        assert restored.pieces[cell].color == piece.color
        assert restored.pieces[cell].type == piece.type


# --- гравці ---

def test_roundtrip_players(sample_game):
    restored = _roundtrip(sample_game)
    assert restored.players[Color.WHITE].id == "p1"
    assert restored.players[Color.BLACK].name == "Bob"


# --- таймер ---

def test_roundtrip_timer_config(sample_game):
    restored = _roundtrip(sample_game)
    assert restored.timer.config.type == TimerType.MOVE
    assert restored.timer.config.duration_seconds == 60


def test_roundtrip_timer_remaining_seconds(sample_game):
    restored = _roundtrip(sample_game)
    assert restored.timer.clocks[Color.WHITE].remaining_seconds == pytest.approx(60.0)
    assert restored.timer.clocks[Color.BLACK].remaining_seconds == pytest.approx(60.0)


def test_roundtrip_timer_running_state(sample_game):
    restored = _roundtrip(sample_game)
    # Білий гравець зараз ходить — годинник запущено
    assert restored.timer.clocks[Color.WHITE].is_running is True
    assert restored.timer.clocks[Color.BLACK].is_running is False


# --- position_history ---

def test_roundtrip_position_history(sample_game):
    restored = _roundtrip(sample_game)
    assert restored.position_history == sample_game.position_history


def test_roundtrip_moves_since_capture(sample_game):
    sample_game.moves_since_capture = 5
    assert _roundtrip(sample_game).moves_since_capture == 5


# --- pending_capture ---

def test_roundtrip_pending_capture_none(sample_game):
    assert _roundtrip(sample_game).pending_capture is None


def test_roundtrip_pending_capture(sample_game):
    chain = CaptureChain(Cell(2, 2), [Cell(4, 4)], [Cell(3, 3)])
    sample_game.pending_capture = CaptureInProgress(
        piece_cell=Cell(4, 4),
        chain=chain,
        completed_steps=1,
        tentatively_captured=[Cell(3, 3)],
    )
    restored = _roundtrip(sample_game)
    pc = restored.pending_capture
    assert pc is not None
    assert pc.piece_cell == Cell(4, 4)
    assert pc.completed_steps == 1
    assert pc.tentatively_captured == [Cell(3, 3)]
    assert pc.chain.path == [Cell(4, 4)]
    assert pc.chain.captured == [Cell(3, 3)]


# --- draw_offer ---

def test_roundtrip_draw_offer(sample_game):
    sample_game.draw_offer = DrawOffer(Color.WHITE, NOW, OfferStatus.PENDING)
    restored = _roundtrip(sample_game)
    assert restored.draw_offer.offered_by == Color.WHITE
    assert restored.draw_offer.status == OfferStatus.PENDING


# --- winner / draw_reason ---

def test_roundtrip_winner(sample_game):
    sample_game.winner = Color.WHITE
    assert _roundtrip(sample_game).winner == Color.WHITE


def test_roundtrip_draw_reason(sample_game):
    sample_game.draw_reason = DrawReason.REPETITION
    assert _roundtrip(sample_game).draw_reason == DrawReason.REPETITION


# --- international rules ---

def test_roundtrip_international_rules():
    p1 = Player("p1", "Alice", Color.WHITE)
    p2 = Player("p2", "Bob", Color.BLACK)
    config = TimerConfig(TimerType.GAME_CLOCK, 300)
    g = create_game("g2", p1, p2, "international", config)
    start_game(g, NOW)
    restored = _roundtrip(g)
    assert restored.rules.name == "international"
    assert restored.board.size == 10
    assert len(restored.pieces) == 40  # 20 + 20
