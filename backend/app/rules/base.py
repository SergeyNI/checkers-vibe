from abc import ABC, abstractmethod

from ..models import Board, Cell, Color, Piece, PieceType
from ..models.move import CaptureChain, Move

UNLIMITED = 99  # sentinel for unlimited queen move range


class BaseRules(ABC):
    board_size: int
    move_limit_threshold: int

    # --- public API ---

    def get_valid_moves(self, pieces: dict[Cell, Piece], board: Board, piece_cell: Cell) -> list[Move]:
        piece = pieces[piece_cell]
        if piece.type == PieceType.MAN:
            return self._get_man_moves(pieces, board, piece_cell)
        return self._get_queen_moves(pieces, board, piece_cell)

    def get_valid_capture_chains(
        self,
        pieces: dict[Cell, Piece],
        board: Board,
        piece_cell: Cell,
        _tentative: list[Cell] | None = None,
        _start: Cell | None = None,
    ) -> list[CaptureChain]:
        if _tentative is None:
            _tentative = []
        if _start is None:
            _start = piece_cell

        piece = pieces.get(piece_cell)
        if piece is None:
            return []

        immediate = self._get_immediate_captures(pieces, board, piece_cell, piece, _tentative)
        if not immediate:
            return []

        chains = []
        for cap_cell, land_cell in immediate:
            new_tentative = _tentative + [cap_cell]
            new_pieces = {k: v for k, v in pieces.items() if k != piece_cell and k != cap_cell}

            # Ukrainian/Brazilian: promotion stops the chain immediately
            if self.should_promote(land_cell, piece.color, board, is_capturing=True):
                new_pieces[land_cell] = Piece(color=piece.color, type=PieceType.QUEEN)
                chains.append(CaptureChain(_start, [land_cell], [cap_cell]))
                continue

            new_pieces[land_cell] = piece
            sub_chains = self.get_valid_capture_chains(new_pieces, board, land_cell, new_tentative, _start)

            if sub_chains:
                for sub in sub_chains:
                    chains.append(CaptureChain(_start, [land_cell] + sub.path, [cap_cell] + sub.captured))
            else:
                chains.append(CaptureChain(_start, [land_cell], [cap_cell]))

        return chains

    def is_capture_mandatory(self, pieces: dict[Cell, Piece], board: Board, color: Color) -> bool:
        return any(
            self.get_valid_capture_chains(pieces, board, cell)
            for cell, piece in pieces.items()
            if piece.color == color
        )

    @abstractmethod
    def should_promote(self, cell: Cell, color: Color, board: Board, is_capturing: bool) -> bool: ...

    @abstractmethod
    def queen_move_range(self) -> int: ...

    # --- private helpers ---

    def _promotion_row(self, color: Color, board: Board) -> int:
        return board.size - 1 if color == Color.WHITE else 0

    def _get_man_moves(self, pieces: dict[Cell, Piece], board: Board, cell: Cell) -> list[Move]:
        piece = pieces[cell]
        forward = 1 if piece.color == Color.WHITE else -1
        return [
            Move(from_cell=cell, to_cell=Cell(cell.row + forward, cell.col + dcol))
            for dcol in (-1, 1)
            if (target := Cell(cell.row + forward, cell.col + dcol)) in board.valid_cells
            and target not in pieces
        ]

    def _get_queen_moves(self, pieces: dict[Cell, Piece], board: Board, cell: Cell) -> list[Move]:
        moves = []
        for diag in board.get_diagonals(cell):
            idx = diag.cells.index(cell)
            for direction in (diag.cells[idx + 1:], diag.cells[:idx][::-1]):
                for target in direction:
                    if target in pieces:
                        break
                    moves.append(Move(from_cell=cell, to_cell=target))
                    if self.queen_move_range() == 1:
                        break
        return moves

    def _get_immediate_captures(
        self, pieces: dict[Cell, Piece], board: Board, cell: Cell, piece: Piece, tentative: list[Cell]
    ) -> list[tuple[Cell, Cell]]:
        if piece.type == PieceType.MAN or self.queen_move_range() == 1:
            return self._man_style_captures(pieces, board, cell, piece, tentative)
        return self._queen_unlimited_captures(pieces, board, cell, piece, tentative)

    def _man_style_captures(
        self, pieces: dict[Cell, Piece], board: Board, cell: Cell, piece: Piece, tentative: list[Cell]
    ) -> list[tuple[Cell, Cell]]:
        results = []
        for drow in (-1, 1):
            for dcol in (-1, 1):
                over = Cell(cell.row + drow, cell.col + dcol)
                land = Cell(cell.row + 2 * drow, cell.col + 2 * dcol)
                if (
                    over in board.valid_cells
                    and land in board.valid_cells
                    and over in pieces
                    and pieces[over].color != piece.color
                    and over not in tentative
                    and land not in pieces
                ):
                    results.append((over, land))
        return results

    def _queen_unlimited_captures(
        self, pieces: dict[Cell, Piece], board: Board, cell: Cell, piece: Piece, tentative: list[Cell]
    ) -> list[tuple[Cell, Cell]]:
        results = []
        for diag in board.get_diagonals(cell):
            idx = diag.cells.index(cell)
            for direction in (diag.cells[idx + 1:], diag.cells[:idx][::-1]):
                found_opponent: Cell | None = None
                for target in direction:
                    if target in pieces:
                        if (
                            pieces[target].color != piece.color
                            and target not in tentative
                            and found_opponent is None
                        ):
                            found_opponent = target
                        else:
                            break
                    elif found_opponent is not None:
                        results.append((found_opponent, target))
        return results
