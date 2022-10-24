from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Score:
    """A type of score, as used in defining rules; does not hold values of players' scores"""
    name: str
    display_name: Optional[str] = None
    win_threshold: Optional[int] = None
