from collections.abc import Sequence
from typing import Optional
import re
import string

from game.Board import Board, EMPTY

_pattern_validator = re.compile(r'''
    [#.0-9a-zA-Z-]*
    (?:
        \[ ([#.0-9a-zA-Z-]) ]  # Center
        [#.0-9a-zA-Z-]*
    )?
''', re.VERBOSE)


class Pattern:
    def __init__(self, s: str):
        match = re.fullmatch(_pattern_validator, s)
        if match is None:
            raise ValueError(f"Invalid pattern '{s}'")

        if match.group(1):
            self.__center = s.index("[")
        else:
            self.__center = None

        self.__string = s.replace("[", "").replace("]", "")

    def match_line(self, line: Board.Line) -> Optional[Sequence[tuple[int, ...]]]:
        """
        Attempt to match this pattern to a given line and center
        :param line: The line to match
        :returns: The positions at which the line matched, as indices into the board, or None if it didn't
        """
        if self.__center is not None:
            # Skip the start of line to force the centers to line up
            start = line.center - self.__center
            if self._full_match(line.tiles[start:start + len(self.__string)]):
                return self._get_match_locations(line, start)
            return None
        else:
            # Try matching from every position that would include the line center
            for start in range(max(0, line.center - len(self.__string) + 1),
                               min(line.center + 1, len(line.tiles) - len(self.__string) + 1)):
                match = self._full_match(line.tiles[start:start + len(self.__string)])
                if match:
                    return self._get_match_locations(line, start)
            return None

    def _full_match(self, tiles: Sequence[int]) -> bool:
        """
        Get whether this pattern matches a given line exactly, ignoring centers
        :param tiles: The line to match
        :returns: Whether or not this pattern matches the line exactly, ignoring centers
        """
        if len(self.__string) != len(tiles):
            return False

        variables = {}
        for char, tile in zip(self.__string, tiles):
            if char == "#" and tile == EMPTY:
                return False
            elif char == "-" and tile != EMPTY:
                return False
            elif char in string.ascii_letters:
                if tile == EMPTY:
                    return False
                inverse_char = char.lower() if char.isupper() else char.upper()
                if char in variables:
                    if tile != variables[char]:
                        return False
                elif inverse_char in variables:
                    if tile == variables[inverse_char]:
                        return False
                else:
                    variables[char] = tile

        return True

    def _get_match_locations(self, line: Board.Line, start: int) -> Sequence[tuple[int, ...]]:
        return line.tile_indices[start : start + len(self.__string)]
