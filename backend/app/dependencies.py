import os
from functools import lru_cache

from .services.redis_store import RedisGameStore
from .session_manager import SessionManager

# Singleton instances — ініціалізуються при першому зверненні

@lru_cache(maxsize=1)
def get_session_manager() -> SessionManager:
    return SessionManager()


@lru_cache(maxsize=1)
def get_redis_store() -> RedisGameStore:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return RedisGameStore(redis_url=url)
