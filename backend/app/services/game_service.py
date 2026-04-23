from datetime import datetime, timezone

from ..models import Board, Cell, Color, Piece, PieceType
from ..models.game import DrawOffer, DrawReason, Game, GameState, OfferStatus, Player
from ..models.move import CaptureChain, CaptureInProgress, Move, MoveHistory
from ..models.timer import GameTimer, PlayerClock, TimerConfig, TimerType
from ..rules import BaseRules, create_rules, get_board
from .board_service import initial_pieces


class GameError(Exception):
    pass


def create_game(
    game_id: str,
    player1: Player,
    player2: Player,
    rules_name: str,
    timer_config: TimerConfig,
) -> Game:
    rules = create_rules(rules_name)
    board = get_board(rules)
    pieces = initial_pieces(board)

    clocks = {
        Color.WHITE: PlayerClock(remaining_seconds=float(timer_config.duration_seconds)),
        Color.BLACK: PlayerClock(remaining_seconds=float(timer_config.duration_seconds)),
    }

    return Game(
        id=game_id,
        board=board,
        rules=rules,
        pieces=pieces,
        players={player1.color: player1, player2.color: player2},
        current_turn=Color.WHITE,
        state=GameState.WAITING,
        history=MoveHistory(),
        timer=GameTimer(config=timer_config, clocks=clocks),
    )


