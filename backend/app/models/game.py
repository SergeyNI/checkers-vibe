from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from .board import Board
from .cell import Cell
from .move import CaptureInProgress, MoveHistory
from .piece import Color, Piece
from .timer import GameTimer


class GameState(Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    PAUSED = "paused"
    FINISHED = "finished"


class DrawReason(Enum):
    AGREEMENT = "agreement"
    REPETITION = "repetition"
    MOVE_LIMIT = "move_limit"


class OfferStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


@dataclass
class DrawOffer:
    offered_by: Color
    offered_at: datetime
    status: OfferStatus = OfferStatus.PENDING


@dataclass
class Player:
    id: str
    name: str
    color: Color


@dataclass
class Game:
    id: str
    board: Board
    rules: object                              # BaseRules — уникаємо циклічного імпорту
    pieces: dict[Cell, Piece]
    players: dict[Color, Player]
    current_turn: Color
    state: GameState
    history: MoveHistory
    timer: GameTimer
    pending_capture: CaptureInProgress | None = None
    draw_offer: DrawOffer | None = None
    draw_reason: DrawReason | None = None
    moves_since_capture: int = 0
    position_history: list[str] = field(default_factory=list)
    winner: Color | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def position_hash(self) -> str:
        state = {
            f"{c.row},{c.col}": f"{p.color.value},{p.type.value}"
            for c, p in sorted(self.pieces.items(), key=lambda x: (x[0].row, x[0].col))
        }
        state["turn"] = self.current_turn.value
        raw = json.dumps(state, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()
