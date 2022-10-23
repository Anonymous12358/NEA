"""
The command line interface
"""

import getpass
import inspect

from pente.account import accounts
from pente.cli.CliPlayerOutput import CliPlayerOutput
from pente.data.Language import Language
from pente.main.Main import Main


class Cli:
    def __init__(self):
        self.__language = Language(["en_UK"])
        self.__main = Main(self.__language)
        self.__COMMANDS = {
            "help": self.help,
            "register": self.register,
            "login": self.login,
            "data": self.load_data,
            "play": self.launch_game,
            "move": self.move,
        }

    def mainloop(self):
        while True:
            self.execute_command(*input(">>> ").split(" "))

    def execute_command(self, *words: str):
        command, *args = words
        if command in self.__COMMANDS.keys():
            # Determine if the provided arguments are compatible with the function
            func = self.__COMMANDS[command]
            params = list(inspect.signature(func).parameters.values())
            is_varargs = len(params) > 0 and params[-1].kind == params[-1].VAR_POSITIONAL
            is_compatible = len(args) == len(params) or is_varargs and len(args) >= len(params) - 1
            if not is_compatible:
                self.__language.print_key("cli.invalid_command")
            else:
                func(*args)
        else:
            self.__language.print_key("cli.unknown_command")

    def help(self):
        for name, func in self.__COMMANDS.items():
            print(f"{name} " + " ".join(f"<{param}>" for param in inspect.signature(func).parameters))

    def register(self, username: str):
        password = getpass.getpass(self.__language.resolve_key("cli.login.password_prompt"))
        if accounts.register(username, password) is None:
            self.__language.print_key("cli.register.duplicate_username")
        else:
            self.__language.print_key("cli.register.ok")

    def login(self, username: str):
        if self.__main.can_login() == Main.LoginResponse.NO_SPACE:
            self.__language.print_key("cli.login.no_space")
            return

        password = getpass.getpass(self.__language.resolve_key("cli.login.password_prompt"))
        response = self.__main.login(username, password)
        if response is Main.LoginResponse.INCORRECT_DETAILS:
            self.__language.print_key("cli.login.incorrect_details")
        else:
            self.__language.print_key("cli.login.ok")

    def load_data(self, *names: str) -> bool:
        response = self.__main.load_data(names)
        if not response:
            self.__language.print_key("cli.load_data.error")
        return response

    def launch_game(self, *names: str):
        # If packs are specified, load them
        if names:
            if not self.load_data(*names):
                # If packs can't be loaded, abort
                self.__language.print_key("cli.launch.no_data")
                return

        response = self.__main.launch_game((CliPlayerOutput(self.__language), CliPlayerOutput(self.__language)))
        if response is Main.LaunchGameResponse.ALREADY_PLAYING:
            self.__language.print_key("cli.launch.already_playing")
        elif response is Main.LaunchGameResponse.NO_DATA:
            # Load Pente, then reattempt
            if not self.load_data("pente"):
                self.__language.print_key("cli.launch.no_data")
                return
            self.__main.launch_game((CliPlayerOutput(self.__language), CliPlayerOutput(self.__language)))

    def move(self, *coords: str):
        try:
            coords = tuple(map(int, coords))
        except ValueError:
            self.__language.print_key("cli.move.bad_format")

        response = self.__main.ui_move(coords)
        if response is Main.MoveResponse.NO_GAME:
            self.__language.print_key("cli.move.no_game")
        elif response is Main.MoveResponse.NOT_TURN:
            self.__language.print_key("cli.move.not_turn")
        elif response is Main.MoveResponse.ILLEGAL:
            self.__language.print_key("cli.move.illegal")
