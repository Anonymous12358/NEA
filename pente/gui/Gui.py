import os
import sys
import tkinter as tk
from functools import partial
from tkinter import ttk

from pente.account import accounts, stats
from pente.core.Core import Core
from pente.core.PlayerOutput import PlayerOutput
from pente.data.Language import Language
from pente.game.Board import Board, EMPTY
from pente.game.Game import Game

if sys.platform == 'linux':
    _BOARD_FONT_SIZE = 17
elif sys.platform == 'darwin':
    _BOARD_FONT_SIZE = 20
else:
    _BOARD_FONT_SIZE = 14


# A:complex-oop
# Gui conforms to the interface of PlayerOutput so it can be used by the Core
class Gui(tk.Frame, PlayerOutput):
    def __init__(self):
        self.__language = Language(["en_UK"], partial(print, end=""))
        self.__core = Core(self.__language)
        self.__game_buttons: list[list[ttk.Button]] = [[] for _ in range(19)]
        self.__game_labels = set()

        super().__init__(tk.Tk())
        self.grid()
        self.winfo_toplevel().title(self.__language.resolve_key("gui.name"))
        # Used to highlight buttons by turning the text green
        style = ttk.Style(self)
        style.configure('highlight.TButton', foreground='#00D040')

        y = 0
        ttk.Button(self, text=self.__language.resolve_key("gui.button.help"), command=self.__help).grid(row=y, column=0)
        quit_button = ttk.Button(self, text=self.__language.resolve_key("gui.button.exit"))
        quit_button.grid(row=y, column=1)
        quit_button.bind('<Shift-Button-1>', lambda _: self.master.destroy())
        concede_button = ttk.Button(self, text=self.__language.resolve_key("gui.button.concede"))
        concede_button.grid(row=y, column=2)
        concede_button.bind('<Shift-Button-1>', lambda _: self.__core.ui_concede())

        y += 1
        self.__username_entry = ttk.Entry(self, width=9)
        self.__username_entry.grid(row=y, column=0)
        self.__password_entry = ttk.Entry(self, width=9, show="•")
        self.__password_entry.grid(row=y, column=1)
        ttk.Button(
            self, text=self.__language.resolve_key("gui.button.register"), command=self.__register
        ).grid(row=y, column=2)

        y += 1
        self.__account_buttons = tuple(
            ttk.Button(self, text=self.__language.resolve_key("gui.button.empty_account"))
            for _ in range(2)
        )
        self.__account_buttons[0].grid(row=y, column=0)
        self.__account_buttons[0].bind('<Shift-Button-1>', lambda _: self.__logout(0))
        self.__account_buttons[1].grid(row=y, column=1)
        self.__account_buttons[1].bind('<Shift-Button-1>', lambda _: self.__logout(1))
        ttk.Button(
            self, text=self.__language.resolve_key("gui.button.login"), command=self.__login
        ).grid(row=y, column=2)

        y += 1
        for i in range(2):
            ttk.Button(
                self, text=self.__language.resolve_key("gui.button.stats"), command=partial(self.__show_stats, i)
            ).grid(row=y, column=i)
        self.__toggle_track_stats_button = ttk.Button(
            self, text=self.__language.resolve_key("gui.button.toggle_stats"), command=self.__toggle_track_stats
        )
        self.__toggle_track_stats_button.grid(row=y, column=2)

        y += 1
        self.__difficulty_entry = ttk.Entry(self, width=9)
        self.__difficulty_entry.grid(row=y, column=0)
        ttk.Button(
            self, text=self.__language.resolve_key("gui.button.set_difficulty"), command=self.__set_difficulty
        ).grid(row=y, column=1)
        ttk.Button(
            self, text=self.__language.resolve_key("gui.button.ai_move"), command=self.__ai_suggestion
        ).grid(row=y, column=2)

        y += 1
        self.__filename_entry = ttk.Entry(self, width=9)
        self.__filename_entry.grid(row=y, column=0)
        ttk.Button(
            self, text=self.__language.resolve_key("gui.button.save"), command=self.__save_game
        ).grid(row=y, column=1)
        ttk.Button(
            self, text=self.__language.resolve_key("gui.button.load"), command=self.__load_game
        ).grid(row=y, column=2)

        y += 1
        available_packs = os.listdir("resources/datapack")
        for i, name in enumerate(("pro", "keryo", "pente")):
            if f"{name}.json" in available_packs:
                ttk.Button(self, text=name, command=partial(self.__load_data, name)).grid(row=y, column=i)

        y += 1
        self.__toggle_autosave_button = ttk.Button(
            self,
            text=self.__language.resolve_key("gui.button.autosave"),
            command=self.__toggle_autosave,
            style='highlight.TButton'
        )
        self.__toggle_autosave_button.grid(row=y, column=0)
        ttk.Button(
            self, text=self.__language.resolve_key("gui.button.undo"), command=self.__core.undo
        ).grid(row=y, column=1)
        ttk.Button(
            self,
            text=self.__language.resolve_key("gui.button.play"),
            command=partial(self.__core.launch_game, self)
        ).grid(row=y, column=2)

    def __help(self):
        self.__language.print_key("gui.help")

    def __load_data(self, name):
        if name == "pro":
            # Hardcode pro to launch pro pente, since the user can't specify multiple packs
            self.__core.load_data(("pro", "pente"))
        else:
            self.__core.load_data((name,))
        if not self.__core.in_game:
            self.__clear_game()

    def __register(self):
        accounts.register(self.__username_entry.get(), self.__password_entry.get())
        self.__username_entry.delete(0, 'end')
        self.__password_entry.delete(0, 'end')

    def __login(self):
        self.__core.login(self.__username_entry.get(), self.__password_entry.get())
        self.__update_account_buttons()
        self.__username_entry.delete(0, 'end')
        self.__password_entry.delete(0, 'end')

    def __logout(self, account_index: int):
        self.__core.logout(account_index)
        self.__update_account_buttons()

    def __show_stats(self, account_index: int):
        username = self.__core.resolve_account_index(account_index)
        if username is None:
            return

        self.__language.print_key("gui.show_stats.header")
        for win_reason, wins in stats.get_all_wins(username).items():
            self.__language.print_key("gui.show_stats.stat", reason=win_reason, wins=str(wins))

    def __toggle_track_stats(self):
        self.__core.should_track_stats = not self.__core.should_track_stats
        if self.__core.should_track_stats:
            self.__toggle_track_stats_button.config(style='highlight.TButton')
        else:
            self.__toggle_track_stats_button.config(style='TButton')

    def __set_difficulty(self):
        try:
            difficulty = float(self.__difficulty_entry.get())
        except ValueError:
            return

        self.__core.difficulty = difficulty

    def __ai_suggestion(self):
        coords = self.__core.ai_suggestion()
        if coords is None:
            return
        self.__game_buttons[coords[0]][coords[1]].config(style='highlight.TButton')

    def __save_game(self):
        self.__core.save(self.__filename_entry.get() or None)

    def __load_game(self):
        self.__core.load_game(self, self.__filename_entry.get())

    def __toggle_autosave(self):
        self.__core.should_autosave = not self.__core.should_autosave
        if self.__core.should_autosave:
            self.__toggle_autosave_button.config(style='highlight.TButton')
        else:
            self.__toggle_autosave_button.config(style='TButton')

    def __update_account_buttons(self):
        logged_in_accounts = self.__core.accounts
        for i, button in enumerate(self.__account_buttons):
            if len(logged_in_accounts) > i:
                button.config(text=logged_in_accounts[i])
            else:
                button.config(text=self.__language.resolve_key("gui.button.empty_account"))

    def __clear_game(self):
        for row in self.__game_buttons:
            for button in row:
                button.destroy()
        for label in self.__game_labels:
            label.destroy()
        self.__game_buttons = [[] for _ in range(19)]
        self.__game_labels.clear()

    def __draw_board(self, board: Board, buttons: bool):
        for (y, x), tile in board.enumerate():
            tile = "-" if tile == EMPTY else str(tile)

            if buttons:
                widget = ttk.Button(self, text=tile, command=partial(self.__core.ui_move, (y, x)), width=1)
                self.__game_buttons[y].append(widget)
            else:
                widget = ttk.Label(self, text=tile, font=('Courier New', 20))
                self.__game_labels.add(widget)
            widget.grid(row=y, column=3+x)

    def send_update(self, game: Game, your_index: int, is_hotseat: bool):
        self.__clear_game()
        self.__draw_board(game.gamestate.board, True)

        displayable_scores = game.get_displayable_scores()
        for y, (display_name, values) in enumerate(displayable_scores):
            label = ttk.Label(self, text=display_name)
            label.grid(row=8+y, column=0)
            self.__game_labels.add(label)
            for x, value in enumerate(values):
                label = ttk.Label(self, text=value)
                label.grid(row=8+y, column=1+x)
                self.__game_labels.add(label)

    def send_victory(self, game: Game, your_index: int, is_hotseat: bool):
        self.__clear_game()
        self.__draw_board(game.gamestate.board, False)
        label = ttk.Label(self, text=self.__language.resolve_key("gui.victory", player=str(game.winner)))
        label.grid(row=8, column=0)
        self.__game_labels.add(label)
