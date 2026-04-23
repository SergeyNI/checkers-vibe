import pytest

from app.models import Cell


def test_cell_equality():
    assert Cell(1, 2) == Cell(1, 2)


def test_cell_inequality():
    assert Cell(1, 2) != Cell(2, 1)


def test_cell_hashable():
    d = {Cell(0, 0): "piece"}
    assert d[Cell(0, 0)] == "piece"


def test_cell_usable_as_set_member():
    s = {Cell(0, 0), Cell(1, 1), Cell(0, 0)}
    assert len(s) == 2


def test_cell_immutable():
    cell = Cell(1, 2)
    with pytest.raises(Exception):
        cell.row = 5
