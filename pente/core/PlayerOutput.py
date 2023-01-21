from __future__ import annotations

from abc import ABC, abstractmethod

from pente.game.Game import Game


###############################################################################################################
# GROUP A SKILL: COMPLEX USER-DEFINED USE OF OOP MODE                                                         #
# The PlayerOutput interface is implemented separately by each UI, so that the Core can call the same methods #
# regardless of the UI in use                                                                                 #
###############################################################################################################
class PlayerOutput(ABC):
    @abstractmethod
    def send_update(self, game: Game, your_index: int, is_hotseat: bool):
        raise NotImplementedError

    @abstractmethod
    def send_victory(self, game: Game, your_index: int, is_hotseat: bool):
        raise NotImplementedError
