from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TimerType(Enum):
    MOVE = "move"            # фіксований час на кожен хід, скидається на початку
    GAME_CLOCK = "game_clock"  # загальний бюджет часу гравця на всю гру


@dataclass
class TimerConfig:
    type: TimerType
    duration_seconds: int


@dataclass
class PlayerClock:
    remaining_seconds: float
    is_running: bool = False
    _started_at: datetime | None = field(default=None, repr=False)

    def start(self, now: datetime) -> None:
        if not self.is_running:
            self._started_at = now
            self.is_running = True

    def stop(self, now: datetime) -> None:
        if self.is_running and self._started_at is not None:
            elapsed = (now - self._started_at).total_seconds()
            self.remaining_seconds = max(0.0, self.remaining_seconds - elapsed)
            self.is_running = False
            self._started_at = None

    def is_expired(self) -> bool:
        return self.remaining_seconds <= 0


@dataclass
class GameTimer:
    config: TimerConfig
    clocks: dict  # dict[Color, PlayerClock] — Color імпортується в game.py
    move_deadline: datetime | None = None

    def start_turn(self, color, now: datetime) -> None:
        from .piece import Color
        for c, clock in self.clocks.items():
            clock.stop(now)
        self.clocks[color].start(now)
        if self.config.type == TimerType.MOVE:
            from datetime import timedelta
            self.move_deadline = now + timedelta(seconds=self.config.duration_seconds)

    def stop_turn(self, color, now: datetime) -> None:
        self.clocks[color].stop(now)
        self.move_deadline = None

    def is_expired(self, color) -> bool:
        return self.clocks[color].is_expired()
