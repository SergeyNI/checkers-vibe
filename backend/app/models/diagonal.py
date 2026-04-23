from dataclasses import dataclass, field
from enum import Enum

from .cell import Cell


class DiagonalDirection(Enum):
    ASCENDING = "ascending"    # зліва направо вгору: row-col = const (головна дорога)
    DESCENDING = "descending"  # зліва направо вниз:  row+col = const


@dataclass
class DiagonalLine:
    cells: list[Cell]           # впорядковані по зростанню row
    direction: DiagonalDirection
    name: str | None = field(default=None)
