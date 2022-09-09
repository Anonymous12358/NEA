from enum import Enum, auto
from typing import Optional, Sequence

from pente.account import accounts
from pente.data import data
from pente.data.Language import Language
from pente.data.data import Data
from pente.data.deserialize import DataError
from pente.game.Game import Game
from pente.main.PlayerOutput import PlayerOutput


class _ResponseEnum(Enum):
    # TODO Rewrite this more neatly once 3.11 adds `__post_init__`
    def __init__(self, *args):
        if self.name != 'OK' and 'OK' not in self.__class__.__members__:
            raise ValueError("Response enum must have OK as the first element")

    def __bool__(self):
        return self == self.__class__.OK


# TODO May want a separate SuperGame to keep from cluttering this class
class Main:
    class GameMode(Enum):
        HOTSEAT = auto()  # Two players using the same UI
        AI = auto()
        NETWORK_HOST = auto()
        NETWORK_CLIENT = auto()

    def __init__(self, language: Language):
        self.__language: Language = language
        self.__data: Optional[Data] = None
        self.__accounts: list[str] = []

        self.__game: Optional[Game] = None
        self.__mode: Optional[Main.GameMode] = None
        self.__player_outputs: Optional[tuple[PlayerOutput, PlayerOutput]] = None

    class LoginResponse(_ResponseEnum):
        OK = auto()
        NO_SPACE = auto()
        INCORRECT_DETAILS = auto()

    def can_login(self) -> LoginResponse:
        if len(self.__accounts) >= 2:
            return Main.LoginResponse.NO_SPACE
        return Main.LoginResponse.OK

    def login(self, username: str, password: str) -> LoginResponse:
        can = self.can_login()
        if not can:
            return can

        if not accounts.login(username, password):
            return Main.LoginResponse.INCORRECT_DETAILS

        self.__accounts.append(username)
        return Main.LoginResponse.OK

    def load_data(self, names: Sequence[str]) -> bool:
        try:
            self.__data = data.load_packs(names, self.__language)
        except DataError:
            return False

        return True

    def __update_players(self):
        if self.__mode is Main.GameMode.HOTSEAT:
            self.__player_outputs[0].update(self.__game, 0, True)
        else:
            for i, player_output in enumerate(self.__player_outputs):
                player_output.update(self.__game, i, False)

    def __end_game(self):
        if self.__mode is Main.GameMode.HOTSEAT:
            self.__player_outputs[0].send_victory(self.__game, 0, True)
        else:
            for i, player_output in enumerate(self.__player_outputs):
                player_output.send_victory(self.__game, i, False)
        self.__game = None
        self.__mode = None
        self.__player_outputs = None

    class LaunchGameResponse(_ResponseEnum):
        OK = auto()
        ALREADY_PLAYING = auto()
        NO_DATA = auto()

    def can_launch_game(self) -> LaunchGameResponse:
        if self.__game is not None:
            return Main.LaunchGameResponse.ALREADY_PLAYING
        if self.__data is None:
            return Main.LaunchGameResponse.NO_DATA
        return Main.LaunchGameResponse.OK

    def launch_game(self, player_outputs: tuple[PlayerOutput, PlayerOutput]) -> LaunchGameResponse:
        can = self.can_launch_game()
        if not can:
            return can

        # TODO When more player outputs exist, blablabla
        self.__player_outputs = player_outputs
        self.__mode = Main.GameMode.HOTSEAT

        self.__game = self.__data.to_game()
        self.__update_players()
        return Main.LaunchGameResponse.OK

    class MoveResponse(_ResponseEnum):
        OK = auto()
        NO_GAME = auto()
        NOT_TURN = auto()
        ILLEGAL = auto()

    def __get_ui_player(self):
        if self.__mode in (Main.GameMode.AI, Main.GameMode.NETWORK_HOST):
            return 0
        elif self.__mode is Main.GameMode.NETWORK_HOST:
            return 1
        else:
            return self.__game.next_player

    def can_ui_move(self, coords: tuple[int, ...]) -> MoveResponse:
        if self.__game is None:
            return Main.MoveResponse.NO_GAME

        if self.__game.next_player != self.__get_ui_player():
            return Main.MoveResponse.NOT_TURN

        if not self.__game.can_place(coords):
            return Main.MoveResponse.ILLEGAL
        return Main.MoveResponse.OK

    def ui_move(self, coords: tuple[int, ...]) -> MoveResponse:
        can = self.can_ui_move(coords)
        if not can:
            return can
        self.__move(self.__get_ui_player(), coords)
        return Main.MoveResponse.OK

    def __move(self, player: int, coords: tuple[int, ...]):
        self.__game.place(coords, player)

        if self.__game.winner is not None:
            self.__end_game()
        else:
            self.__update_players()
