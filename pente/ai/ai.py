import random

import numpy as np

from pente.game.Board import EMPTY, Board
from pente.game.GameState import GameState
from pente.game.rule.Pattern import Pattern

_SCORES = {
    # In the absence of other factors, play near the opponent
    Pattern("Aa"): 0.1,
    # Immediately captured
    Pattern("a[A]A-"): -3,
    Pattern("aA[A]-"): -3,
    # Vulnerable to capture
    Pattern("-AA-"): -1,
    # Threatening capture
    Pattern("[A]aa-"): 3,
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
    Pattern("[A]aaaa"): 50,
    Pattern("a[A]aaa"): 50,
    Pattern("aa[A]aa"): 50,
    # Pente
    Pattern("AAAAA"): 200,
}


def _score_play(board: Board, center: tuple[int, ...]):
    lines = board.get_lines(center)
    result = 0
    for pattern, score in _SCORES.items():
        for line in lines:
            if pattern.match_line(line):
                result += score
    return result


def best_move(gamestate: GameState, difficulty: float) -> tuple[int, ...]:
    board = gamestate.board.copy()

    best_play, best_score = (0,) * len(board.dimensions), float('-inf')
    for test_play in np.ndindex(board.dimensions):
        if board[test_play] != EMPTY:
            continue

        board[test_play] = gamestate.next_player
        test_score = _score_play(board, test_play)
        test_score += difficulty * random.random()
        if test_score > best_score:
            best_play = test_play
            best_score = test_score

        board[test_play] = EMPTY

    return best_play
