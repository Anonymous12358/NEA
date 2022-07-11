from collections.abc import Sequence

from game.Board import Board
from game.GameState import GameState
from game.rule.Rule import Rule

NUM_PLAYERS = 2


class Game:
    def __init__(self, dimensions: tuple[int, ...], rules: Sequence[Rule], memos: Sequence[str],
                 win_thresholds: dict[str, int]):
        self.__gamestate = GameState(Board(dimensions), memos, NUM_PLAYERS)
        self.__rules = rules
        self.__win_thresholds = win_thresholds
        self.winner = -1

    def place(self, color: int, coords: tuple[int, ...]):
        """
        Take a turn by placing a tile on the board, applying rules, and checking victory
        :param color: The color of the tile to place
        :param coords: The coordinates at which to place
        """
        # Place tile
        self.__gamestate.board[coords] = color

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
