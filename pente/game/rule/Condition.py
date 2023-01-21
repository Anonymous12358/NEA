from collections.abc import Sequence, Collection
from typing import Optional

from pente.game.rule.Applicable import Applicable
from pente.game.GameState import GameState


class ScoreCondition(Applicable):
    def __init__(self, player_index: int, memo: str, minimum: Optional[int] = None, maximum: Optional[int] = None):
        self.__player_index = player_index
        self.__memo = memo
        self.__minimum = minimum
        self.__maximum = maximum

    def apply(self, gamestate: GameState, locations: Sequence[tuple[int, ...]], center: tuple[int, ...]) -> bool:
        scores = gamestate.scores[self.__memo]
        player = self._resolve_player_index(gamestate, locations, center, self.__player_index)
        if (self.__minimum is not None and scores[player] < self.__minimum or
                self.__maximum is not None and scores[player] > self.__maximum):
            return False
        return True


class CoordsCondition(Applicable):
    def __init__(self, axes: Collection[int], minimum: Optional[int], maximum: Optional[int]):
        self.__axes = axes
        self.__minimum = minimum
        self.__maximum = maximum

    def apply(self, gamestate: GameState, locations: Sequence[tuple[int, ...]], center: tuple[int, ...]) -> bool:
        for axis, ordinate in enumerate(center):
            if axis not in self.__axes:
                continue
            if (self.__minimum is not None and ordinate < self.__minimum or
                    self.__maximum is not None and ordinate > self.__maximum):
                return False
        else:
            return True


#####################################################################################################################
# GROUP A SKILL: OTHER TECHNICAL SKILL                                                                              #
# Defined Condition as a sum type of two classes, to avoid the need for an abstract class which would associate the #
# classes but not define functionality                                                                              #
#####################################################################################################################

# Sum type is neater than empty superclass
Condition = ScoreCondition | CoordsCondition
