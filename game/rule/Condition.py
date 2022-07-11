import operator
from collections.abc import Sequence
from enum import Enum, auto
from functools import partial
from typing import Optional

from game.rule.Applicable import Applicable
from game.GameState import GameState


class Condition(Applicable):
    class PlayerType(Enum):
        PLAYER = auto()
        OPPONENT = auto()
        ALL = auto()

    class Operation(Enum):
        # functools.partial is used as a workaround to allow callable enum members
        # credit so/40338625
        MAX = partial(max)
        MIN = partial(min)
        MEAN = partial(lambda x: sum(x)/len(x))

        def __call__(self, *args, **kwargs):
            return self.value(*args, **kwargs)

    class Comparison(Enum):
        LESS_THAN = partial(operator.lt)
        GREATER_THAN = partial(operator.gt)
        EQUAL = partial(operator.eq)
        MULTIPLE = partial(lambda a, b: a % b == 0)

        def __call__(self, *args, **kwargs):
            return self.value(*args, **kwargs)

    def __init__(self, player_index: int, memo: str, player_type: PlayerType, operation: Optional[Operation],
                 comparison: Comparison, value: int):
        if operation is None and player_type != Condition.PlayerType.PLAYER:
            raise ValueError("Operation may only be None for player_type == PLAYER")
        if operation is not None and player_type == Condition.PlayerType.PLAYER:
            raise ValueError("Operation must be None for player_type == PLAYER")

        self.__player_index = player_index
        self.__memo = memo
        self.__player_type = player_type
        self.__operation = operation
        self.__comparison = comparison
        self.__value = value

    def apply(self, gamestate: GameState, locations: Sequence[tuple[int, ...]], center: tuple[int, ...]):
        scores = gamestate.scores[self.__memo]
        player = self.resolve_player_index(gamestate, locations, center, self.__player_index)
        if self.__player_type == Condition.PlayerType.PLAYER:
            score = scores[player]
        else:
            if self.__player_type == Condition.PlayerType.OPPONENT:
                player = gamestate.board[locations[self.__player_index]]
                scores = scores[:player] + scores[player+1:]
            score = self.__operation(scores)

        return self.__comparison(score, self.__value)
