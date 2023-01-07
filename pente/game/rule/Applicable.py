from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import IntEnum

from pente.game.Board import EMPTY
from pente.game.GameState import GameState


# A:complex-oop
# The abstract class Applicable defines the utility method _resolve_player_index used by its subclasses
class Applicable(ABC):
    """Anything that looks at a pattern match is applicable"""

    class _PlayerIndexRogue(IntEnum):
        """The rogue values used for player_index keys in datapacks"""
        CENTER = -1
        ACTIVE = -2
        REMOVE = -3

    @abstractmethod
    def apply(self, gamestate: GameState, locations: Sequence[tuple[int, ...]], center: tuple[int, ...]) -> bool:
        raise NotImplementedError

    @staticmethod
    def _resolve_player_index(gamestate: GameState, locations: Sequence[tuple[int, ...]], center: tuple[int, ...],
                              player_index: int) -> int:
        """
        Resolve a player index specified within a rule, including the rogue values -1, -2, and -3
        :param gamestate: The gamestate within which to resolve the index
        :param locations: The match locations
        :param center: The location of the center in the board (NOT an index into locations)
        :param player_index: The index to resolve
        :returns: The player at that index
        """
        if player_index == Applicable._PlayerIndexRogue.REMOVE:
            return EMPTY
        elif player_index == Applicable._PlayerIndexRogue.ACTIVE:
            return gamestate.active_player
        elif player_index == Applicable._PlayerIndexRogue.CENTER:
            return gamestate.board[center]
        else:
            player = gamestate.board[locations[player_index]]
            if player == EMPTY:
                raise RuntimeError("Player index referred to empty tile (likely caused by a broken datapack)")
            return player
