import operator
from collections.abc import Sequence
from enum import Enum
from functools import partial

from pente.game.rule.Applicable import Applicable
from pente.game.GameState import GameState


class ScoreAction(Applicable):
    class Operation(Enum):
        # functools.partial is used as a workaround to allow callable enum members
        # Credit: https://stackoverflow.com/questions/40338652/how-to-define-enum-values-that-are-functions
        SET = partial(lambda a, b: b)
        ADD = partial(operator.add)
        MULTIPLY = partial(operator.mul)

        def __call__(self, *args, **kwargs):
            return self.value(*args, **kwargs)

    def __init__(self, player_index: int, memo: str, operation: Operation, value: int):
        self.__player_index = player_index
        self.__memo = memo
        self.__operation = operation
        self.__value = value

    def apply(self, gamestate: GameState, locations: Sequence[tuple[int, ...]], center: tuple[int, ...]) -> bool:
        player = self._resolve_player_index(gamestate, locations, center, self.__player_index)
        previous = gamestate.scores[self.__memo][player]
        gamestate.scores[self.__memo][player] = self.__operation(previous, self.__value)
        return True
