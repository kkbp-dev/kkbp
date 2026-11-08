"""A Step: one built-in unit of work within the Core Import."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..bundle._contract import GAMES
from .options import Option


@dataclass(frozen=True)
class Step:
    """`fn(ctx)`, run for the Games in `games`, or for every Game when `games` is empty.

    Game lists name exact Games; profile inheritance never widens them (docs/design/game-profile.md).
    """

    fn: Callable
    games: tuple[str, ...] = ()
    options: tuple[Option, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "games", tuple(self.games))
        object.__setattr__(self, "options", tuple(self.options))
        unknown = [g for g in self.games if g not in GAMES]
        if unknown:
            raise ValueError(f"Step {self.name}: unknown Game {', '.join(unknown)}; Games are {', '.join(GAMES)}")

    @property
    def name(self) -> str:
        return self.fn.__name__

    def runs_on(self, game: str) -> bool:
        return not self.games or game in self.games
