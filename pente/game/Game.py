from collections.abc import Sequence
from typing import Optional, Self

from pente.game.Board import Board, EMPTY
from pente.game.GameState import GameState
from pente.game.Score import Score
from pente.game.rule.Restriction import Restriction
from pente.game.rule.Rule import Rule

# From here down, the game works with more than two players. Those idiots at UX just didn't know what to do with it.
NUM_PLAYERS = 2


class Game:
    def __init__(self, dimensions: tuple[int, ...], scores: Sequence[Score], restrictions: Sequence[Restriction],
                 rules: Sequence[Rule]):
        self.__gamestate = GameState(Board(dimensions), [score.name for score in scores], NUM_PLAYERS)
        self.__scores = scores
        self.__restrictions = restrictions
        self.__rules = rules
        self.winner = None
        self.win_reason = None

    @classmethod
    def from_gamestate(cls, gamestate: GameState, dimensions: tuple[int, ...], scores: Sequence[Score],
                       restrictions: Sequence[Restriction], rules: Sequence[Rule]) -> Self:
        result = cls(dimensions, scores, restrictions, rules)
        result.__gamestate = gamestate
        return result

    @property
    def gamestate(self) -> GameState:
        return self.__gamestate

    @property
    def next_player(self) -> int:
        return self.gamestate.next_player

    def get_displayable_scores(self) -> list[tuple[str, list[int]]]:
        """
        :returns: A list of tuples of (display name, list of value of the score for each player) for each score
        """
        return [(score.display_name, self.__gamestate.scores[score.name])
                for score in self.__scores if score.display_name is not None]

    def can_place(self, coords: tuple[int, ...], player: Optional[int] = None) -> bool:
        """
        Check if a move is legal based on:
        - Whether or not the coordinates are within the grid
        - Whether or not a stone is currently there
        - Restrictions defined by data packs
        :param coords: The coordinates at which to consider placing
        :param player: The color of the tile to consider placing
        """
        # Save the previous active player so that checking can_place doesn't affect the active player
        saved_active_player = self.__gamestate.active_player
        if player is None:
            player = self.next_player
        self.__gamestate.active_player = player

        try:
            # Wrong number of dimensions
            if len(coords) != len(self.__gamestate.board.dimensions):
                return False

            # Out of bounds
            if not all(0 <= ordinate < dimension
                       for ordinate, dimension in zip(coords, self.__gamestate.board.dimensions)):
                return False

            # Already a tile there
            if self.__gamestate.board[coords] != EMPTY:
                return False

            # Check restrictions
            if not self.__restrictions:
                return True
            lines = self.__gamestate.board.get_lines(coords)
            return all(restriction.invoke(self.__gamestate, coords, lines) for restriction in self.__restrictions)
        finally:
            self.__gamestate.active_player = saved_active_player

    def place(self, coords: tuple[int, ...], player: Optional[int] = None):
        """
        Take a turn by placing a tile on the board, applying rules, and checking victory
        :param coords: The coordinates at which to place
        :param player: The color of the tile to place; if None, use the next player in turn order
        """
        if player is None:
            player = self.next_player
        if not self.can_place(coords, player):
            return

        self.__gamestate.active_player = player

        # Place tile
        self.__gamestate.board[coords] = player

        # Apply rules
        lines = self.__gamestate.board.get_lines(coords)
        for rule in self.__rules:
            rule.invoke(self.__gamestate, coords, lines)

        # Check victory conditions
        for score in self.__scores:
            if score.win_threshold is not None:
                for player in range(NUM_PLAYERS):
                    if self.__gamestate.scores[score.name][player] >= score.win_threshold:
                        self.winner = player
                        self.win_reason = score.name
                        break
                else:
                    continue
                break
