"""
Interfaces between the UI and the features, delegating UI requests to the appropriate class
"""
import json
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Sequence

from pente.account import accounts
from pente.data import data, load_gamestate
from pente.data.Language import Language
from pente.data.data import Data
from pente.data.deserialize import DataError
from pente.game.Game import Game
from pente.game.GameState import GameState
from pente.main.PlayerOutput import PlayerOutput


class _ResponseEnum(Enum):
    # so/73492285
    """
    Response enums are used to represent to the UI what happened in the Main when the request was made
    """

    def __init_subclass__(cls, **kwargs):
        if 'OK' not in cls.__members__:
            raise ValueError("Response enum must have an OK element")

    def __bool__(self):
        return self == self.__class__.OK


# TODO Rename this class
class Main:
    class GameMode(Enum):
        HOTSEAT = auto()  # Two players using the same UI
        AI = auto()
        NETWORK_HOST = auto()
        NETWORK_CLIENT = auto()

    def __init__(self, language: Language):
        self.__language: Language = language
        self.__data: Optional[Data] = None
        self.__pack_names: Sequence[str] = []
        self.__accounts: list[str] = []

        self.__game: Optional[Game] = None
        self.__game_pack_names: Sequence[str] = []
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

        self.__pack_names = names

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

    def launch_game(self, player_outputs: tuple[PlayerOutput, PlayerOutput], gamestate: Optional[GameState] = None
                    ) -> LaunchGameResponse:
        can = self.can_launch_game()
        if not can:
            return can

        self.__player_outputs = player_outputs
        # TODO When more player outputs exist, set the mode correctly
        self.__mode = Main.GameMode.HOTSEAT

        self.__game_pack_names = self.__pack_names

        self.__game = self.__data.to_game(gamestate)
        self.__update_players()
        return Main.LaunchGameResponse.OK

    def ui_concede(self):
        if self.__game is None:
            return False
        else:
            self.__game.winner = (self.__get_ui_player() + 1) % 2
            self.__end_game()
            return True

    class MoveResponse(_ResponseEnum):
        OK = auto()
        NO_GAME = auto()
        NOT_TURN = auto()
        ILLEGAL = auto()

    def __get_ui_player(self):
        """
        Get which player index the UI is currently controlling. For playing on a network or against AI, this is
        constant; for hotseat play, this is the next player in turn order.
        """
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

    def save(self, name: Optional[str] = None) -> Optional[str]:
        if self.__game is None:
            return None

        if name is None:
            name = datetime.now().strftime('saves/%Y-%m-%dT%H-%M-%S.%f.json')
        save = self.__game.gamestate.to_dict()
        save["datapacks"] = self.__game_pack_names
        save["accounts"] = self.__accounts

        Path("saves").mkdir(parents=True, exist_ok=True)
        with open(name, 'w') as file:
            file.write(json.dumps(save))

        return name

    def load_game(self, player_outputs: tuple[PlayerOutput, PlayerOutput], file_name: str) -> LaunchGameResponse:
        try:
            gamestate, dct = load_gamestate.load_gamestate(self.__language, file_name)
        except load_gamestate.LoadGameStateError:
            return Main.LaunchGameResponse.NO_DATA

        self.load_data(dct["datapacks"])

        return self.launch_game(player_outputs, gamestate)
