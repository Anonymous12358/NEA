from collections.abc import Sequence

from pente.game.rule.Applicable import Applicable
from pente.game.GameState import GameState


class BoardAction(Applicable):
    def __init__(self, location_index: int, player_index: int):
        self.__location_index = location_index
        self.__player_index = player_index

    def apply(self, gamestate: GameState, locations: Sequence[tuple[int, ...]], center: tuple[int, ...]):
        player = self.resolve_player_index(gamestate, locations, center, self.__player_index)
        location = locations[self.__location_index]
        gamestate.board[location] = player
