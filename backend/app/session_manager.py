from fastapi import WebSocket


class SessionManager:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}      # session_id → ws
        self._session_to_game: dict[str, str] = {}        # session_id → game_id
        self._game_sessions: dict[str, set[str]] = {}     # game_id → {session_id}

    async def connect(self, session_id: str, game_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[session_id] = ws
        self._session_to_game[session_id] = game_id
        self._game_sessions.setdefault(game_id, set()).add(session_id)

    def disconnect(self, session_id: str) -> None:
        game_id = self._session_to_game.pop(session_id, None)
        self._connections.pop(session_id, None)
        if game_id:
            self._game_sessions.get(game_id, set()).discard(session_id)

    def is_connected(self, session_id: str) -> bool:
        return session_id in self._connections

    def game_id_for(self, session_id: str) -> str | None:
        return self._session_to_game.get(session_id)

    def all_disconnected(self, game_id: str) -> bool:
        sessions = self._game_sessions.get(game_id, set())
        return all(s not in self._connections for s in sessions)

    async def send(self, session_id: str, message: dict) -> None:
        ws = self._connections.get(session_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(session_id)

    async def broadcast(self, game_id: str, message: dict) -> None:
        for sid in list(self._game_sessions.get(game_id, set())):
            await self.send(sid, message)
