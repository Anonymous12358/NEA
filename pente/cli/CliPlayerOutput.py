"""
Implementation of PlayerOutput for the command line
"""

from __future__ import annotations

from pente.data.Language import Language
from pente.game.Game import Game
from pente.main.PlayerOutput import PlayerOutput


class CliPlayerOutput(PlayerOutput):
    def __init__(self, language: Language):
        self.__language = language

    def update(self, game: Game, your_index: int, is_hotseat: bool):
        print(game.gamestate.board)

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
            self.__language.print_key("cli.output.victory.who", player=str(game.next_player))
        else:
            self.__language.print_key("cli.output.victory.you")

        print(game.gamestate.board)
