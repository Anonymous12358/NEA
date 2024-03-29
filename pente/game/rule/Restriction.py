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

    ############################################################################################################
    # GROUP A SKILL: RECURSIVE ALGORITHMS                                                                      #
    # A DisjunctionRestriction can have any number of children which may themselves be DisjunctionRestrictions #
    # The truth value of a DisjunctionRestriction is therefore determined recursively                          #
    # The base case here is based on polymorphism - we recurse iff a child is a DisjunctionRestriction         #
    ############################################################################################################
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


#######################################################################################################################
# GROUP A SKILL: OTHER TECHNICAL SKILL                                                                                #
# Defined Restriction as a sum type of two classes, to avoid the need for an abstract class which would associate the #
# classes but not define functionality                                                                                #
#######################################################################################################################
Restriction = DisjunctionRestriction | PatternRestriction
