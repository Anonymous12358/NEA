from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import IntEnum

from pente.game.Board import EMPTY
from pente.game.GameState import GameState


class Applicable(ABC):
    class PlayerIndexRogue(IntEnum):
        CENTER = -1
        ACTIVE = -2
        REMOVE = -3

    @abstractmethod
    def apply(self, gamestate: GameState, locations: Sequence[tuple[int, ...]], center: tuple[int, ...]):
        raise NotImplementedError

    @staticmethod
    def resolve_player_index(gamestate: GameState, locations: Sequence[tuple[int, ...]], center: tuple[int, ...],
                             player_index: int):
        """
        Resolve a player index specified within a rule, including the rogue values -1, -2, and -3
        :param gamestate: The gamestate within which to resolve the index
        :param locations: The match locations
        :param center: The location of the center in the board (NOT an index into locations)
        :param player_index: The index to resolve
        :return:
        """
        if player_index == Applicable.PlayerIndexRogue.REMOVE:
            return EMPTY
        elif player_index == Applicable.PlayerIndexRogue.ACTIVE:
            return gamestate.active_player
        elif player_index == Applicable.PlayerIndexRogue.CENTER:
            return gamestate.board[center]
        else:
            player = gamestate.board[locations[player_index]]
            if player == EMPTY:
                raise RuntimeError("Player index refered to empty tile (likely caused by an unsafe datapack)")
