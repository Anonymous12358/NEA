from collections.abc import Callable

from pente.data.Language import Language
from pente.game.GameState import GameState
from pente.game.PlayerController import PlayerController


class CliPlayerController(PlayerController):
    def __init__(self, language: Language):
        self.__language = language

    def get_move(self, validator: Callable[[tuple[int, ...]], bool]) -> tuple[int, ...]:
        while True:
            self.__language.print_key("cli.move.prompt")
            inp = input()
            if not all(map(str.isdigit, inp.split())):
                self.__language.print_key("cli.move.bad_format")
            else:
                move = tuple(map(int, inp.split()))
                if not validator(move):
                    self.__language.print_key("cli.move.illegal")
                else:
                    return tuple(map(int, inp.split()))

    def update(self, gamestate: GameState, is_your_turn: bool):
        if is_your_turn:
            print(gamestate.board)
            for player in range(gamestate.num_players):
                self.__language.print_key("cli.score.header", player=str(player))
                for memo, scores in gamestate.scores.items():
                    self.__language.print_key("cli.score.score", memo=memo, value=str(scores[player]))

            self.__language.print_key("cli.your_turn")

    def send_victory(self, winner: int, is_you: bool):
        if is_you:
            self.__language.print_key("cli.victory.you")
        else:
            self.__language.print_key("cli.victory.other", player=str(winner))
