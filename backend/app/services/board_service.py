from ..models import Board, Cell, Color, Piece, PieceType


def initial_pieces(board: Board) -> dict[Cell, Piece]:
    rows_per_side = 3 if board.size == 8 else 4
    gap = board.size - 2 * rows_per_side  # порожні рядки в середині

    white_rows = set(range(rows_per_side))
    black_rows = set(range(rows_per_side + gap, board.size))

    pieces: dict[Cell, Piece] = {}
    for cell in board.valid_cells:
        if cell.row in white_rows:
            pieces[cell] = Piece(Color.WHITE, PieceType.MAN)
        elif cell.row in black_rows:
            pieces[cell] = Piece(Color.BLACK, PieceType.MAN)
    return pieces
