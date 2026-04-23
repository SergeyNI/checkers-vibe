import pytest

from app.models import BOARD_8, BOARD_10, Board


@pytest.fixture
def board_8() -> Board:
    return BOARD_8


@pytest.fixture
def board_10() -> Board:
    return BOARD_10
