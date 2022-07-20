from abc import ABC, abstractmethod
from collections.abc import Callable

from pente.game.GameState import GameState


class PlayerController(ABC):
    @abstractmethod
    def get_move(self, validator: Callable[[tuple[int, ...]], bool]) -> tuple[int, ...]:
        raise NotImplementedError

    @abstractmethod
    def update(self, gamestate: GameState, is_your_turn: bool):
        raise NotImplementedError

    @abstractmethod
    def send_victory(self, winner: int, is_you: bool):
        raise NotImplementedError
