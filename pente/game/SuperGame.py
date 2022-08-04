import itertools
from collections.abc import Sequence
from functools import partial

from pente.game.Game import Game
from pente.game.PlayerController import PlayerController


class SuperGame:
    def __init__(self, game: Game, player_controllers: Sequence[PlayerController]):
        if len(player_controllers) != game.gamestate.num_players:
            raise ValueError("Invalid number of player controllers")

        self.__game = game
        self.__player_controllers = player_controllers

    def run(self):
        for turn in itertools.cycle(range(self.__game.gamestate.num_players)):
            for i, player_controller in enumerate(self.__player_controllers):
                player_controller.update(self.__game.gamestate.board, self.__game.get_displayable_scores(), i == turn)

            coords = self.__player_controllers[turn].get_move(partial(self.__game.can_place, player=turn))
            self.__game.place(coords, turn)

            if self.__game.winner is not None:
                for i, player_controller in enumerate(self.__player_controllers):
                    player_controller.send_victory(self.__game.gamestate, self.__game.winner, i == self.__game.winner)
                break
