from dataclasses import dataclass
from enum import Enum


class Color(Enum):
    WHITE = "white"
    BLACK = "black"


class PieceType(Enum):
    MAN = "man"
    QUEEN = "queen"


@dataclass(frozen=True)
class Piece:
    color: Color
    type: PieceType
