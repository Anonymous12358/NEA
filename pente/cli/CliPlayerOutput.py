"""
Implementation of PlayerOutput for the command line
"""

from __future__ import annotations

from typing import Optional

from pente.data.Language import Language
from pente.game.Board import Board, EMPTY
from pente.game.Game import Game
from pente.core.PlayerOutput import PlayerOutput


class CliPlayerOutput(PlayerOutput):
    def __init__(self, language: Language, colors: tuple[str, str]):
        self.__language = language
        self.__colors = colors

    def send_update(self, game: Game, your_index: int, is_hotseat: bool):
        print(self.__stringify_board(game.gamestate.board))

        displayable_scores = game.get_displayable_scores()
        if len(displayable_scores) == 1:
            self.__language.print_key("cli.output.score.one_score", display_name=displayable_scores[0][0],
                                      values=" ".join(map(str, displayable_scores[0][1])))
        elif len(displayable_scores) > 1:
            for player in range(len(displayable_scores[0][1])):
                self.__language.print_key("cli.output.score.header", player=str(player))
                for display_name, scores in displayable_scores:
                    self.__language.print_key("cli.output.score.score", display_name=display_name,
                                              value=str(scores[player]))

        if is_hotseat or game.next_player != your_index:
            self.__language.print_key("cli.output.turn.who", player=str(game.next_player))
        else:
            self.__language.print_key("cli.output.turn.you")

    def send_victory(self, game: Game, your_index: int, is_hotseat: bool):
        if is_hotseat or game.winner != your_index:
            self.__language.print_key("cli.output.victory.who", player=str(game.winner))
        else:
            self.__language.print_key("cli.output.victory.you")

        print(self.__stringify_board(game.gamestate.board))

    def __stringify_board(self, board: Board):
        result = ""
        # Column numbers
        if len(board.dimensions) <= 2:
            result += " "
            for i in range(board.dimensions[-1]):
                result += str(i % 10)
            result += "\n"
        # Row numbers
        if len(board.dimensions) == 2:
            result += "0"

        for coords, tile in board.enumerate():
            # Add new lines when moving in dimensions beyond the first
            if any(coords):
                for ordinate in coords[::-1]:
                    if ordinate == 0:
                        result += "\n"
                        # Row numbers
                        if len(board.dimensions) == 2:
                            result += str(coords[0] % 10)
                    else:
                        break

            if tile == EMPTY:
                if result and result[-1] == "-":
                    result += "-"
                else:
                    result += '\x1b[0m-'
            else:
                char = chr(tile + 48)
                if result and result[-1] == char and result[-2] != "\n":
                    result += char
                else:
                    result += f'\x1b[{self.__colors[tile]}m{chr(tile + 48)}'

        result += '\x1b[0m'
        return result
