from collections.abc import Sequence
from enum import auto, Enum

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

    def apply(self, gamestate: GameState, center: tuple[int, ...]):
        lines = gamestate.board.get_lines(center)
        matches = {}
        for i, line in enumerate(lines):
            if self.__multimatchmode == Rule.Mode.HALF and len(lines) - i - 1 in matches.keys():
                continue

            match = self.__pattern.match_line(line)
            if match is not None:
                does_satisfy = all(condition.apply(gamestate, match, center) for condition in self.__conditions)
                if does_satisfy:
                    matches[i] = match
                    if self.__multimatchmode == Rule.Mode.ONE:
                        break

        for score_action in self.__score_actions:
            for match in matches.values():
                score_action.apply(gamestate, match, center)
        for board_action in self.__board_actions:
            for match in matches.values():
                board_action.apply(gamestate, match, center)
