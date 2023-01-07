from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Score:
    """A type of score, as used in defining rules. Values of players' scores are held in the gamestate."""
    name: str
    display_name: Optional[str] = None
    win_threshold: Optional[int] = None
