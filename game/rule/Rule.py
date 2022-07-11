from collections.abc import Sequence
from enum import auto, Enum
from itertools import chain

from game.Board import Board
from game.rule.BoardAction import BoardAction
from game.rule.Condition import Condition
from game.GameState import GameState
from game.rule.Pattern import Pattern
from game.rule.ScoreAction import ScoreAction


class Rule:
    class Mode(Enum):
        ONE = auto()
        HALF = auto()
        ALL = auto()

    def __init__(self, pattern: Pattern, multimatch_mode: Mode, conditions: Sequence[Condition],
                 score_actions: Sequence[ScoreAction], board_actions: Sequence[BoardAction]):
        self.__pattern = pattern
        self.__multimatchmode = multimatch_mode
        self.__conditions = conditions
        self.__score_actions = score_actions
        self.__board_actions = board_actions

    def invoke(self, gamestate: GameState, center: tuple[int, ...], lines: Sequence[Board.Line]):
        matched_directions = set()
        matches = []
        for i, line in enumerate(lines):
            if self.__multimatchmode == Rule.Mode.HALF and len(lines) - i - 1 in matched_directions:
                continue

            match = self.__pattern.match_line(line)
            if match is not None:
                does_satisfy = all(condition.apply(gamestate, match, center) for condition in self.__conditions)
                if does_satisfy:
                    matched_directions.add(i)
                    matches.append(match)
                    if self.__multimatchmode == Rule.Mode.ONE:
                        break

        for action in chain(self.__score_actions, self.__board_actions):
            for match in matches:
                action.apply(gamestate, match, center)
