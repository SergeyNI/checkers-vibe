from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..models import Cell, Color
from ..models.game import GameState
from ..rules.base import BaseRules
from ..schemas.ws_messages import (
    draw_offered_msg,
    error_msg,
    game_finished_msg,
    game_snapshot_msg,
)
from ..services.game_serializer import GameSerializer
from ..services.game_service import (
    GameError,
    apply_move,
    expire_by_timeout,
    offer_draw,
    resign,
    respond_draw,
)
from ..dependencies import get_redis_store, get_session_manager
from ..session_manager import SessionManager
from .lobby import _active_games, get_session

router = APIRouter()


def _valid_moves_for_current_player(game) -> dict:
    rules: BaseRules = game.rules
    if game.state != GameState.ACTIVE or game.pending_capture is not None:
        return {}
    if rules.is_capture_mandatory(game.pieces, game.board, game.current_turn):
        return {}
    result = {}
    for cell, piece in game.pieces.items():
        if piece.color == game.current_turn:
            moves = rules.get_valid_moves(game.pieces, game.board, cell)
            if moves:
                result[f"{cell.row},{cell.col}"] = [
                    {"row": m.to_cell.row, "col": m.to_cell.col} for m in moves
                ]
    return result


def _capture_chains_for_current_player(game) -> dict:
    rules: BaseRules = game.rules
    if game.state != GameState.ACTIVE:
        return {}

    if game.pending_capture is not None:
        pc = game.pending_capture
        chains = rules.get_valid_capture_chains(game.pieces, game.board, pc.piece_cell)
        if not chains:
            return {}
        key = f"{pc.piece_cell.row},{pc.piece_cell.col}"
        return {
            key: [
                {
                    "path": [{"row": c.row, "col": c.col} for c in ch.path],
                    "captured": [{"row": c.row, "col": c.col} for c in ch.captured],
                }
                for ch in chains
            ]
        }

    if not rules.is_capture_mandatory(game.pieces, game.board, game.current_turn):
        return {}
    result = {}
    for cell, piece in game.pieces.items():
        if piece.color == game.current_turn:
            chains = rules.get_valid_capture_chains(game.pieces, game.board, cell)
            if chains:
                key = f"{cell.row},{cell.col}"
                result[key] = [
                    {
                        "path": [{"row": c.row, "col": c.col} for c in ch.path],
                        "captured": [{"row": c.row, "col": c.col} for c in ch.captured],
                    }
                    for ch in chains
                ]
    return result


async def _broadcast_snapshot(game, manager: SessionManager) -> None:
    chains = _capture_chains_for_current_player(game)
    valid_moves = _valid_moves_for_current_player(game)
    msg = game_snapshot_msg(GameSerializer.to_dict(game), chains)
    msg["valid_moves"] = valid_moves
    await manager.broadcast(game.id, msg)

    if game.state == GameState.FINISHED:
        finished = game_finished_msg(
            winner=game.winner.value if game.winner else None,
            draw_reason=game.draw_reason.value if game.draw_reason else None,
        )
        await manager.broadcast(game.id, finished)
        _active_games.pop(game.id, None)


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(ws: WebSocket, session_id: str) -> None:
    store = get_redis_store()
    manager = get_session_manager()

    session = get_session(session_id) or await store.get_session_data(session_id)
    if session is None:
        await ws.close(code=4004)
        return

    game_id = session.get("game_id")
    if game_id is None:
        await ws.close(code=4003)
        return

    game = _active_games.get(game_id)
    if game is None:
        game = await store.load(game_id)
        if game is None:
            await ws.close(code=4004)
            return
        _active_games[game_id] = game

    await manager.connect(session_id, game_id, ws)

    # Відправляємо поточний стан гри при підключенні
    await _broadcast_snapshot(game, manager)

    player_id = session["player_id"]

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")
            now = datetime.now(timezone.utc)

            try:
                if msg_type == "make_move":
                    from_cell = Cell(data["from_cell"]["row"], data["from_cell"]["col"])
                    to_cell = Cell(data["to_cell"]["row"], data["to_cell"]["col"])
                    apply_move(game, player_id, from_cell, to_cell, now)
                    await store.save(game)
                    await _broadcast_snapshot(game, manager)

                elif msg_type == "offer_draw":
                    offer_draw(game, player_id)
                    await store.save(game)
                    await manager.broadcast(game_id, draw_offered_msg(
                        next(p for p in game.players.values() if p.id == player_id).color.value
                    ))

                elif msg_type == "respond_draw":
                    respond_draw(game, player_id, accepted=data.get("accepted", False), now=now)
                    await store.save(game)
                    await _broadcast_snapshot(game, manager)

                elif msg_type == "resign":
                    resign(game, player_id, now)
                    await store.save(game)
                    await _broadcast_snapshot(game, manager)

                elif msg_type == "check_timer":
                    if game.state == GameState.ACTIVE and game.timer.is_expired(game.current_turn, now):
                        expire_by_timeout(game, game.current_turn, now)
                        await store.save(game)
                        await _broadcast_snapshot(game, manager)

                else:
                    await manager.send(session_id, error_msg(f"Unknown message type: {msg_type!r}"))

            except GameError as e:
                await manager.send(session_id, error_msg(str(e)))

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        if manager.all_disconnected(game_id):
            if game.state == GameState.FINISHED:
                await store.delete(game_id)
            else:
                game.state = GameState.PAUSED
                await store.save(game)
