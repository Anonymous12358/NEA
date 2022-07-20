from collections.abc import Iterable
from dataclasses import dataclass, InitVar, field

from pente.game.Board import Board


@dataclass
class GameState:
    board: Board
    memos: InitVar[Iterable[str]]
    num_players: int
    scores: dict[str, list[int]] = field(init=False, default=None)
    active_player: int = field(init=False, default=-1)

    def __post_init__(self, memos: list[str]):
        self.scores = {memo: [0] * self.num_players for memo in memos}
