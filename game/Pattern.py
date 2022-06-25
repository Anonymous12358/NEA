from collections.abc import Sequence
from typing import Optional
import re
import numpy as np
import string

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

    def match_line(self, line_center: int, line: Sequence[int]) -> Optional[int]:
        """
        Attempt to match this pattern to a given line and center
        :param line_center: The position of the center within the line
        :param line: The line to match
        :return: The first position at which the pattern matches, or None if it doesn't
        """
        if self.__center is not None:
            # Skip the start of line to force the centers to line up
            start = line_center - self.__center
            if self._full_match(line[start:start + len(self.__string)]):
                return start
            return None
        else:
            # Try matching from every position that would include the line center
            for start in range(max(0, line_center - len(self.__string) + 1),
                               min(line_center + 1, len(self.__string) - len(line) - 1)):
                match = self._full_match(line[start:start + len(self.__string)])
                if match:
                    return start
            return None

    def _full_match(self, line: Sequence[int]) -> bool:
        """
        Get whether this pattern matches a given line exactly, ignoring centers
        :param line: The line to match
        :return: Whether or not this pattern matches the line exactly, ignoring centers
        """
        if len(self.__string) != len(line):
            return False

        variables = {}
        for char, tile in zip(self.__string, line):
            if char == "#" and tile == 0:
                return False
            elif char == "-" and tile != 0:
                return False
            elif char in string.digits and tile != int(char):
                return False
            elif char in string.ascii_letters:
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
