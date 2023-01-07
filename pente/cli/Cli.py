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
from pente.core.Core import Core

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
    # Maps colour names (which are parts of language keys) to colour codes (part of the ANSI escape to set the colour)
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
        "bright_black": '30;1',
        "bright_red": '31;1',
        "bright_green": '32;1',
        "bright_yellow": '33;1',
        "bright_blue": '34;1',
        "bright_magenta": '35;1',
        "bright_cyan": '36;1',
        "bright_white": '37;1',
    }

    def __init__(self):
        self.__language = Language(["en_UK"], partial(print, end=""))
        self.__core = Core(self.__language)
        self.__COMMANDS = {}
        for command_name, func_name in _COMMANDS.items():
            self.__COMMANDS[command_name] = getattr(self, func_name)

        # Maps colour aliases (user-facing, determined by language) to colour names (part of language keys)
        self.__COLOR_ALIASES = {}
        for color_name, color_code in Cli.__COLORS.items():
            self.__COLOR_ALIASES[self.__language.resolve_key(f"color.{color_name}")] = color_code

    def mainloop(self):
        self.__language.print_key("cli.help_prompt")
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
        """Display a list of commands"""
        last_func = None
        for name, func in self.__COMMANDS.items():
            # If a command is registered under multiple names, consider only the first
            if func == last_func:
                continue
            last_func = func
            print(f"{name} " + " ".join(f"<{param}>" for param in inspect.signature(func).parameters))
            self.__language.print_key(f"cli.help.{name}")

    @command
    def register(self, username: str):
        """Register an account with a given username; password entered separately"""
        self.__language.print_key("cli.login.password_prompt")
        # Flush the print buffer before getpass can disable echo
        print(end="", flush=True)
        password = getpass.getpass("")
        if accounts.register(username, password) is None:
            self.__language.print_key("cli.register.duplicate_username")
        else:
            self.__language.print_key("cli.register.ok")

    @command
    def login(self, username: str):
        """Login the given account (must be registered)"""
        if self.__core.can_login() == Core.LoginResponse.NO_SPACE:
            self.__language.print_key("cli.login.no_space")
            return

        self.__language.print_key("cli.login.password_prompt")
        print(end="", flush=True)
        password = getpass.getpass("")
        response = self.__core.login(username, password)
        if response is Core.LoginResponse.INCORRECT_DETAILS:
            self.__language.print_key("cli.login.incorrect_details")
        else:
            self.__language.print_key("cli.login.ok")

    @command
    def logout(self, account_index: str):
        """Logout the given account by account index"""
        try:
            account_index = int(account_index)
        except ValueError:
            self.__language.print_key("cli.logout.bad_format")
            return

        response = self.__core.logout(account_index)
        if not response:
            self.__language.print_key("cli.logout.not_logged_in")
        else:
            self.__language.print_key("cli.logout.ok")

    @command("listaccounts")
    def list_accounts(self):
        """List which accounts are currently logged in"""
        logged_in_accounts = self.__core.accounts
        if len(logged_in_accounts) == 0:
            self.__language.print_key("cli.list_accounts.none")
        if len(logged_in_accounts) == 1:
            self.__language.print_key("cli.list_accounts.one", account=logged_in_accounts[0])
        if len(logged_in_accounts) == 2:
            self.__language.print_key("cli.list_accounts.two", account1=logged_in_accounts[0],
                                      account2=logged_in_accounts[1])

    def __get_color(self, account_index: int):
        username = self.__core.resolve_account_index(account_index)
        if username is None:
            return '0'
        else:
            return accounts.get_color(username)

    @command("color")
    @command("colour")
    def set_color(self, account_index: str, color: str):
        """Set the colour to use to represent pieces belonging to a given account, by account index"""
        try:
            account_index = int(account_index)
        except ValueError:
            self.__language.print_key("cli.set_color.bad_format")
            return

        username = self.__core.resolve_account_index(account_index)
        if username is None:
            self.__language.print_key("cli.index_not_logged_in")
            return

        if color not in self.__COLOR_ALIASES:
            self.__language.print_key("cli.set_color.bad_color")
            return

        accounts.set_color(username, self.__COLOR_ALIASES[color])
        self.__language.print_key("cli.set_color.ok")

    @command("data")
    def load_data(self, *names: str) -> bool:
        """Load a set of datapacks; the next game launched will use those datapacks"""
        response = self.__core.load_data(names)
        if not response:
            self.__language.print_key("cli.load_data.error")
        return response

    @command("listdata")
    def list_datapacks(self):
        """List the currently loaded datapacks"""
        packs = self.__core.pack_names
        if len(packs) == 0:
            self.__language.print_key("cli.list_datapacks.none")
        else:
            self.__language.print_key("cli.list_datapacks.some", packs=" ".join(packs))

    @command("play")
    def launch_game(self, *names: str):
        """Launch a game with the currently loaded datapacks. If no datapacks are loaded, loads pente first. If
        datapacks are specified as arguments, loads those packs first."""
        # If packs are specified, load them
        if names:
            if not self.load_data(*names):
                # If packs can't be loaded, abort
                self.__language.print_key("cli.launch.no_data")
                return

        colors = self.__get_color(0), self.__get_color(1)
        player_output = CliPlayerOutput(self.__language, colors)
        response = self.__core.launch_game(player_output)
        if response is Core.LaunchGameResponse.ALREADY_PLAYING:
            self.__language.print_key("cli.launch.already_playing")
        elif response is Core.LaunchGameResponse.NO_DATA:
            # Load Pente, then reattempt
            if not self.load_data("pente"):
                self.__language.print_key("cli.launch.no_data")
                return
            self.__core.launch_game(player_output)

    def __confirm(self, key: str, **kwargs: str) -> bool:
        """
        Requests confirmation from the user for some action. The positive response is determined by language keys.
        :param key: A fragment of the language key used to find the question.
        :param \\**kwargs: Parameters for the language key.
        :returns: True if the user enters the positive response.
        """
        self.__language.print_key("cli.confirm." + key, **kwargs)
        return input().lower() == self.__language.resolve_key("cli.confirm.positive_response")

    @command
    def concede(self):
        """Concede the current game"""
        if not self.__confirm("concede"):
            return

        response = self.__core.ui_concede()
        if not response:
            self.__language.print_key("cli.concede.no_game")

    @command
    def move(self, *coords: str):
        """Make a move in the current game at the given coordinates"""
        try:
            coords = tuple(map(int, coords))
        except ValueError:
            self.__language.print_key("cli.move.bad_format")
            return

        response = self.__core.ui_move(coords)
        if response is Core.MoveResponse.NO_GAME:
            self.__language.print_key("cli.move.no_game")
        elif response is Core.MoveResponse.ILLEGAL:
            self.__language.print_key("cli.move.illegal")

    @command
    def save(self):
        """Save the current game into the saves folder. The file is named according to the date and time."""
        file_name = self.__core.save()
        if file_name is not None:
            self.__language.print_key("cli.save_game.ok", file_name=file_name)
        else:
            self.__language.print_key("cli.save_game.no_game")

    @command("load")
    def load_game(self, file_name: str):
        """Load a saved game from the save folder, by the given file name."""
        colors = self.__get_color(0), self.__get_color(1)
        response = self.__core.load_game(CliPlayerOutput(self.__language, colors), file_name)
        if response is Core.LaunchGameResponse.ALREADY_PLAYING:
            self.__language.print_key("cli.launch.already_playing")
        elif response is Core.LaunchGameResponse.NO_DATA:
            self.__language.print_key("cli.launch.no_data")

    @command("autosave")
    def toggle_autosave(self):
        """Toggle whether or not the game is automatically saved into saves/autosave.json before every move. On by
        default."""
        self.__core.should_autosave = not self.__core.should_autosave
        mode = self.__language.resolve_key("cli.toggle." + ("on" if self.__core.should_autosave else "off"))
        self.__language.print_key("cli.toggle_autosave", mode=mode)

    @command
    def undo(self):
        """Restore the last autosave, which is most likely the state of the game before the previous move"""
        response = self.__core.undo()
        if response is Core.UndoResponse.AUTOSAVING_OFF:
            self.__language.print_key("cli.undo.autosaving_off")
        elif response is Core.UndoResponse.NO_GAME:
            self.__language.print_key("cli.undo.no_game")
        elif response is Core.UndoResponse.NO_DATA:
            self.__language.print_key("cli.undo.no_data")

    @command
    def difficulty(self, difficulty: str):
        """Set the difficulty rating of the ai. 0 is the hardest difficulty; 30 is very easy"""
        try:
            difficulty = float(difficulty)
        except ValueError:
            self.__language.print_key("cli.difficulty.bad_format")
            return

        self.__core.difficulty = difficulty
        self.__language.print_key("cli.difficulty.ok")

    @command("aimove")
    def ai_suggestion(self):
        """Have the ai suggest a move. To play against the ai, use this command and then manually input the move on
        its turn."""
        response = self.__core.ai_suggestion()
        if response is None:
            self.__language.print_key("cli.ai_suggestion.invalid")
        else:
            self.__language.print_key("cli.ai_suggestion.ok", move=" ".join(map(str, response)))

    @command("trackstats")
    def toggle_track_stats(self):
        """Toggle whether statistics are tracked. If on, when a game ends, the winner and win reason are recorded. Off
        by default."""
        self.__core.should_track_stats = not self.__core.should_track_stats
        mode = self.__language.resolve_key("cli.toggle." + ("on" if self.__core.should_track_stats else "off"))
        self.__language.print_key("cli.toggle_track_stats", mode=mode)

    @command("showstats")
    def show_stats(self, account_index: str, win_reason: str):
        """Display the number of games a given account, by account index, has won in a given way. Default win reasons
        are gomoku.victory for five in a row, pente.captures, and .concede. .all to display all reasons."""
        try:
            account_index = int(account_index)
        except ValueError:
            self.__language.print_key("cli.show_stats.bad_format")
            return

        username = self.__core.resolve_account_index(account_index)
        if username is None:
            self.__language.print_key("cli.index_not_logged_in")
            return

        if win_reason == '.all':
            for win_reason, wins in stats.get_all_wins(username).items():
                self.__language.print_key("cli.show_stats.ok", reason=win_reason, wins=str(wins))
        else:
            wins = stats.get_wins(username, win_reason)
            self.__language.print_key("cli.show_stats.ok", reason=win_reason, wins=str(wins))

    @command("clearstats")
    def clear_stats(self, account_index: str):
        """Clear all statistics for a given account by account index"""
        try:
            account_index = int(account_index)
        except ValueError:
            self.__language.print_key("cli.clear_stats.bad_format")
            return

        if not self.__confirm("clear_stats"):
            return

        username = self.__core.resolve_account_index(account_index)
        stats.clear_wins(username)
        self.__language.print_key("cli.clear_stats.ok")

    @command
    def exit(self):
        """Exit the application. No saves are made or statistics tracked."""
        if self.__confirm("exit"):
            raise SystemExit
