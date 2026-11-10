"""Time-limited (dynamic) obstacles."""

from __future__ import annotations

from dataclasses import dataclass

from swarmforge.core.exceptions import ValidationError
from swarmforge.core.types import Cell


@dataclass(frozen=True)
class DynamicObstacle:
    cell: Cell
    start: float
    end: float | None = None  # None -> permanent once inserted

    def __post_init__(self) -> None:
        if self.start < 0 or (self.end is not None and self.end <= self.start):
            raise ValidationError("dynamic obstacle requires 0 <= start < end")
