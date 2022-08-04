from collections.abc import Callable, Sequence

from pente.data.Language import Language
from pente.game.Board import Board
from pente.game.GameState import GameState
from pente.game.PlayerController import PlayerController


class CliPlayerController(PlayerController):
    def __init__(self, name: str, language: Language):
        self.__name = name
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

    def update(self, board: Board, displayable_scores: Sequence[tuple[str, Sequence[int]]], is_your_turn: bool):
        if not is_your_turn:
            return

        self.__language.print_key("cli.name", name=self.__name)
        print(board)

        if len(displayable_scores) == 1:
            self.__language.print_key("cli.score.one_score", display_name=displayable_scores[0][0],
                                      values=" ".join(map(str, displayable_scores[0][1])))
        elif len(displayable_scores) > 1:
            for player in range(len(displayable_scores[0][1])):
                self.__language.print_key("cli.score.header", player=str(player))
                for display_name, scores in displayable_scores:
                    self.__language.print_key("cli.score.score", display_name=display_name, value=str(scores[player]))

        self.__language.print_key("cli.your_turn")

    def send_victory(self, gamestate: GameState, winner: int, is_you: bool):
        if is_you:
            self.__language.print_key("cli.victory.you", player=str(winner))
        else:
            self.__language.print_key("cli.victory.other", player=str(winner))
        print(gamestate.board)
