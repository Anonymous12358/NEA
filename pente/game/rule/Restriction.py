from __future__ import annotations

from collections.abc import Collection, Sequence
from typing import Optional

from pente.game.Board import Board
from pente.game.GameState import GameState
from pente.game.rule.Condition import Condition
from pente.game.rule.Pattern import Pattern
from pente.game.rule.Rule import Rule


class DisjunctionRestriction:
    def __init__(self, conjunctions: Collection[Collection[Restriction]]):
        self.__conjunctions = conjunctions

    def invoke(self, gamestate: GameState, center: tuple[int, ...], lines: Sequence[Board.Line]) -> bool:
        return any(all(restriction.invoke(gamestate, center, lines) for restriction in conjunction)
                   for conjunction in self.__conjunctions)


class PatternRestriction(Rule):
    """
    A version of Rule that cannot apply actions
    """
    def __init__(self, pattern: Pattern, conditions: Sequence[Condition], active_player: Optional[int] = None,
                 negate: bool = False):
        super().__init__(pattern, Rule.Mode.ONE, conditions, [], [], active_player)
        self.__negate = negate

    def invoke(self, gamestate: GameState, center: tuple[int, ...], lines: Sequence[Board.Line]) -> bool:
        result = self.__negate != super().invoke(gamestate, center, lines)
        return result


Restriction = DisjunctionRestriction | PatternRestriction
