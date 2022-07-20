from collections.abc import Callable

from pente.data import language
from pente.game.GameState import GameState
from pente.game.PlayerController import PlayerController


class CliPlayerController(PlayerController):
    def get_move(self, validator: Callable[[tuple[int, ...]], bool]) -> tuple[int, ...]:
        while True:
            language.print_key("cli.move.prompt")
            inp = input()
            if not all(map(str.isdigit, inp.split())):
                language.print_key("cli.move.bad_format")
            else:
                move = tuple(map(int, inp.split()))
                if not validator(move):
                    language.print_key("cli.move.illegal")
                else:
                    return tuple(map(int, inp.split()))

    def update(self, gamestate: GameState, is_your_turn: bool):
        if is_your_turn:
            print(gamestate.board)
            for player in range(gamestate.num_players):
                language.print_key("cli.score.header", player=str(player))
                for memo, scores in gamestate.scores.items():
                    language.print_key("cli.score.score", memo=memo, value=str(scores[player]))

            language.print_key("cli.your_turn")

    def send_victory(self, winner: int, is_you: bool):
        if is_you:
            language.print_key("cli.victory.you")
        else:
            language.print_key("cli.victory.other", player=str(winner))
