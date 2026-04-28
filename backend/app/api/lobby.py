import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..dependencies import get_redis_store
from ..models import Color
from ..models.game import Game, Player
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

# In-memory сховища (write-through кеш; авторитетне сховище — Redis)
_waiting_rooms: dict[str, dict] = {}   # room_id → room data
_sessions: dict[str, dict] = {}        # session_id → {game_id, player_id}
_active_games: dict[str, Game] = {}    # game_id → Game


@router.post("/rooms", response_model=CreateRoomResponse)
async def create_room(body: CreateRoomRequest) -> CreateRoomResponse:
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
    store = get_redis_store()
    session_data = {"player_id": player_id, "game_id": None}
    _sessions[session_id] = session_data
    await store.save_session_data(session_id, session_data)

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
    store = get_redis_store()

    # Прив'язуємо сесії до гри
    creator_session_data = {"player_id": room["creator_id"], "game_id": game_id}
    joiner_session_data = {"player_id": player2_id, "game_id": game_id}
    _sessions[room["creator_session"]] = creator_session_data
    _sessions[session2_id] = joiner_session_data
    _active_games[game_id] = game
    await asyncio.gather(
        store.save_session_data(room["creator_session"], creator_session_data),
        store.save_session_data(session2_id, joiner_session_data),
        store.save(game),
    )

    return JoinRoomResponse(
        room_id=room_id,
        session_id=session2_id,
        player_id=player2_id,
        game_id=game_id,
    )


def get_game(game_id: str):
    return _active_games.get(game_id)


def get_session(session_id: str) -> dict | None:
    return _sessions.get(session_id)
