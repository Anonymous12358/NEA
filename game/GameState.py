from dataclasses import dataclass

from game.Board import Board


@dataclass
class GameState:
    board: Board
    scores: dict[str, list[int]]
    winner: int
    active_player: int
    num_players: int = 2
