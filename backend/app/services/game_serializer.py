from datetime import datetime

from ..models import BOARD_8, BOARD_10, Cell, Color, Piece, PieceType
from ..models.game import DrawOffer, DrawReason, Game, GameState, OfferStatus, Player
from ..models.move import CaptureChain, CaptureInProgress, MoveHistory
from ..models.timer import GameTimer, PlayerClock, TimerConfig, TimerType
from ..rules import create_rules

_BOARDS = {8: BOARD_8, 10: BOARD_10}


class GameSerializer:

    @staticmethod
    def to_dict(game: Game) -> dict:
        return {
            "id": game.id,
            "board_size": game.board.size,
            "rules_name": game.rules.name,
            "pieces": [
                {"row": c.row, "col": c.col, "color": p.color.value, "type": p.type.value}
                for c, p in game.pieces.items()
            ],
            "players": [
                {"id": pl.id, "name": pl.name, "color": pl.color.value}
                for pl in game.players.values()
            ],
            "current_turn": game.current_turn.value,
            "state": game.state.value,
            "history": game.history.to_json(),
            "timer": _serialize_timer(game.timer),
            "pending_capture": _serialize_pending(game.pending_capture),
            "draw_offer": _serialize_draw_offer(game.draw_offer),
            "draw_reason": game.draw_reason.value if game.draw_reason else None,
            "moves_since_capture": game.moves_since_capture,
            "position_history": game.position_history,
            "winner": game.winner.value if game.winner else None,
            "created_at": game.created_at.isoformat(),
            "updated_at": game.updated_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> Game:
        board = _BOARDS[data["board_size"]]
        rules = create_rules(data["rules_name"])
        pieces = {
            Cell(p["row"], p["col"]): Piece(Color(p["color"]), PieceType(p["type"]))
            for p in data["pieces"]
        }
        players = {
            Color(pl["color"]): Player(pl["id"], pl["name"], Color(pl["color"]))
            for pl in data["players"]
        }
        return Game(
            id=data["id"],
            board=board,
            rules=rules,
            pieces=pieces,
            players=players,
            current_turn=Color(data["current_turn"]),
            state=GameState(data["state"]),
            history=MoveHistory.from_json(data["history"]),
            timer=_deserialize_timer(data["timer"]),
            pending_capture=_deserialize_pending(data["pending_capture"]),
            draw_offer=_deserialize_draw_offer(data["draw_offer"]),
            draw_reason=DrawReason(data["draw_reason"]) if data["draw_reason"] else None,
            moves_since_capture=data["moves_since_capture"],
            position_history=data["position_history"],
            winner=Color(data["winner"]) if data["winner"] else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


# --- timer ---

def _serialize_timer(timer: GameTimer) -> dict:
    return {
        "config": {
            "type": timer.config.type.value,
            "duration_seconds": timer.config.duration_seconds,
        },
        "clocks": {
            color.value: {
                "remaining_seconds": clock.remaining_seconds,
                "is_running": clock.is_running,
                "started_at": clock._started_at.isoformat() if clock._started_at else None,
            }
            for color, clock in timer.clocks.items()
        },
        "move_deadline": timer.move_deadline.isoformat() if timer.move_deadline else None,
    }


def _deserialize_timer(data: dict) -> GameTimer:
    config = TimerConfig(
        type=TimerType(data["config"]["type"]),
        duration_seconds=data["config"]["duration_seconds"],
    )
    clocks = {}
    for color_val, c in data["clocks"].items():
        clock = PlayerClock(
            remaining_seconds=c["remaining_seconds"],
            is_running=c["is_running"],
        )
        if c.get("started_at"):
            clock._started_at = datetime.fromisoformat(c["started_at"])
        clocks[Color(color_val)] = clock

    deadline = datetime.fromisoformat(data["move_deadline"]) if data.get("move_deadline") else None
    return GameTimer(config=config, clocks=clocks, move_deadline=deadline)


# --- pending capture ---

def _serialize_pending(pc: CaptureInProgress | None) -> dict | None:
    if pc is None:
        return None
    return {
        "piece_cell": _c(pc.piece_cell),
        "chain": {
            "piece_cell": _c(pc.chain.piece_cell),
            "path": [_c(c) for c in pc.chain.path],
            "captured": [_c(c) for c in pc.chain.captured],
        },
        "completed_steps": pc.completed_steps,
        "tentatively_captured": [_c(c) for c in pc.tentatively_captured],
    }


def _deserialize_pending(data: dict | None) -> CaptureInProgress | None:
    if data is None:
        return None
    chain = CaptureChain(
        piece_cell=_dc(data["chain"]["piece_cell"]),
        path=[_dc(c) for c in data["chain"]["path"]],
        captured=[_dc(c) for c in data["chain"]["captured"]],
    )
    return CaptureInProgress(
        piece_cell=_dc(data["piece_cell"]),
        chain=chain,
        completed_steps=data["completed_steps"],
        tentatively_captured=[_dc(c) for c in data["tentatively_captured"]],
    )


# --- draw offer ---

def _serialize_draw_offer(offer: DrawOffer | None) -> dict | None:
    if offer is None:
        return None
    return {
        "offered_by": offer.offered_by.value,
        "offered_at": offer.offered_at.isoformat(),
        "status": offer.status.value,
    }


def _deserialize_draw_offer(data: dict | None) -> DrawOffer | None:
    if data is None:
        return None
    return DrawOffer(
        offered_by=Color(data["offered_by"]),
        offered_at=datetime.fromisoformat(data["offered_at"]),
        status=OfferStatus(data["status"]),
    )


# --- helpers ---

def _c(cell: Cell) -> dict:
    return {"row": cell.row, "col": cell.col}


def _dc(data: dict) -> Cell:
    return Cell(data["row"], data["col"])
