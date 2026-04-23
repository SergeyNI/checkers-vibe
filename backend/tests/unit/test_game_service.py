import pytest
from datetime import datetime

from app.models import Color, Cell, Piece, PieceType
from app.models.game import DrawReason, Game, GameState, Player
from app.models.timer import TimerConfig, TimerType
from app.services.game_service import (
    GameError,
    apply_move,
    create_game,
    offer_draw,
    resign,
    respond_draw,
    start_game,
)


NOW = datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def timer_config():
    return TimerConfig(type=TimerType.MOVE, duration_seconds=60)


@pytest.fixture
def players():
    return (
        Player(id="p1", name="Alice", color=Color.WHITE),
        Player(id="p2", name="Bob", color=Color.BLACK),
    )


@pytest.fixture
def game(players, timer_config):
    p1, p2 = players
    g = create_game("g1", p1, p2, "ukrainian", timer_config)
    start_game(g, NOW)
    return g


# --- create / start ---

def test_game_starts_in_active_state(game):
    assert game.state == GameState.ACTIVE


def test_game_initial_turn_is_white(game):
    assert game.current_turn == Color.WHITE


def test_game_initial_pieces_count_8x8(game):
    white = sum(1 for p in game.pieces.values() if p.color == Color.WHITE)
    black = sum(1 for p in game.pieces.values() if p.color == Color.BLACK)
    assert white == 12
    assert black == 12


def test_game_cannot_start_twice(game):
    with pytest.raises(GameError):
        start_game(game, NOW)


# --- regular move ---

def test_white_can_make_valid_move(game):
    # Знаходимо шашку білих що може ходити
    from app.rules import UkrainianRules
    rules = UkrainianRules()
    from_cell = next(
        cell for cell, piece in game.pieces.items()
        if piece.color == Color.WHITE and rules.get_valid_moves(game.pieces, game.board, cell)
    )
    to_cell = rules.get_valid_moves(game.pieces, game.board, from_cell)[0].to_cell
    apply_move(game, "p1", from_cell, to_cell, NOW)
    assert game.pieces.get(from_cell) is None
    assert game.pieces.get(to_cell) is not None


def test_turn_switches_after_move(game):
    from app.rules import UkrainianRules
    rules = UkrainianRules()
    from_cell = next(
        cell for cell, piece in game.pieces.items()
        if piece.color == Color.WHITE and rules.get_valid_moves(game.pieces, game.board, cell)
    )
    to_cell = rules.get_valid_moves(game.pieces, game.board, from_cell)[0].to_cell
    apply_move(game, "p1", from_cell, to_cell, NOW)
    assert game.current_turn == Color.BLACK


def test_wrong_player_raises(game):
    from app.rules import UkrainianRules
    rules = UkrainianRules()
    from_cell = next(
        cell for cell, piece in game.pieces.items()
        if piece.color == Color.WHITE and rules.get_valid_moves(game.pieces, game.board, cell)
    )
    to_cell = rules.get_valid_moves(game.pieces, game.board, from_cell)[0].to_cell
    with pytest.raises(GameError):
        apply_move(game, "p2", from_cell, to_cell, NOW)  # Bob's turn is black


def test_invalid_move_raises(game):
    with pytest.raises(GameError):
        apply_move(game, "p1", Cell(2, 0), Cell(5, 5), NOW)


# --- capture ---

def test_capture_removes_opponent_piece(players, timer_config):
    p1, p2 = players
    g = create_game("g2", p1, p2, "ukrainian", timer_config)
    g.pieces = {
        Cell(2, 2): Piece(Color.WHITE, PieceType.MAN),
        Cell(3, 3): Piece(Color.BLACK, PieceType.MAN),
    }
    start_game(g, NOW)
    apply_move(g, "p1", Cell(2, 2), Cell(4, 4), NOW)
    assert Cell(3, 3) not in g.pieces
    assert Cell(4, 4) in g.pieces


def test_capture_recorded_in_history(players, timer_config):
    p1, p2 = players
    g = create_game("g3", p1, p2, "ukrainian", timer_config)
    g.pieces = {
        Cell(2, 2): Piece(Color.WHITE, PieceType.MAN),
        Cell(3, 3): Piece(Color.BLACK, PieceType.MAN),
    }
    start_game(g, NOW)
    apply_move(g, "p1", Cell(2, 2), Cell(4, 4), NOW)
    assert len(g.history.moves) == 1
    assert g.history.moves[0].is_capture


# --- promotion ---

def test_man_promotes_on_last_row(players, timer_config):
    p1, p2 = players
    g = create_game("g4", p1, p2, "ukrainian", timer_config)
    g.pieces = {Cell(6, 0): Piece(Color.WHITE, PieceType.MAN)}
    start_game(g, NOW)
    apply_move(g, "p1", Cell(6, 0), Cell(7, 1), NOW)
    assert g.pieces[Cell(7, 1)].type == PieceType.QUEEN


# --- win condition ---

def test_win_when_opponent_has_no_pieces(players, timer_config):
    p1, p2 = players
    g = create_game("g5", p1, p2, "ukrainian", timer_config)
    g.pieces = {
        Cell(2, 2): Piece(Color.WHITE, PieceType.MAN),
        Cell(3, 3): Piece(Color.BLACK, PieceType.MAN),
    }
    start_game(g, NOW)
    apply_move(g, "p1", Cell(2, 2), Cell(4, 4), NOW)
    assert g.state == GameState.FINISHED
    assert g.winner == Color.WHITE


# --- draw ---

def test_draw_by_agreement(game):
    offer_draw(game, "p1")
    respond_draw(game, "p2", accepted=True, now=NOW)
    assert game.state == GameState.FINISHED
    assert game.winner is None
    assert game.draw_reason == DrawReason.AGREEMENT


def test_draw_offer_declined(game):
    offer_draw(game, "p1")
    respond_draw(game, "p2", accepted=False)
    assert game.state == GameState.ACTIVE


def test_cannot_respond_to_own_draw_offer(game):
    offer_draw(game, "p1")
    with pytest.raises(GameError):
        respond_draw(game, "p1", accepted=True)


def test_draw_by_move_limit(players, timer_config):
    p1, p2 = players
    g = create_game("g6", p1, p2, "ukrainian", timer_config)
    g.pieces = {
        Cell(0, 0): Piece(Color.WHITE, PieceType.QUEEN),
        Cell(7, 7): Piece(Color.BLACK, PieceType.QUEEN),
    }
    start_game(g, NOW)
    # Форсуємо лічильник до порогу - 1
    g.moves_since_capture = g.rules.move_limit_threshold - 1
    # Один хід без захоплення → нічия
    apply_move(g, "p1", Cell(0, 0), Cell(1, 1), NOW)
    assert g.state == GameState.FINISHED
    assert g.draw_reason == DrawReason.MOVE_LIMIT


# --- resign ---

def test_resign_ends_game(game):
    resign(game, "p1", NOW)
    assert game.state == GameState.FINISHED
    assert game.winner == Color.BLACK


def test_resign_on_finished_game_raises(game):
    resign(game, "p1", NOW)
    with pytest.raises(GameError):
        resign(game, "p2", NOW)
