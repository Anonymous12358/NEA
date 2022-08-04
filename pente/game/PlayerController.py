from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence

from pente.game.Board import Board
from pente.game.GameState import GameState


class PlayerController(ABC):
    @abstractmethod
    def get_move(self, validator: Callable[[tuple[int, ...]], bool]) -> tuple[int, ...]:
        raise NotImplementedError

    @abstractmethod
    def update(self, board: Board, displayable_scores: Sequence[tuple[str, Sequence[int]]], is_your_turn: bool):
        raise NotImplementedError

    @abstractmethod
    def send_victory(self, gamestate: GameState, winner: int, is_you: bool):
        raise NotImplementedError
