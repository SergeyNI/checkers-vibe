from ..models import Board, Cell, Color
from .base import BaseRules


class BrazilianRules(BaseRules):
    name = "brazilian"
    board_size = 8
    move_limit_threshold = 15

    def queen_move_range(self) -> int:
        return 1

    def should_promote(self, cell: Cell, color: Color, board: Board, is_capturing: bool) -> bool:
        return cell.row == self._promotion_row(color, board)
