"""
Stores stateful aspects of the program that aren't UI-specific
"""
import json
import traceback
from datetime import datetime
from enum import Enum, auto
from json import JSONDecodeError
from pathlib import Path
from typing import Optional, Sequence

from yaml.scanner import ScannerError

from pente.account import accounts, stats
from pente.ai import ai
from pente.data import data, load_gamestate
from pente.data.Language import Language
from pente.data.data import Data
from pente.data.deserialize import DataError
from pente.game.Game import Game
from pente.game.GameState import GameState
from pente.core.PlayerOutput import PlayerOutput


class _ResponseEnum(Enum):
    """
    Response enums are used to represent to the UI what happened in the Core when the request was made
    """

    # so/73492285
    def __init_subclass__(cls, **kwargs):
        if 'OK' not in cls.__members__:
            raise ValueError("Response enum must have an OK element")

    def __bool__(self):
        return self == self.__class__.OK


class Core:
    def __init__(self, language: Language):
        self.__language: Language = language
        self.__data: Optional[Data] = None
        # Only the packs that were explicitly loaded are remembered
        self.__pack_names: tuple[str, ...] = ()
        self.__accounts: list[str] = []
        self.should_autosave: bool = True
        self.difficulty: float = 0
        self.should_track_stats: bool = False

        self.__game: Optional[Game] = None
        self.__game_pack_names: tuple[str, ...] = ()
        self.__player_output: Optional[PlayerOutput] = None

    @property
    def accounts(self):
        return tuple(self.__accounts)

    @property
    def pack_names(self) -> tuple[str, ...]:
        return self.__pack_names

    @property
    def in_game(self) -> bool:
        return self.__game is not None

    def resolve_account_index(self, account_index: int) -> Optional[str]:
        return None if account_index >= len(self.__accounts) else self.__accounts[account_index]

    class LoginResponse(_ResponseEnum):
        OK = auto()
        NO_SPACE = auto()
        INCORRECT_DETAILS = auto()

    def can_login(self) -> LoginResponse:
        if len(self.__accounts) >= 2:
            return Core.LoginResponse.NO_SPACE
        return Core.LoginResponse.OK

    def login(self, username: str, password: str) -> LoginResponse:
        can = self.can_login()
        if not can:
            return can

        if not accounts.login(username, password):
            return Core.LoginResponse.INCORRECT_DETAILS

        self.__accounts.append(username)
        return Core.LoginResponse.OK

    def logout(self, account_index: int) -> bool:
        if account_index >= len(self.__accounts):
            return False

        self.__accounts.pop(account_index)
        return True

    def load_data(self, names: Sequence[str]) -> bool:
        try:
            self.__data = data.load_packs(names, self.__language)
        except (ScannerError, JSONDecodeError, FileNotFoundError, PermissionError):
            traceback.print_exc()
            return False
        except DataError:
            return False

        self.__pack_names = tuple(names)

        return True

    def __update_players(self):
        self.__player_output.send_update(self.__game, 0, True)

    def __end_game(self):
        if self.should_track_stats:
            username = self.resolve_account_index(self.__game.winner)
            if username is not None:
                wins = stats.get_wins(username, self.__game.win_reason)
                stats.set_wins(username, self.__game.win_reason, wins + 1)

        self.__player_output.send_victory(self.__game, 0, True)
        self.__game = None
        self.__mode = None
        self.__player_output = None

    class LaunchGameResponse(_ResponseEnum):
        OK = auto()
        ALREADY_PLAYING = auto()
        NO_DATA = auto()

    def launch_game(self, player_output: PlayerOutput, gamestate: Optional[GameState] = None) -> LaunchGameResponse:
        if self.__game is not None:
            return Core.LaunchGameResponse.ALREADY_PLAYING
        if self.__data is None:
            return Core.LaunchGameResponse.NO_DATA

        self.__player_output = player_output

        self.__game_pack_names = self.__pack_names

        self.__game = self.__data.to_game(gamestate)
        self.__update_players()
        return Core.LaunchGameResponse.OK

    def ui_concede(self):
        if self.__game is None:
            return False
        else:
            self.__game.winner = (self.__game.next_player + 1) % 2
            self.__game.win_reason = '.concede'
            self.__end_game()
            return True

    class MoveResponse(_ResponseEnum):
        OK = auto()
        NO_GAME = auto()
        ILLEGAL = auto()

    def ui_move(self, coords: tuple[int, ...]) -> MoveResponse:
        if self.__game is None:
            return Core.MoveResponse.NO_GAME

        if not self.__game.can_place(coords):
            return Core.MoveResponse.ILLEGAL

        if self.should_autosave:
            self.save("autosave")

        self.__move(coords)
        return Core.MoveResponse.OK

    def __move(self, coords: tuple[int, ...]):
        self.__game.place(coords)

        if self.__game.winner is not None:
            self.__end_game()
        else:
            self.__update_players()

    def save(self, name: Optional[str] = None) -> Optional[str]:
        if self.__game is None:
            return None

        if name is None:
            name = datetime.now().strftime('%Y-%m-%dT%H-%M-%S.%f')
        name = f"saves/{name}.json"
        save = self.__game.gamestate.to_dict()
        save["datapacks"] = self.__game_pack_names
        save["accounts"] = self.__accounts

        Path("saves").mkdir(parents=True, exist_ok=True)
        with open(name, 'w') as file:
            file.write(json.dumps(save))

        return name

    def load_game(self, player_output: PlayerOutput, file_name: str) -> LaunchGameResponse:
        try:
            gamestate, dct = load_gamestate.load_gamestate(self.__language, file_name)
        except (ScannerError, JSONDecodeError, FileNotFoundError, PermissionError):
            traceback.print_exc()
            return Core.LaunchGameResponse.NO_DATA
        except load_gamestate.LoadGameStateError:
            return Core.LaunchGameResponse.NO_DATA

        if dct["datapacks"] != self.__pack_names:
            self.load_data(dct["datapacks"])

        return self.launch_game(player_output, gamestate)

    class UndoResponse(_ResponseEnum):
        OK = auto()
        NO_GAME = auto()
        AUTOSAVING_OFF = auto()
        NO_DATA = auto()

    def undo(self) -> UndoResponse:
        """
        Silently end the current game and replace it with the autosave, while keeping the same player outputs
        """
        if not self.should_autosave:
            return Core.UndoResponse.AUTOSAVING_OFF
        previous_game = self.__game
        if previous_game is None:
            return Core.UndoResponse.NO_GAME
        self.__game = None

        try:
            load_response = self.load_game(self.__player_output, "autosave")
        finally:
            self.__game = previous_game
        # launch_game will never return ALREADY_PLAYING since we set self.__game = None
        if load_response is Core.LaunchGameResponse.NO_DATA:
            self.__game = previous_game
            return Core.UndoResponse.NO_DATA

        return Core.UndoResponse.OK

    def ai_suggestion(self) -> Optional[tuple[int, ...]]:
        if self.__game is None or self.__game_pack_names != ("pente",):
            return None

        return ai.best_move(self.__game.gamestate, self.difficulty)
