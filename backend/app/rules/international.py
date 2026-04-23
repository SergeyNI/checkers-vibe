from ..models import Board, Cell, Color
from .base import UNLIMITED, BaseRules


class InternationalRules(BaseRules):
    name = "international"
    board_size = 10
    move_limit_threshold = 25

    def queen_move_range(self) -> int:
        return UNLIMITED

    def should_promote(self, cell: Cell, color: Color, board: Board, is_capturing: bool) -> bool:
        # Фігура не отримує promotion під час серії захоплень
        if is_capturing:
            return False
        return cell.row == self._promotion_row(color, board)
