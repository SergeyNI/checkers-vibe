from ..models import Board, BOARD_8, BOARD_10
from .base import BaseRules
from .ukrainian import UkrainianRules
from .brazilian import BrazilianRules
from .international import InternationalRules

_RULES: dict[str, type[BaseRules]] = {
    "ukrainian": UkrainianRules,
    "brazilian": BrazilianRules,
    "international": InternationalRules,
}


def create_rules(name: str) -> BaseRules:
    cls = _RULES.get(name)
    if cls is None:
        raise ValueError(f"Unknown rules: {name!r}. Choose from: {list(_RULES)}")
    return cls()


def get_board(rules: BaseRules) -> Board:
    return BOARD_8 if rules.board_size == 8 else BOARD_10
