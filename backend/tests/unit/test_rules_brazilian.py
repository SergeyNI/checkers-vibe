import pytest

from app.models import BOARD_8, Cell, Color, Piece, PieceType
from app.rules import BrazilianRules


@pytest.fixture
def rules():
    return BrazilianRules()


@pytest.fixture
def board():
    return BOARD_8


def test_queen_moves_only_one_cell(rules, board):
    pieces = {Cell(0, 0): Piece(Color.WHITE, PieceType.QUEEN)}
    moves = rules.get_valid_moves(pieces, board, Cell(0, 0))
    targets = {m.to_cell for m in moves}
    # Дамка може йти лише на 1 клітинку
    assert Cell(1, 1) in targets
    assert Cell(2, 2) not in targets
    assert Cell(7, 7) not in targets


def test_queen_capture_one_step(rules, board):
    pieces = {
        Cell(0, 0): Piece(Color.WHITE, PieceType.QUEEN),
        Cell(1, 1): Piece(Color.BLACK, PieceType.MAN),
    }
    chains = rules.get_valid_capture_chains(pieces, board, Cell(0, 0))
    assert len(chains) == 1
    assert chains[0].path == [Cell(2, 2)]


def test_queen_cannot_land_far_after_capture(rules, board):
    pieces = {
        Cell(0, 0): Piece(Color.WHITE, PieceType.QUEEN),
        Cell(1, 1): Piece(Color.BLACK, PieceType.MAN),
    }
    chains = rules.get_valid_capture_chains(pieces, board, Cell(0, 0))
    # Може приземлитись лише на (2,2), не на (3,3) або далі
    landing_cells = {c.path[0] for c in chains}
    assert landing_cells == {Cell(2, 2)}


def test_man_moves_same_as_ukrainian(rules, board):
    pieces = {Cell(2, 2): Piece(Color.WHITE, PieceType.MAN)}
    moves = rules.get_valid_moves(pieces, board, Cell(2, 2))
    targets = {m.to_cell for m in moves}
    assert Cell(3, 1) in targets
    assert Cell(3, 3) in targets
    assert Cell(1, 1) not in targets


def test_promotion_on_last_row_during_capture(rules, board):
    # Brazilian: promotion відбувається навіть під час захоплення
    assert rules.should_promote(Cell(7, 1), Color.WHITE, board, is_capturing=True) is True


def test_board_size_is_8(rules):
    assert rules.board_size == 8
