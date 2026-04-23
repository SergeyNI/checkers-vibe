from typing import Any

from pydantic import BaseModel


# --- client → server ---

class MakeMoveMsg(BaseModel):
    type: str = "make_move"
    from_cell: dict  # {row, col}
    to_cell: dict    # {row, col}


class OfferDrawMsg(BaseModel):
    type: str = "offer_draw"


class RespondDrawMsg(BaseModel):
    type: str = "respond_draw"
    accepted: bool


class ResignMsg(BaseModel):
    type: str = "resign"


class ReconnectMsg(BaseModel):
    type: str = "reconnect"
    session_id: str


# --- server → client ---

def game_snapshot_msg(game_dict: dict, capture_chains: dict) -> dict:
    return {
        "type": "game_snapshot",
        "game": game_dict,
        "capture_chains": capture_chains,
    }


def error_msg(message: str) -> dict:
    return {"type": "error", "message": message}


def game_finished_msg(winner: str | None, draw_reason: str | None) -> dict:
    return {"type": "game_finished", "winner": winner, "draw_reason": draw_reason}


def draw_offered_msg(offered_by: str) -> dict:
    return {"type": "draw_offered", "offered_by": offered_by}
