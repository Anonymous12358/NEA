from collections.abc import Sequence
from typing import Optional

from pente.game.Board import Board, EMPTY
from pente.game.GameState import GameState
from pente.game.rule.Restriction import Restriction
from pente.game.rule.Rule import Rule

NUM_PLAYERS = 2


class Game:
    def __init__(self, dimensions: tuple[int, ...], restrictions: Sequence[Restriction], rules: Sequence[Rule],
                 memos: Sequence[str], win_thresholds: dict[str, int]):
        self.__gamestate = GameState(Board(dimensions), memos, NUM_PLAYERS)
        self.__restrictions = restrictions
        self.__rules = rules
        self.__win_thresholds = win_thresholds
        self.winner = None

    @property
    def gamestate(self):
        return self.__gamestate

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
            player = (saved_active_player + 1) % NUM_PLAYERS
        self.__gamestate.active_player = player

        try:
            if len(coords) != len(self.__gamestate.board.dimensions):
                return False

            if not all(0 <= ordinate < dimension
                       for ordinate, dimension in zip(coords, self.__gamestate.board.dimensions)):
                return False

            if self.__gamestate.board[coords] != EMPTY:
                return False

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
            player = (self.__gamestate.active_player + 1) % NUM_PLAYERS
        self.__gamestate.active_player = player

        if not self.can_place(coords, player):
            return

        # Place tile
        self.__gamestate.board[coords] = player

        # Apply rules
        lines = self.__gamestate.board.get_lines(coords)
        for rule in self.__rules:
            rule.invoke(self.__gamestate, coords, lines)

        # Check victory conditions
        for memo, threshold in self.__win_thresholds.items():
            for player in range(NUM_PLAYERS):
                if self.__gamestate.scores[memo][player] >= threshold:
                    self.winner = player
                    break
            else:
                continue
            break
