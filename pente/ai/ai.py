import random

import numpy as np

from pente.game.Board import EMPTY, Board
from pente.game.GameState import GameState
from pente.game.rule.Pattern import Pattern

# Distance weightings are cumulative, so stones within 3 tiles are counted 1+2 times
_DISTANCE_WEIGHTINGS = {1: 3, 3: 2, 5: 1}
_SCORES = {
    # In the absence of other factors, play near the opponent
    Pattern("Aa"): 0.1,
    # Immediately captured
    Pattern("a[A]A-"): -3,
    Pattern("aA[A]-"): -3,
    # Vulnerable to capture
    Pattern("-AA-"): -1,
    # Threatening capture
    Pattern("-[A]aa-"): 3,
    # Saving from capture
    Pattern("aAA[A]"): 2,
    # Capture
    Pattern("[A]aaA"): 4,
    # Stretch two and blocking opponent's stretch two
    Pattern("-A-A-"): 1,
    Pattern("[A]a-a-"): 1,
    Pattern("-a[A]a-"): 1,
    # Open tria (if a tria has an opponent's piece two tiles away, it can't be turned into an open tessera)
    Pattern("--AAA-"): 4,
    # Open trias must be blocked
    Pattern("[A]aaa-"): 20,
    # Stretch tria and blocking
    Pattern("-AA-A-"): 2,
    Pattern("-aa[A]a-"): 20,
    Pattern("[A]aa-a-"): 20,
    Pattern("-aa-a[A]"): 20,
    # Open tessera
    Pattern("-AAAA-"): 20,
    # Closed tessera still grants initiative (no center need be specified because if we're lowercase, we already lost)
    Pattern("aAAAA-"): 3,
    # Block win
    Pattern("[A]aaaaA"): 50,
    Pattern("a[A]aaa"): 50,
    Pattern("aa[A]aa"): 50,
    # Pente
    Pattern("AAAAA"): 200,
}


def weight_board(tiles: np.ndarray) -> np.ndarray:
    # Each empty tile has a weighting of at least 1, so any empty tile could be chosen
    weights = np.full(tiles.shape, 1)
    for coords in np.ndindex(tiles.shape):
        if tiles[coords] != EMPTY:
            weights[coords] = 0
            continue

        # Nearby stones
        for distance, distance_weighting in _DISTANCE_WEIGHTINGS.items():
            weights[coords] += np.count_nonzero(
                tiles[tuple(slice(max(0, ordinate - distance), ordinate + distance) for ordinate in coords)]
                != EMPTY
            ) * distance_weighting

    return weights


def random_move(gamestate: GameState) -> tuple[int, ...]:
    tiles = gamestate.board.get_tiles()
    weight_cumsum = np.cumsum(weight_board(tiles))
    # We don't want to be able to roll 0, but we do want to be able to roll max
    roll = (1 - random.random()) * weight_cumsum[-1]
    # Find the leftmost value in weight_cumsum that is less than or equal to roll
    index = np.searchsorted(weight_cumsum, roll, side='left')

    return np.unravel_index(index, tiles.shape)


def score_play(tiles: np.ndarray, center: tuple[int, ...]):
    lines = Board.get_lines_on(tiles, center)
    result = 0
    for pattern, score in _SCORES.items():
        for line in lines:
            if pattern.match_line(line):
                result += score
    return result


def best_move(gamestate: GameState) -> tuple[int, ...]:
    tiles = gamestate.board.get_tiles()

    best_play, best_score = (0,) * tiles.ndim, float('-inf')
    for test_play in np.ndindex(tiles.shape):
        if tiles[test_play] != EMPTY:
            continue

        tiles[test_play] = gamestate.next_player
        test_score = score_play(tiles, test_play)
        if test_score > best_score:
            best_play = test_play
            best_score = test_score

        tiles[test_play] = EMPTY

    return best_play
