import pytest

from app.models import Cell
from app.models.move import CaptureChain, CaptureInProgress, Move, MoveHistory


# --- Move ---

def test_move_is_not_capture_when_no_captured():
    move = Move(from_cell=Cell(2, 2), to_cell=Cell(3, 3))
    assert move.is_capture is False


def test_move_is_capture_when_has_captured():
    move = Move(from_cell=Cell(2, 2), to_cell=Cell(4, 4), captured=(Cell(3, 3),))
    assert move.is_capture is True


def test_move_immutable():
    move = Move(from_cell=Cell(2, 2), to_cell=Cell(3, 3))
    with pytest.raises(Exception):
        move.from_cell = Cell(0, 0)


def test_move_equality():
    m1 = Move(Cell(0, 0), Cell(1, 1))
    m2 = Move(Cell(0, 0), Cell(1, 1))
    assert m1 == m2


def test_move_captured_default_empty():
    move = Move(Cell(0, 0), Cell(1, 1))
    assert move.captured == ()


# --- CaptureChain ---

def test_capture_chain_path_and_captured_equal_length():
    chain = CaptureChain(
        piece_cell=Cell(0, 0),
        path=[Cell(2, 2)],
        captured=[Cell(1, 1)],
    )
    assert len(chain.path) == len(chain.captured)


def test_capture_chain_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        CaptureChain(
            piece_cell=Cell(0, 0),
            path=[Cell(2, 2), Cell(4, 4)],
            captured=[Cell(1, 1)],
        )


def test_capture_chain_multi_jump():
    chain = CaptureChain(
        piece_cell=Cell(0, 0),
        path=[Cell(2, 2), Cell(4, 0)],
        captured=[Cell(1, 1), Cell(3, 1)],
    )
    assert len(chain.path) == 2


# --- CaptureInProgress ---

def test_capture_in_progress_tracks_completed_steps():
    chain = CaptureChain(Cell(0, 0), [Cell(2, 2)], [Cell(1, 1)])
    progress = CaptureInProgress(
        piece_cell=Cell(2, 2),
        chain=chain,
        completed_steps=1,
        tentatively_captured=[Cell(1, 1)],
    )
    assert progress.completed_steps == 1
    assert Cell(1, 1) in progress.tentatively_captured


# --- MoveHistory ---

def test_history_push_and_pop():
    history = MoveHistory()
    move = Move(Cell(0, 0), Cell(1, 1))
    history.push(move)
    assert history.pop() == move


def test_history_pop_empty_raises():
    with pytest.raises(IndexError):
        MoveHistory().pop()


def test_history_to_json_and_from_json():
    history = MoveHistory()
    history.push(Move(Cell(0, 0), Cell(1, 1)))
    history.push(Move(Cell(2, 2), Cell(4, 4), captured=(Cell(3, 3),)))

    restored = MoveHistory.from_json(history.to_json())
    assert restored.moves == history.moves
