import itertools
import operator
from collections.abc import Sequence, Collection
from enum import Enum
from functools import partial
from typing import Optional

from pente.game.rule.Applicable import Applicable
from pente.game.GameState import GameState


class ScoreCondition(Applicable):
    class Comparison(Enum):
        # functools.partial is used as a workaround to allow callable enum members
        # credit so/40338625
        LESS_THAN = partial(operator.lt)
        GREATER_THAN = partial(operator.gt)
        EQUAL = partial(operator.eq)
        MULTIPLE = partial(lambda a, b: a % b == 0)

        def __call__(self, *args, **kwargs):
            return self.value(*args, **kwargs)

    def __init__(self, player_index: int, memo: str, comparison: Comparison, value: int):
        self.__player_index = player_index
        self.__memo = memo
        self.__comparison = comparison
        self.__value = value

    def apply(self, gamestate: GameState, locations: Sequence[tuple[int, ...]], center: tuple[int, ...]):
        scores = gamestate.scores[self.__memo]
        player = self.resolve_player_index(gamestate, locations, center, self.__player_index)
        return self.__comparison(scores[player], self.__value)


class CoordsCondition(Applicable):
    def __init__(self, axes: Collection[int], minimum: Optional[int], maximum: Optional[int]):
        self.__axes = axes
        self.__minimum = minimum
        self.__maximum = maximum

    def apply(self, gamestate: GameState, locations: Sequence[tuple[int, ...]], center: tuple[int, ...]):
        for ordinate in itertools.compress(center, self.__axes):
            if (self.__minimum is not None and ordinate < self.__minimum or
                    self.__maximum is not None and ordinate > self.__maximum):
                return False
        else:
            return True


# Sum type is neater than empty superclass
Condition = ScoreCondition | CoordsCondition
