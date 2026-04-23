from dataclasses import dataclass, field
from typing import ClassVar

from .cell import Cell


@dataclass(frozen=True)
class Move:
    from_cell: Cell
    to_cell: Cell
    captured: tuple[Cell, ...] = field(default_factory=tuple)

    @property
    def is_capture(self) -> bool:
        return len(self.captured) > 0


@dataclass
class CaptureChain:
    piece_cell: Cell
    path: list[Cell]      # впорядкована послідовність клітинок куди стрибає
    captured: list[Cell]  # відповідно впорядковані захоплені фігури

    def __post_init__(self) -> None:
        if len(self.path) != len(self.captured):
            raise ValueError(
                f"path and captured must have equal length, "
                f"got path={len(self.path)}, captured={len(self.captured)}"
            )


@dataclass
class CaptureInProgress:
    piece_cell: Cell                      # поточна позиція після останнього стрибка
    chain: CaptureChain                   # обрана комбінація захоплень
    completed_steps: int                  # скільки стрибків вже зроблено
    tentatively_captured: list[Cell]      # захоплені але ще не зняті (міжнародні правила)


@dataclass
class MoveHistory:
    moves: list[Move] = field(default_factory=list)

    def push(self, move: Move) -> None:
        self.moves.append(move)

    def pop(self) -> Move:
        if not self.moves:
            raise IndexError("history is empty")
        return self.moves.pop()

    def to_json(self) -> list[dict]:
        return [
            {
                "from_cell": {"row": m.from_cell.row, "col": m.from_cell.col},
                "to_cell": {"row": m.to_cell.row, "col": m.to_cell.col},
                "captured": [{"row": c.row, "col": c.col} for c in m.captured],
            }
            for m in self.moves
        ]

    @classmethod
    def from_json(cls, data: list[dict]) -> "MoveHistory":
        moves = [
            Move(
                from_cell=Cell(**d["from_cell"]),
                to_cell=Cell(**d["to_cell"]),
                captured=tuple(Cell(**c) for c in d["captured"]),
            )
            for d in data
        ]
        return cls(moves=moves)
