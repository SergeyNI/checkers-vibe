import json

import redis.asyncio as aioredis

from ..models.game import Game
from .game_serializer import GameSerializer

GAME_TTL = 86400       # 24 год
SESSION_TTL = 3600     # 1 год
PLAYER_TTL = 86400     # 24 год


class RedisGameStore:
    def __init__(self, redis_url: str, ttl: int = GAME_TTL) -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl

    async def save(self, game: Game) -> None:
        key = f"game:{game.id}"
        data = json.dumps(GameSerializer.to_dict(game))
        await self._redis.set(key, data, ex=self._ttl)

    async def load(self, game_id: str) -> Game | None:
        key = f"game:{game_id}"
        data = await self._redis.get(key)
        if data is None:
            return None
        return GameSerializer.from_dict(json.loads(data))

    async def delete(self, game_id: str) -> None:
        await self._redis.delete(f"game:{game_id}")

    async def exists(self, game_id: str) -> bool:
        return bool(await self._redis.exists(f"game:{game_id}"))

    async def save_player_game(self, player_id: str, game_id: str) -> None:
        await self._redis.set(f"player:{player_id}:game", game_id, ex=PLAYER_TTL)

    async def get_player_game(self, player_id: str) -> str | None:
        return await self._redis.get(f"player:{player_id}:game")

    async def save_session_data(self, session_id: str, data: dict) -> None:
        await self._redis.set(f"session:{session_id}", json.dumps(data), ex=SESSION_TTL)

    async def get_session_data(self, session_id: str) -> dict | None:
        raw = await self._redis.get(f"session:{session_id}")
        return json.loads(raw) if raw else None

    async def close(self) -> None:
        await self._redis.aclose()
