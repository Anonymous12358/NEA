"""
Functions for loading saved games to produce gamestates
"""

import json

import jsonschema
import yaml

from pente.data import Language
from pente.game.Board import Board
from pente.game.GameState import GameState


class LoadGameStateError(RuntimeError):
    pass


def load_gamestate(language: Language, file_name: str) -> tuple[GameState, dict]:
    """
    :returns: The loaded gamestate, and a dictionary for direct access to the validated loaded data
    """
    #############################################################
    # GROUP B SKILL: WRITING AND READING FROM FILES             #
    # Read the file containing the serialised gamestate to load #
    #############################################################
    try:
        with open(f"saves/{file_name}.json", 'r') as file:
            dct = json.loads(file.read())
    except json.JSONDecodeError:
        language.print_key("error.load_game.invalid_json")
        raise
    except (FileNotFoundError, PermissionError):
        language.print_key("error.load_game.game_file_absent")
        raise

    schema = _load_schema(language)
    try:
        jsonschema.validate(dct, schema)
    except jsonschema.SchemaError:
        language.print_key("error.load_game.invalid_schema")
        raise
    except jsonschema.ValidationError:
        language.print_key("error.load_game.invalid_by_schema")
        raise

    # Further validation
    try:
        board = Board.from_list(dct["board"])
    except ValueError:
        language.print_key("error.load_game.invalid_board")
        raise LoadGameStateError("error.load_game.invalid_board")

    num_players = dct.get("num_players", 2)
    if num_players != 2:
        language.print_key("warning.load_game.invalid_num_players")
        num_players = 2

    scores = dct["scores"]
    if not all(len(score_list) == num_players for score_list in scores.values()):
        language.print_key("error.load_game.invalid_scores")
        raise LoadGameStateError("error.load_game.invalid_scores")

    memos = scores.keys()
    active_player = dct["active_player"]

    gamestate = GameState(board, memos, num_players)
    gamestate.scores = scores
    gamestate.active_player = active_player
    return gamestate, dct


def _load_schema(language: Language) -> dict:
    ##########################################################################
    # GROUP B SKILL: WRITING AND READING FROM FILES                          #
    # Read the file containing the schema for validating the saved gamestate #
    ##########################################################################
    try:
        with open("resources/save_schema.yml", 'r') as schema_file:
            return yaml.safe_load(schema_file)
    except yaml.scanner.ScannerError:
        language.print_key("error.load_game.invalid_schema")
        raise
    except (FileNotFoundError, PermissionError):
        language.print_key("error.file_absent.save_schema")
        raise
