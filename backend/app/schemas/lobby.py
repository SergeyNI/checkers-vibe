from pydantic import BaseModel, Field


class CreateRoomRequest(BaseModel):
    player_name: str
    rules: str = "ukrainian"
    timer_type: str = "move"
    timer_duration: int = Field(default=60, ge=10, le=3600)


class CreateRoomResponse(BaseModel):
    room_id: str
    session_id: str
    player_id: str


class JoinRoomRequest(BaseModel):
    player_name: str


class JoinRoomResponse(BaseModel):
    room_id: str
    session_id: str
    player_id: str
    game_id: str


class RoomInfo(BaseModel):
    room_id: str
    creator_name: str
    rules: str
    timer_type: str
    timer_duration: int
