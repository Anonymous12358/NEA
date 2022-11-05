"""
The command line interface
"""
import getpass
import inspect
from collections.abc import Callable
from functools import partial

from pente.account import accounts, stats
from pente.cli.CliPlayerOutput import CliPlayerOutput
from pente.data.Language import Language
from pente.main.Main import Main

_COMMANDS = {}


# Decorator to register command in _COMMANDS
def command(name_or_func):
    # Called as @command
    if isinstance(name_or_func, Callable):
        _COMMANDS[name_or_func.__name__] = name_or_func.__name__
        return name_or_func
    # Called as @command(name)
    else:
        def decorator(func):
            _COMMANDS[name_or_func] = func.__name__
            return func
        return decorator


class Cli:
    # Maps color names (which are parts of language keys) to color codes (part of the ANSI escape to set the color)
    __COLORS = {
        "default": '0',
        "black": '30',
        "red": '31',
        "green": '32',
        "yellow": '33',
        "blue": '34',
        "magenta": '35',
        "cyan": '36',
        "white": '37',
        "bright_black": '30',
        "bright_red": '31',
        "bright_green": '32',
        "bright_yellow": '33',
        "bright_blue": '34',
        "bright_magenta": '35',
        "bright_cyan": '36',
        "bright_white": '37',
    }

    def __init__(self):
        self.__language = Language(["en_UK"], partial(print, end=""))
        self.__main = Main(self.__language)
        self.__COMMANDS = {}
        for command_name, func_name in _COMMANDS.items():
            self.__COMMANDS[command_name] = getattr(self, func_name)

        self.__COLOR_ALIASES = {}
        for color_name, color_code in Cli.__COLORS.items():
            self.__COLOR_ALIASES[self.__language.resolve_key(f"color.{color_name}")] = color_code

    def mainloop(self):
        while True:
            self.__language.print_key("cli.prompt")
            self.execute_command(*input().split(" "))

    def execute_command(self, *words: str):
        command_name, *args = words
        if command_name in self.__COMMANDS.keys():
            # Determine if the provided arguments are compatible with the function
            func = self.__COMMANDS[command_name]
            params = list(inspect.signature(func).parameters.values())
            is_varargs = len(params) > 0 and params[-1].kind == params[-1].VAR_POSITIONAL
            is_compatible = len(args) == len(params) or is_varargs and len(args) >= len(params) - 1
            if not is_compatible:
                self.__language.print_key("cli.invalid_command")
            else:
                func(*args)
        else:
            self.__language.print_key("cli.unknown_command")

    @command
    def help(self):
        for name, func in self.__COMMANDS.items():
            print(f"{name} " + " ".join(f"<{param}>" for param in inspect.signature(func).parameters))

    @command
    def register(self, username: str):
        self.__language.print_key("cli.login.password_prompt")
        password = getpass.getpass("")
        if accounts.register(username, password) is None:
            self.__language.print_key("cli.register.duplicate_username")
        else:
            self.__language.print_key("cli.register.ok")

    @command
    def login(self, username: str):
        if self.__main.can_login() == Main.LoginResponse.NO_SPACE:
            self.__language.print_key("cli.login.no_space")
            return

        self.__language.print_key("cli.login.password_prompt")
        password = getpass.getpass("")
        response = self.__main.login(username, password)
        if response is Main.LoginResponse.INCORRECT_DETAILS:
            self.__language.print_key("cli.login.incorrect_details")
        else:
            self.__language.print_key("cli.login.ok")

    @command
    def logout(self, username: str):
        response = self.__main.logout(username)
        if not response:
            self.__language.print_key("cli.logout.not_logged_in")
        else:
            self.__language.print_key("cli.logout.ok")

    @command("listaccounts")
    def list_accounts(self):
        logged_in_accounts = self.__main.accounts
        if len(logged_in_accounts) == 0:
            self.__language.print_key("cli.list_accounts.none")
        if len(logged_in_accounts) == 1:
            self.__language.print_key("cli.list_accounts.one", account=logged_in_accounts[0])
        if len(logged_in_accounts) == 2:
            self.__language.print_key("cli.list_accounts.two", account1=logged_in_accounts[0],
                                      account2=logged_in_accounts[1])

    def __get_color(self, account_index: int):
        username = self.__main.resolve_account_index(account_index)
        if username is None:
            return '0'
        else:
            return accounts.get_color(username)

    @command("color")
    @command("colour")
    def set_color(self, account_index: str, color: str):
        try:
            account_index = int(account_index)
        except ValueError:
            self.__language.print_key("cli.set_color.bad_format")
            return

        username = self.__main.resolve_account_index(account_index)
        if username is None:
            self.__language.print_key("cli.set_color.not_logged_in")
            return

        accounts.set_color(username, self.__COLOR_ALIASES[color])
        self.__language.print_key("cli.set_color.ok")

    @command("data")
    def load_data(self, *names: str) -> bool:
        response = self.__main.load_data(names)
        if not response:
            self.__language.print_key("cli.load_data.error")
        return response

    @command("listdata")
    def list_datapacks(self):
        packs = self.__main.pack_names
        if len(packs) == 0:
            self.__language.print_key("cli.list_datapacks.none")
        else:
            self.__language.print_key("cli.list_datapacks.some", packs=" ".join(packs))

    @command("play")
    def launch_game(self, *names: str):
        # If packs are specified, load them
        if names:
            if not self.load_data(*names):
                # If packs can't be loaded, abort
                self.__language.print_key("cli.launch.no_data")
                return

        colors = self.__get_color(0), self.__get_color(1)
        player_outputs = CliPlayerOutput(self.__language, colors), CliPlayerOutput(self.__language, colors)
        response = self.__main.launch_game(player_outputs)
        if response is Main.LaunchGameResponse.ALREADY_PLAYING:
            self.__language.print_key("cli.launch.already_playing")
        elif response is Main.LaunchGameResponse.NO_DATA:
            # Load Pente, then reattempt
            if not self.load_data("pente"):
                self.__language.print_key("cli.launch.no_data")
                return
            self.__main.launch_game(player_outputs)

    @command
    def concede(self):
        self.__language.print_key("cli.confirm.concede")
        if input().lower() != "y":
            return

        response = self.__main.ui_concede()
        if not response:
            self.__language.print_key("cli.concede.no_game")

    @command
    def move(self, *coords: str):
        try:
            coords = tuple(map(int, coords))
        except ValueError:
            self.__language.print_key("cli.move.bad_format")
            return

        response = self.__main.ui_move(coords)
        if response is Main.MoveResponse.NO_GAME:
            self.__language.print_key("cli.move.no_game")
        elif response is Main.MoveResponse.NOT_TURN:
            self.__language.print_key("cli.move.not_turn")
        elif response is Main.MoveResponse.ILLEGAL:
            self.__language.print_key("cli.move.illegal")

    @command
    def save(self):
        file_name = self.__main.save()
        if file_name is not None:
            self.__language.print_key("cli.save_game.ok", file_name=file_name)
        else:
            self.__language.print_key("cli.save_game.no_game")

    @command("load")
    def load_game(self, file_name: str):
        colors = self.__get_color(0), self.__get_color(1)
        player_outputs = CliPlayerOutput(self.__language, colors), CliPlayerOutput(self.__language, colors)
        response = self.__main.load_game(player_outputs, file_name)
        if response is Main.LaunchGameResponse.ALREADY_PLAYING:
            self.__language.print_key("cli.launch.already_playing")
        elif response is Main.LaunchGameResponse.NO_DATA:
            self.__language.print_key("cli.launch.no_data")

    @command("autosave")
    def toggle_autosave(self):
        self.__main.should_autosave = not self.__main.should_autosave
        mode = self.__language.resolve_key("cli.toggle." + ("on" if self.__main.should_autosave else "off"))
        self.__language.print_key("cli.toggle_autosave", mode=mode)

    @command
    def undo(self):
        response = self.__main.undo()
        if response is Main.UndoResponse.AUTOSAVING_OFF:
            self.__language.print_key("cli.undo.autosaving_off")
        elif response is Main.UndoResponse.NO_GAME:
            self.__language.print_key("cli.undo.no_game")
        elif response is Main.UndoResponse.NO_DATA:
            self.__language.print_key("cli.undo.no_data")

    @command
    def exit(self):
        self.__language.print_key("cli.confirm.exit")
        if input().lower() == "y":
            raise SystemExit

    @command
    def difficulty(self, difficulty: str):
        try:
            difficulty = float(difficulty)
        except ValueError:
            self.__language.print_key("cli.difficulty.bad_format")
            return

        self.__main.difficulty = difficulty
        self.__language.print_key("cli.difficulty.ok")

    @command("aimove")
    def ai_suggestion(self):
        response = self.__main.ai_suggestion()
        if response is None:
            self.__language.print_key("cli.ai_suggestion.invalid")
        else:
            self.__language.print_key("cli.ai_suggestion.ok", move=" ".join(map(str, response)))

    @command("trackstats")
    def toggle_track_stats(self):
        self.__main.should_track_stats = not self.__main.should_track_stats
        mode = self.__language.resolve_key("cli.toggle." + ("on" if self.__main.should_track_stats else "off"))
        self.__language.print_key("cli.toggle_track_stats", mode=mode)

    @command("showstats")
    def show_stats(self, account_index: str, win_reason: str):
        try:
            account_index = int(account_index)
        except ValueError:
            self.__language.print_key("cli.show_stats.bad_format")
            return

        username = self.__main.resolve_account_index(account_index)
        wins = stats.get_wins(username, win_reason)
        self.__language.print_key("cli.show_stats.ok", wins=str(wins))

    @command("clearstats")
    def clear_stats(self, account_index: str):
        try:
            account_index = int(account_index)
        except ValueError:
            self.__language.print_key("cli.clear_stats.bad_format")
            return

        username = self.__main.resolve_account_index(account_index)
        stats.clear_wins(username)
        self.__language.print_key("cli.clear_stats.ok")