def start_game(game: Game, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    if game.state != GameState.WAITING:
        raise GameError(f"Cannot start game in state {game.state.value}")
    game.state = GameState.ACTIVE
    game.timer.start_turn(Color.WHITE, now)
    _record_position(game)
    game.updated_at = now


def apply_move(game: Game, player_id: str, from_cell: Cell, to_cell: Cell, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    _assert_active(game)
    _assert_turn(game, player_id)

    rules: BaseRules = game.rules

    if game.pending_capture is not None:
        _continue_capture(game, to_cell, now)
    elif rules.is_capture_mandatory(game.pieces, game.board, game.current_turn):
        _start_capture(game, from_cell, to_cell, now)
    else:
        _execute_regular_move(game, from_cell, to_cell, now)

    game.updated_at = now


def offer_draw(game: Game, player_id: str) -> None:
    _assert_active(game)
    color = _color_of(game, player_id)
    if game.draw_offer is not None and game.draw_offer.status == OfferStatus.PENDING:
        raise GameError("Draw already offered")
    game.draw_offer = DrawOffer(offered_by=color, offered_at=datetime.now(timezone.utc))


def respond_draw(game: Game, player_id: str, accepted: bool, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    _assert_active(game)
    if game.draw_offer is None or game.draw_offer.status != OfferStatus.PENDING:
        raise GameError("No pending draw offer")
    color = _color_of(game, player_id)
    if color == game.draw_offer.offered_by:
        raise GameError("Cannot respond to your own draw offer")
    if accepted:
        game.draw_offer.status = OfferStatus.ACCEPTED
        _finish_draw(game, DrawReason.AGREEMENT, now)
    else:
        game.draw_offer.status = OfferStatus.DECLINED


def resign(game: Game, player_id: str, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    _assert_active(game)
    color = _color_of(game, player_id)
    opponent = Color.BLACK if color == Color.WHITE else Color.WHITE
    game.winner = opponent
    game.state = GameState.FINISHED
    game.timer.stop_turn(color, now)
    game.updated_at = now


# --- internal ---

def _continue_capture(game: Game, to_cell: Cell, now: datetime) -> None:
    pc = game.pending_capture
    rules: BaseRules = game.rules

    chains = rules.get_valid_capture_chains(game.pieces, game.board, pc.piece_cell)
    matching = [c for c in chains if len(c.path) > 0 and c.path[0] == to_cell]
    if not matching:
        raise GameError(f"Invalid capture step to {to_cell}")

    chain = matching[0]
    cap_cell = chain.captured[0]

    # виконуємо стрибок
    piece = game.pieces.pop(pc.piece_cell)
    game.pieces.pop(cap_cell, None)
    game.pieces[to_cell] = piece

    new_tentative = pc.tentatively_captured + [cap_cell]
    completed = pc.completed_steps + 1

    # перевіряємо чи є ще обов'язкові захоплення
    remaining = rules.get_valid_capture_chains(game.pieces, game.board, to_cell)
    if remaining:
        game.pending_capture = CaptureInProgress(
            piece_cell=to_cell,
            chain=chain,
            completed_steps=completed,
            tentatively_captured=new_tentative,
        )
    else:
        # серія завершена
        game.pending_capture = None
        _check_promotion(game, to_cell, is_capturing=False)
        game.history.push(Move(pc.piece_cell, to_cell, captured=tuple(new_tentative)))
        game.moves_since_capture = 0
        _finalize_turn(game, now)


def _start_capture(game: Game, from_cell: Cell, to_cell: Cell, now: datetime) -> None:
    rules: BaseRules = game.rules
    chains = rules.get_valid_capture_chains(game.pieces, game.board, from_cell)
    matching = [c for c in chains if c.path[0] == to_cell]
    if not matching:
        raise GameError(f"No valid capture from {from_cell} to {to_cell}")

    chain = matching[0]
    cap_cell = chain.captured[0]

    piece = game.pieces.pop(from_cell)
    game.pieces.pop(cap_cell, None)
    game.pieces[to_cell] = piece

    # Ukrainian: promotion зупиняє серію
    if rules.should_promote(to_cell, piece.color, game.board, is_capturing=True):
        game.pieces[to_cell] = Piece(color=piece.color, type=PieceType.QUEEN)
        game.history.push(Move(from_cell, to_cell, captured=(cap_cell,)))
        game.moves_since_capture = 0
        game.pending_capture = None
        _finalize_turn(game, now)
        return

    remaining = rules.get_valid_capture_chains(game.pieces, game.board, to_cell)
    if remaining:
        game.pending_capture = CaptureInProgress(
            piece_cell=to_cell,
            chain=chain,
            completed_steps=1,
            tentatively_captured=[cap_cell],
        )
        # таймер продовжує йти поки серія не завершена
    else:
        game.history.push(Move(from_cell, to_cell, captured=(cap_cell,)))
        game.moves_since_capture = 0
        game.pending_capture = None
        _finalize_turn(game, now)


def _execute_regular_move(game: Game, from_cell: Cell, to_cell: Cell, now: datetime) -> None:
    rules: BaseRules = game.rules
    valid = rules.get_valid_moves(game.pieces, game.board, from_cell)
    if not any(m.to_cell == to_cell for m in valid):
        raise GameError(f"Invalid move from {from_cell} to {to_cell}")

    piece = game.pieces.pop(from_cell)
    game.pieces[to_cell] = piece

    _check_promotion(game, to_cell, is_capturing=False)
    game.history.push(Move(from_cell, to_cell))
    game.moves_since_capture += 1
    _finalize_turn(game, now)


def _check_promotion(game: Game, cell: Cell, is_capturing: bool) -> None:
    piece = game.pieces.get(cell)
    if piece and piece.type == PieceType.MAN:
        if game.rules.should_promote(cell, piece.color, game.board, is_capturing):
            game.pieces[cell] = Piece(color=piece.color, type=PieceType.QUEEN)


def _finalize_turn(game: Game, now: datetime) -> None:
    opponent = Color.BLACK if game.current_turn == Color.WHITE else Color.WHITE

    game.timer.stop_turn(game.current_turn, now)

    _record_position(game)
    _check_draw_conditions(game)

    if game.state == GameState.FINISHED:
        return

    _check_win_condition(game, opponent)

    if game.state == GameState.FINISHED:
        return

    game.current_turn = opponent
    game.timer.start_turn(opponent, now)


def _check_win_condition(game: Game, next_player: Color) -> None:
    rules: BaseRules = game.rules
    has_pieces = any(p.color == next_player for p in game.pieces.values())
    if not has_pieces:
        game.winner = Color.BLACK if next_player == Color.WHITE else Color.WHITE
        game.state = GameState.FINISHED
        return

    has_moves = any(
        rules.get_valid_moves(game.pieces, game.board, cell) or
        rules.get_valid_capture_chains(game.pieces, game.board, cell)
        for cell, piece in game.pieces.items()
        if piece.color == next_player
    )
    if not has_moves:
        game.winner = Color.BLACK if next_player == Color.WHITE else Color.WHITE
        game.state = GameState.FINISHED


def _check_draw_conditions(game: Game) -> None:
    rules: BaseRules = game.rules
    if game.moves_since_capture >= rules.move_limit_threshold:
        _finish_draw(game, DrawReason.MOVE_LIMIT)
        return

    current_hash = game.position_history[-1] if game.position_history else None
    if current_hash and game.position_history.count(current_hash) >= 3:
        _finish_draw(game, DrawReason.REPETITION)


def _finish_draw(game: Game, reason: DrawReason, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    game.state = GameState.FINISHED
    game.winner = None
    game.draw_reason = reason
    game.updated_at = now


def _record_position(game: Game) -> None:
    game.position_history.append(game.position_hash())


def _assert_active(game: Game) -> None:
    if game.state != GameState.ACTIVE:
        raise GameError(f"Game is not active (state={game.state.value})")


def _assert_turn(game: Game, player_id: str) -> None:
    player = next((p for p in game.players.values() if p.id == player_id), None)
    if player is None:
        raise GameError(f"Player {player_id!r} not in game")
    if player.color != game.current_turn:
        raise GameError("Not your turn")


def _color_of(game: Game, player_id: str) -> Color:
    player = next((p for p in game.players.values() if p.id == player_id), None)
    if player is None:
        raise GameError(f"Player {player_id!r} not in game")
    return player.color
