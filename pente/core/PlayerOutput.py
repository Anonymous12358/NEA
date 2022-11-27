from __future__ import annotations

from abc import ABC, abstractmethod

from pente.game.Game import Game


class PlayerOutput(ABC):
    @abstractmethod
    def send_update(self, game: Game, your_index: int, is_hotseat: bool):
        raise NotImplementedError

    @abstractmethod
    def send_victory(self, game: Game, your_index: int, is_hotseat: bool):
        raise NotImplementedError
