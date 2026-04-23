import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..models import Color
from ..models.game import Player
from ..models.timer import TimerConfig, TimerType
from ..schemas.lobby import (
    CreateRoomRequest,
    CreateRoomResponse,
    JoinRoomRequest,
    JoinRoomResponse,
    RoomInfo,
)
from ..services.game_service import create_game, start_game

router = APIRouter()

# In-memory сховище кімнат (замінюється Redis у prod)
_waiting_rooms: dict[str, dict] = {}   # room_id → room data
_sessions: dict[str, dict] = {}        # session_id → {game_id, player_id}


@router.post("/rooms", response_model=CreateRoomResponse)
async def create_room(body: CreateRoomRequest) -> CreateRoomResponse:
    try:
        timer_type = TimerType(body.timer_type)
    except ValueError:
        raise HTTPException(400, f"Unknown timer_type: {body.timer_type!r}")

    room_id = str(uuid.uuid4())
    player_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    _waiting_rooms[room_id] = {
        "room_id": room_id,
        "creator_name": body.player_name,
        "creator_id": player_id,
        "creator_session": session_id,
        "rules": body.rules,
        "timer_type": body.timer_type,
        "timer_duration": body.timer_duration,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _sessions[session_id] = {"player_id": player_id, "game_id": None}

    return CreateRoomResponse(
        room_id=room_id,
        session_id=session_id,
        player_id=player_id,
    )


@router.get("/rooms", response_model=list[RoomInfo])
async def list_rooms() -> list[RoomInfo]:
    return [
        RoomInfo(
            room_id=r["room_id"],
            creator_name=r["creator_name"],
            rules=r["rules"],
            timer_type=r["timer_type"],
            timer_duration=r["timer_duration"],
        )
        for r in _waiting_rooms.values()
    ]


@router.post("/rooms/{room_id}/join", response_model=JoinRoomResponse)
async def join_room(room_id: str, body: JoinRoomRequest) -> JoinRoomResponse:
    room = _waiting_rooms.pop(room_id, None)
    if room is None:
        raise HTTPException(404, "Room not found or already started")

    player2_id = str(uuid.uuid4())
    session2_id = str(uuid.uuid4())

    # Створюємо гру
    p1 = Player(id=room["creator_id"], name=room["creator_name"], color=Color.WHITE)
    p2 = Player(id=player2_id, name=body.player_name, color=Color.BLACK)
    config = TimerConfig(
        type=TimerType(room["timer_type"]),
        duration_seconds=room["timer_duration"],
    )
    game = create_game(str(uuid.uuid4()), p1, p2, room["rules"], config)
    start_game(game)

    game_id = game.id

    # Прив'язуємо сесії до гри
    _sessions[room["creator_session"]]["game_id"] = game_id
    _sessions[session2_id] = {"player_id": player2_id, "game_id": game_id}

    # Зберігаємо гру в пам'яті (WebSocket handler зчитає її)
    _active_games[game_id] = game

    return JoinRoomResponse(
        room_id=room_id,
        session_id=session2_id,
        player_id=player2_id,
        game_id=game_id,
    )


# Спільне in-memory сховище активних ігор (доступне з WebSocket handler)
_active_games: dict[str, object] = {}  # game_id → Game


def get_game(game_id: str):
    return _active_games.get(game_id)


def get_session(session_id: str) -> dict | None:
    return _sessions.get(session_id)
