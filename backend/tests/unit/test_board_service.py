from app.models import BOARD_8, BOARD_10, Color
from app.services.board_service import initial_pieces


def test_initial_pieces_8x8_white_count():
    pieces = initial_pieces(BOARD_8)
    assert sum(1 for p in pieces.values() if p.color == Color.WHITE) == 12


def test_initial_pieces_8x8_black_count():
    pieces = initial_pieces(BOARD_8)
    assert sum(1 for p in pieces.values() if p.color == Color.BLACK) == 12


def test_initial_pieces_10x10_white_count():
    pieces = initial_pieces(BOARD_10)
    assert sum(1 for p in pieces.values() if p.color == Color.WHITE) == 20


def test_initial_pieces_10x10_black_count():
    pieces = initial_pieces(BOARD_10)
    assert sum(1 for p in pieces.values() if p.color == Color.BLACK) == 20


def test_initial_pieces_all_on_valid_cells():
    for board in (BOARD_8, BOARD_10):
        pieces = initial_pieces(board)
        for cell in pieces:
            assert cell in board.valid_cells


def test_initial_pieces_middle_rows_empty_8x8():
    pieces = initial_pieces(BOARD_8)
    from app.models import Cell
    for col in range(8):
        assert Cell(3, col) not in pieces
        assert Cell(4, col) not in pieces


def test_initial_pieces_white_on_bottom_rows_8x8():
    pieces = initial_pieces(BOARD_8)
    for cell, piece in pieces.items():
        if piece.color == Color.WHITE:
            assert cell.row in (0, 1, 2)


def test_initial_pieces_black_on_top_rows_8x8():
    pieces = initial_pieces(BOARD_8)
    for cell, piece in pieces.items():
        if piece.color == Color.BLACK:
            assert cell.row in (5, 6, 7)
