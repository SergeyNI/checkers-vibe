from dataclasses import dataclass, field
from typing import Literal

from .cell import Cell
from .diagonal import DiagonalDirection, DiagonalLine


@dataclass
class Board:
    size: Literal[8, 10]
    valid_cells: frozenset[Cell] = field(init=False, repr=False)
    dark_cells_count: int = field(init=False)
    ascending_diagonals: list[DiagonalLine] = field(init=False, repr=False)
    descending_diagonals: list[DiagonalLine] = field(init=False, repr=False)
    _asc_index: dict[Cell, DiagonalLine] = field(init=False, repr=False)
    _desc_index: dict[Cell, DiagonalLine] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.valid_cells = frozenset(
            Cell(row, col)
            for row in range(self.size)
            for col in range(self.size)
            if (row + col) % 2 == 0
        )
        self.dark_cells_count = len(self.valid_cells)
        self.ascending_diagonals, self.descending_diagonals = self._compute_diagonals()
        self._asc_index = {cell: diag for diag in self.ascending_diagonals for cell in diag.cells}
        self._desc_index = {cell: diag for diag in self.descending_diagonals for cell in diag.cells}

    def _compute_diagonals(self) -> tuple[list[DiagonalLine], list[DiagonalLine]]:
        asc_groups: dict[int, list[Cell]] = {}
        desc_groups: dict[int, list[Cell]] = {}

        for cell in self.valid_cells:
            asc_groups.setdefault(cell.row - cell.col, []).append(cell)
            desc_groups.setdefault(cell.row + cell.col, []).append(cell)

        ascending = [
            DiagonalLine(
                cells=sorted(cells, key=lambda c: c.row),
                direction=DiagonalDirection.ASCENDING,
                name="main_road" if key == 0 else None,
            )
            for key, cells in sorted(asc_groups.items())
            if len(cells) >= 2
        ]

        descending = [
            DiagonalLine(
                cells=sorted(cells, key=lambda c: c.row),
                direction=DiagonalDirection.DESCENDING,
            )
            for key, cells in sorted(desc_groups.items())
            if len(cells) >= 2
        ]

        return ascending, descending

    def get_diagonal(self, cell: Cell, direction: DiagonalDirection) -> DiagonalLine | None:
        if direction == DiagonalDirection.ASCENDING:
            return self._asc_index.get(cell)
        return self._desc_index.get(cell)

    def get_diagonals(self, cell: Cell) -> list[DiagonalLine]:
        result = []
        if cell in self._asc_index:
            result.append(self._asc_index[cell])
        if cell in self._desc_index:
            result.append(self._desc_index[cell])
        return result


BOARD_8 = Board(size=8)
BOARD_10 = Board(size=10)
