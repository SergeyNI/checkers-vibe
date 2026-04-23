from app.models import BOARD_8, BOARD_10, Board, Cell
from app.models.diagonal import DiagonalDirection


def test_board_8_dark_cells_count(board_8):
    assert board_8.dark_cells_count == 32


def test_board_10_dark_cells_count(board_10):
    assert board_10.dark_cells_count == 50


def test_board_constants_are_singletons():
    assert BOARD_8 is BOARD_8
    assert BOARD_10 is BOARD_10


def test_all_valid_cells_are_dark(board_8):
    for cell in board_8.valid_cells:
        assert (cell.row + cell.col) % 2 == 0


def test_main_road_exists_on_8x8(board_8):
    main_road = next(
        (d for d in board_8.ascending_diagonals if d.name == "main_road"), None
    )
    assert main_road is not None


def test_main_road_goes_corner_to_corner(board_8):
    main_road = next(d for d in board_8.ascending_diagonals if d.name == "main_road")
    assert main_road.cells[0] == Cell(0, 0)
    assert main_road.cells[-1] == Cell(7, 7)
    assert len(main_road.cells) == 8


def test_main_road_exists_on_10x10(board_10):
    main_road = next(
        (d for d in board_10.ascending_diagonals if d.name == "main_road"), None
    )
    assert main_road is not None
    assert len(main_road.cells) == 10


def test_diagonal_cells_ordered_by_ascending_row(board_8):
    for diag in board_8.ascending_diagonals + board_8.descending_diagonals:
        rows = [c.row for c in diag.cells]
        assert rows == sorted(rows)


def test_all_diagonals_have_at_least_two_cells(board_8):
    for diag in board_8.ascending_diagonals + board_8.descending_diagonals:
        assert len(diag.cells) >= 2


def test_corner_cell_has_one_diagonal(board_8):
    # (0,0) — кут головної дороги, descending лінія має лише 1 клітинку
    diagonals = board_8.get_diagonals(Cell(0, 0))
    assert len(diagonals) == 1
    assert diagonals[0].direction == DiagonalDirection.ASCENDING


def test_corner_h8_has_one_diagonal(board_8):
    diagonals = board_8.get_diagonals(Cell(7, 7))
    assert len(diagonals) == 1


def test_middle_cell_has_two_diagonals(board_8):
    diagonals = board_8.get_diagonals(Cell(3, 3))
    assert len(diagonals) == 2


def test_get_diagonal_ascending(board_8):
    diag = board_8.get_diagonal(Cell(0, 0), DiagonalDirection.ASCENDING)
    assert diag is not None
    assert diag.name == "main_road"


def test_get_diagonal_descending_none_for_corner(board_8):
    diag = board_8.get_diagonal(Cell(0, 0), DiagonalDirection.DESCENDING)
    assert diag is None


def test_every_valid_cell_in_at_least_one_diagonal(board_8):
    for cell in board_8.valid_cells:
        assert len(board_8.get_diagonals(cell)) >= 1
