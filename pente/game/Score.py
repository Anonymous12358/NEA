from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Score:
    name: str
    display_name: Optional[str] = None
    win_threshold: Optional[int] = None
