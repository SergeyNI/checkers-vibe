import pytest

from app.models import BOARD_10, Cell, Color, Piece, PieceType
from app.rules import InternationalRules


@pytest.fixture
def rules():
    return InternationalRules()


@pytest.fixture
def board():
    return BOARD_10


def test_board_size_is_10(rules):
    assert rules.board_size == 10


def test_queen_moves_unlimited(rules, board):
    pieces = {Cell(0, 0): Piece(Color.WHITE, PieceType.QUEEN)}
    moves = rules.get_valid_moves(pieces, board, Cell(0, 0))
    targets = {m.to_cell for m in moves}
    assert Cell(9, 9) in targets
    assert Cell(5, 5) in targets


def test_no_promotion_during_capture_chain(rules, board):
    # International: фігура не отримує promotion під час серії захоплень
    assert rules.should_promote(Cell(9, 1), Color.WHITE, board, is_capturing=True) is False


def test_promotion_after_capture_chain(rules, board):
    # Але отримує promotion після завершення серії
    assert rules.should_promote(Cell(9, 1), Color.WHITE, board, is_capturing=False) is True


def test_black_promotion_row_is_zero(rules, board):
    assert rules.should_promote(Cell(0, 2), Color.BLACK, board, is_capturing=False) is True
    assert rules.should_promote(Cell(0, 2), Color.BLACK, board, is_capturing=True) is False


def test_capture_chain_no_promotion_interrupt(rules, board):
    # Шашка проходить через останній ряд під час серії — НЕ зупиняється
    pieces = {
        Cell(7, 1): Piece(Color.WHITE, PieceType.MAN),
        Cell(8, 2): Piece(Color.BLACK, PieceType.MAN),  # стрибок виходить на ряд 9 (promotion)
        Cell(8, 0): Piece(Color.BLACK, PieceType.MAN),  # альтернативний стрибок
    }
    chains = rules.get_valid_capture_chains(pieces, board, Cell(7, 1))
    # При is_capturing=True should_promote повертає False — ланцюг не зупиняється
    # Шашка досягає (9,3) але НЕ отримує promotion і НЕ зупиняє серію
    assert all(len(c.path) == 1 for c in chains)  # в цій позиції 1 стрибок (немає продовження)


def test_man_moves_forward_only(rules, board):
    pieces = {Cell(3, 3): Piece(Color.WHITE, PieceType.MAN)}
    moves = rules.get_valid_moves(pieces, board, Cell(3, 3))
    targets = {m.to_cell for m in moves}
    assert Cell(4, 2) in targets
    assert Cell(4, 4) in targets
    assert Cell(2, 2) not in targets


def test_queen_capture_unlimited_landing(rules, board):
    pieces = {
        Cell(0, 0): Piece(Color.WHITE, PieceType.QUEEN),
        Cell(3, 3): Piece(Color.BLACK, PieceType.MAN),
    }
    chains = rules.get_valid_capture_chains(pieces, board, Cell(0, 0))
    landing_cells = {c.path[0] for c in chains}
    assert Cell(4, 4) in landing_cells
    assert Cell(5, 5) in landing_cells
    assert Cell(9, 9) in landing_cells
