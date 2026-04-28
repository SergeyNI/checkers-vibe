from typing import Literal

from pydantic import BaseModel, Field

RulesName = Literal["ukrainian", "brazilian", "international"]
TimerTypeName = Literal["move", "game_clock"]


class CreateRoomRequest(BaseModel):
    player_name: str = Field(min_length=1, max_length=50)
    rules: RulesName = "ukrainian"
    timer_type: TimerTypeName = "move"
    timer_duration: int = Field(default=60, ge=10, le=3600)


class CreateRoomResponse(BaseModel):
    room_id: str
    session_id: str
    player_id: str


class JoinRoomRequest(BaseModel):
    player_name: str = Field(min_length=1, max_length=50)


class JoinRoomResponse(BaseModel):
    room_id: str
    session_id: str
    player_id: str
    game_id: str


class RoomInfo(BaseModel):
    room_id: str
    creator_name: str
    rules: RulesName
    timer_type: TimerTypeName
    timer_duration: int
